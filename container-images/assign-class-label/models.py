import base64
from typing import Any, Literal, Self
from pydantic import (
    BaseModel,
    RootModel,
    model_validator,
    field_validator,
)
from enum import StrEnum


class Base(BaseModel):
    pass


class ApiVersion(StrEnum):
    V1 = "admission.k8s.io/v1"


class Operation(StrEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CONNECT = "CONNECT"


class PatchType(StrEnum):
    JSONPATCH = "JSONPatch"


class PatchOp(StrEnum):
    REPLACE = "replace"
    ADD = "add"
    REMOVE = "remove"


class PatchAction(Base):
    op: PatchOp
    path: str
    value: Any


# https://jsonpatch.com/
Patch = RootModel[list[PatchAction]]


# https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.30/#status-v1-meta
class AdmissionReviewStatus(Base):
    message: str


# https://kubernetes.io/docs/reference/config-api/apiserver-admission.v1/#admission-k8s-io-v1-AdmissionResponse
class AdmissionResponse(Base):
    allowed: bool
    status: AdmissionReviewStatus | None = None
    uid: str
    patchType: PatchType | None = None
    patch: str | Patch | None = None

    @field_validator("patch", mode="before")
    @classmethod
    def validate_patch(cls, val: Patch | str | bytes) -> bytes:
        if isinstance(val, (str, bytes)):
            # Make sure the base64 string contains valid data.
            val = Patch.model_validate_json(base64.b64decode(val))
        return base64.b64encode(val.model_dump_json().encode())

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if self.patch and not self.patchType:
            raise ValueError("missing patchType field")
        if self.patchType and not self.patch:
            raise ValueError(f"patchType is {self.patchType} but there is no patch")

        return self


# https://kubernetes.io/docs/reference/config-api/apiserver-admission.v1/#admission-k8s-io-v1-AdmissionRequest
class AdmissionRequest(Base):
    uid: str
    name: str | None = None
    operation: Operation = Operation.CREATE
    object: dict[str, Any] | None = None


# https://kubernetes.io/docs/reference/config-api/apiserver-admission.v1/#admission-k8s-io-v1-AdmissionReview
class AdmissionReview(Base):
    apiVersion: Literal[ApiVersion.V1] = ApiVersion.V1
    kind: Literal["AdmissionReview"] = "AdmissionReview"
    request: AdmissionRequest | None = None
    response: AdmissionResponse | None = None

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if not (self.request or self.response):
            raise ValueError("must contain a request or a response")

        return self


class Metadata(Base):
    labels: dict[str, str] = {}


class Pod(Base):
    metadata: Metadata
