import logging

from kubernetes import config, client
from openshift.dynamic import DynamicClient
from typing import cast
from typing_extensions import Protocol, override

from exc import ProviderError

LOG = logging.getLogger(__name__)


class Provider(Protocol):
    def group_members(self, group_name: str) -> list[str] | None: ...


class KubernetesProvider(Provider):
    def __init__(self):
        """Allocate a Kubernetes dynamic client and Group API client"""

        super().__init__()

        try:
            config.load_config()
        except config.ConfigException as err:
            LOG.warning("unable to configure Kubernetes client: %s", err)
            raise ProviderError("unable to configure Kubernetes client")

        k8s_client = client.ApiClient()
        dyn_client = DynamicClient(k8s_client)

        self._client = dyn_client
        self._group_resource = dyn_client.resources.get(
            api_version="user.openshift.io/v1", kind="Group"
        )

    def group_members(self, group_name):
        group_obj = self._group_resource.get(name=group_name)
        return group_obj.users
