import logging
import pydantic

from typing import Callable, Any, cast
from flask import Flask, Response, request, jsonify, current_app

from models import (
    Base,
    AdmissionReview,
    AdmissionResponse,
    AdmissionReviewStatus,
    PatchOp,
    PatchType,
    Patch,
    PatchAction,
    Pod,
)

from providers import Provider, KubernetesProvider
from exc import ApplicationError

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DEFAULTS:
    LABEL_NAME = "nerc.mghpcc.org/class"
    PROVIDER = KubernetesProvider


def jsonresponse() -> Callable[..., Callable[..., Response]]:
    """Transforms the response from a view function into a JSON object."""

    def _outer(func: Callable[..., Base]) -> Callable[..., Response]:
        def _inner(*args: list[Any], **kwargs: dict[str, Any]) -> Response:
            res = func(*args, **kwargs)
            return jsonify(res.model_dump(exclude_none=True))

        return _inner

    return _outer


def assign_class_label(provider: Provider, pod: Pod, groups: list[str]) -> str | None:
    pod_user = pod.metadata.labels.get("opendatahub.io/user")

    # If there is no user, we have nothing to do.
    if pod_user is None:
        return

    # Iterate through classes
    try:
        for group in groups:
            # Get users in group (class)
            users = provider.group_members(group)

            # Check if group has no users
            if not users:
                LOG.warning(f"Group {group} has no users.")
                continue

            # Compare users in the groups (classes) with the pod user
            if pod_user in users:
                LOG.info(f"Assigning class label: {group} to user {pod_user}")
                return group
    except Exception as err:
        LOG.error("failed to process groups: %s", err)
        raise ApplicationError("failed to process groups")

    return None


def json_patch_escape(val: str) -> str:
    return val.replace("~", "~0").replace("/", "~1")


@jsonresponse()
def mutate_pod() -> AdmissionReview:
    body = AdmissionReview(**request.get_json())
    pod = Pod(**body.request.object)

    # Grab class that the pod user belongs to
    class_label = assign_class_label(
        current_app.provider, pod, current_app.config["GROUPS"]
    )

    # If user not in any class, return without modifications
    if not class_label:
        return AdmissionReview(
            response=AdmissionResponse(
                allowed=True,
                uid=body.request.uid,
                status=AdmissionReviewStatus(message="No class label assigned"),
            )
        )

    # Generate JSON Patch to add class label
    label_name: str = cast(str, current_app.config["LABEL_NAME"])
    patch = Patch(
        [
            PatchAction(
                op=PatchOp.ADD,
                path=f"/metadata/labels/{json_patch_escape(label_name)}",
                value=class_label,
            )
        ]
    )

    # Return webhook response that includes the patch to add class label
    return AdmissionReview(
        response=AdmissionResponse(
            uid=body.request.uid,
            allowed=True,
            patchType=PatchType.JSONPATCH,
            patch=patch,
        )
    )


def handle_validationerror(
    err: pydantic.ValidationError,
) -> tuple[str, int, dict[str, str]]:
    return str(err), 400, {"content-type": "text/plain"}


def handle_applicationerror(err: ApplicationError) -> tuple[str, int, dict[str, str]]:
    return str(err), 500, {"content-type": "text/plain"}


def health() -> tuple[str, int, dict[str, str]]:
    return "OK", 200, {"content-type": "text/plain"}


def create_app(**config: dict[str, Any]) -> Flask:
    """Use an application factory [1] to create the Flask app.

    This makes it much easier to write tests for the application, since we can
    set up the test environment before instantiating the app. This is difficult
    to do if the app is created at `import` time.

    [1]: https://flask.palletsprojects.com/en/3.0.x/patterns/appfactories/
    """

    app = Flask(__name__)
    app.config.from_object(DEFAULTS)
    app.config.from_prefixed_env("RHOAI")
    if config:
        app.config.update(config)

    if not app.config.get("GROUPS"):
        LOG.error("Missing groups configuration")
        exit(1)

    app.config["GROUPS"] = app.config["GROUPS"].split(",")
    app.provider = app.config["PROVIDER"]()

    app.errorhandler(pydantic.ValidationError)(handle_validationerror)
    app.errorhandler(ApplicationError)(handle_applicationerror)
    app.add_url_rule("/healthz", view_func=health)
    app.add_url_rule("/mutate", view_func=mutate_pod, methods=["POST"])

    return app
