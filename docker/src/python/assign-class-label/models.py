import base64
from typing import Any, Literal
from pydantic import (
    BaseModel,
    RootModel,
    model_validator,
    field_validator,
)
from enum import StrEnum


class ApiVersion(StrEnum):
    V1 = "admission.k8s.io/v1"


class Operation(StrEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CONNECT = "CONNECT"


class PatchType(StrEnum):
    JSONPatch = "JSONPatch"


class PatchOp(StrEnum):
    REPLACE = "replace"
    ADD = "add"
    REMOVE = "remove"


class PatchAction(BaseModel):
    op: PatchOp
    path: str
    value: Any


# https://jsonpatch.com/
Patch = RootModel[list[PatchAction]]


# https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.30/#status-v1-meta
class AdmissionReviewStatus(BaseModel):
    message: str


# https://kubernetes.io/docs/reference/config-api/apiserver-admission.v1/#admission-k8s-io-v1-AdmissionResponse
class AdmissionResponse(BaseModel):
    allowed: bool
    status: AdmissionReviewStatus | None = None
    uid: str
    patchType: PatchType | None = None
    patch: str | None = None

    @field_validator("patch", mode="before")
    @classmethod
    def validate_patch(cls, val):
        if isinstance(val, Patch):
            val = base64.b64encode(val.model_dump_json().encode())
        elif isinstance(val, (str, bytes)):
            # Make sure the base64 string contains valid data.
            Patch.model_validate_json(base64.b64decode(val))
        return val

    @model_validator(mode="after")
    def validate_model(self):
        if self.patch and not self.patchType:
            raise ValueError("missing patchType field")
        if self.patchType and not self.patch:
            raise ValueError(f"patchType is {self.patchType} but there is no patch")

        return self


# https://kubernetes.io/docs/reference/config-api/apiserver-admission.v1/#admission-k8s-io-v1-AdmissionRequest
class AdmissionRequest(BaseModel):
    uid: str
    name: str | None = None
    operation: Operation = Operation.CREATE
    object: dict[str, Any] | None = None


# https://kubernetes.io/docs/reference/config-api/apiserver-admission.v1/#admission-k8s-io-v1-AdmissionReview
class AdmissionReview(BaseModel):
    apiVersion: Literal[ApiVersion.V1] = ApiVersion.V1
    kind: Literal["AdmissionReview"] = "AdmissionReview"
    request: AdmissionRequest | None = None
    response: AdmissionResponse | None = None

    @model_validator(mode="after")
    def validate_model(self):
        if not (self.request or self.response):
            raise ValueError("must contain a request or a response")

        return self


class Metadata(BaseModel):
    labels: dict[str, str] = {}


class Pod(BaseModel):
    metadata: Metadata
