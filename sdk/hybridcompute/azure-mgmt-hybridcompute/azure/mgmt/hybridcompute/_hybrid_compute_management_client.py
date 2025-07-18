# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------

from copy import deepcopy
from typing import Any, Optional, TYPE_CHECKING, cast
from typing_extensions import Self

from azure.core.pipeline import policies
from azure.core.rest import HttpRequest, HttpResponse
from azure.core.settings import settings
from azure.mgmt.core import ARMPipelineClient
from azure.mgmt.core.policies import ARMAutoResourceProviderRegistrationPolicy
from azure.mgmt.core.tools import get_arm_endpoints

from . import models as _models
from ._configuration import HybridComputeManagementClientConfiguration
from ._utils.serialization import Deserializer, Serializer
from .operations import (
    ExtensionMetadataOperations,
    ExtensionMetadataV2Operations,
    ExtensionPublisherOperations,
    ExtensionTypeOperations,
    GatewaysOperations,
    HybridComputeManagementClientOperationsMixin,
    LicenseProfilesOperations,
    LicensesOperations,
    MachineExtensionsOperations,
    MachineRunCommandsOperations,
    MachinesOperations,
    NetworkProfileOperations,
    NetworkSecurityPerimeterConfigurationsOperations,
    Operations,
    PrivateEndpointConnectionsOperations,
    PrivateLinkResourcesOperations,
    PrivateLinkScopesOperations,
    SettingsOperations,
)

if TYPE_CHECKING:
    from azure.core.credentials import TokenCredential


class HybridComputeManagementClient(
    HybridComputeManagementClientOperationsMixin
):  # pylint: disable=too-many-instance-attributes
    """The Hybrid Compute Management Client.

    :ivar licenses: LicensesOperations operations
    :vartype licenses: azure.mgmt.hybridcompute.operations.LicensesOperations
    :ivar machines: MachinesOperations operations
    :vartype machines: azure.mgmt.hybridcompute.operations.MachinesOperations
    :ivar license_profiles: LicenseProfilesOperations operations
    :vartype license_profiles: azure.mgmt.hybridcompute.operations.LicenseProfilesOperations
    :ivar machine_extensions: MachineExtensionsOperations operations
    :vartype machine_extensions: azure.mgmt.hybridcompute.operations.MachineExtensionsOperations
    :ivar extension_metadata: ExtensionMetadataOperations operations
    :vartype extension_metadata: azure.mgmt.hybridcompute.operations.ExtensionMetadataOperations
    :ivar extension_metadata_v2: ExtensionMetadataV2Operations operations
    :vartype extension_metadata_v2:
     azure.mgmt.hybridcompute.operations.ExtensionMetadataV2Operations
    :ivar extension_type: ExtensionTypeOperations operations
    :vartype extension_type: azure.mgmt.hybridcompute.operations.ExtensionTypeOperations
    :ivar extension_publisher: ExtensionPublisherOperations operations
    :vartype extension_publisher: azure.mgmt.hybridcompute.operations.ExtensionPublisherOperations
    :ivar operations: Operations operations
    :vartype operations: azure.mgmt.hybridcompute.operations.Operations
    :ivar network_profile: NetworkProfileOperations operations
    :vartype network_profile: azure.mgmt.hybridcompute.operations.NetworkProfileOperations
    :ivar machine_run_commands: MachineRunCommandsOperations operations
    :vartype machine_run_commands: azure.mgmt.hybridcompute.operations.MachineRunCommandsOperations
    :ivar gateways: GatewaysOperations operations
    :vartype gateways: azure.mgmt.hybridcompute.operations.GatewaysOperations
    :ivar settings: SettingsOperations operations
    :vartype settings: azure.mgmt.hybridcompute.operations.SettingsOperations
    :ivar private_link_scopes: PrivateLinkScopesOperations operations
    :vartype private_link_scopes: azure.mgmt.hybridcompute.operations.PrivateLinkScopesOperations
    :ivar private_link_resources: PrivateLinkResourcesOperations operations
    :vartype private_link_resources:
     azure.mgmt.hybridcompute.operations.PrivateLinkResourcesOperations
    :ivar private_endpoint_connections: PrivateEndpointConnectionsOperations operations
    :vartype private_endpoint_connections:
     azure.mgmt.hybridcompute.operations.PrivateEndpointConnectionsOperations
    :ivar network_security_perimeter_configurations:
     NetworkSecurityPerimeterConfigurationsOperations operations
    :vartype network_security_perimeter_configurations:
     azure.mgmt.hybridcompute.operations.NetworkSecurityPerimeterConfigurationsOperations
    :param credential: Credential needed for the client to connect to Azure. Required.
    :type credential: ~azure.core.credentials.TokenCredential
    :param subscription_id: The ID of the target subscription. Required.
    :type subscription_id: str
    :param base_url: Service URL. Default value is None.
    :type base_url: str
    :keyword api_version: Api Version. Default value is "2025-02-19-preview". Note that overriding
     this default value may result in unsupported behavior.
    :paramtype api_version: str
    :keyword int polling_interval: Default waiting time between two polls for LRO operations if no
     Retry-After header is present.
    """

    def __init__(
        self, credential: "TokenCredential", subscription_id: str, base_url: Optional[str] = None, **kwargs: Any
    ) -> None:
        _cloud = kwargs.pop("cloud_setting", None) or settings.current.azure_cloud  # type: ignore
        _endpoints = get_arm_endpoints(_cloud)
        if not base_url:
            base_url = _endpoints["resource_manager"]
        credential_scopes = kwargs.pop("credential_scopes", _endpoints["credential_scopes"])
        self._config = HybridComputeManagementClientConfiguration(
            credential=credential, subscription_id=subscription_id, credential_scopes=credential_scopes, **kwargs
        )

        _policies = kwargs.pop("policies", None)
        if _policies is None:
            _policies = [
                policies.RequestIdPolicy(**kwargs),
                self._config.headers_policy,
                self._config.user_agent_policy,
                self._config.proxy_policy,
                policies.ContentDecodePolicy(**kwargs),
                ARMAutoResourceProviderRegistrationPolicy(),
                self._config.redirect_policy,
                self._config.retry_policy,
                self._config.authentication_policy,
                self._config.custom_hook_policy,
                self._config.logging_policy,
                policies.DistributedTracingPolicy(**kwargs),
                policies.SensitiveHeaderCleanupPolicy(**kwargs) if self._config.redirect_policy else None,
                self._config.http_logging_policy,
            ]
        self._client: ARMPipelineClient = ARMPipelineClient(base_url=cast(str, base_url), policies=_policies, **kwargs)

        client_models = {k: v for k, v in _models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)
        self._serialize.client_side_validation = False
        self.licenses = LicensesOperations(self._client, self._config, self._serialize, self._deserialize)
        self.machines = MachinesOperations(self._client, self._config, self._serialize, self._deserialize)
        self.license_profiles = LicenseProfilesOperations(
            self._client, self._config, self._serialize, self._deserialize
        )
        self.machine_extensions = MachineExtensionsOperations(
            self._client, self._config, self._serialize, self._deserialize
        )
        self.extension_metadata = ExtensionMetadataOperations(
            self._client, self._config, self._serialize, self._deserialize
        )
        self.extension_metadata_v2 = ExtensionMetadataV2Operations(
            self._client, self._config, self._serialize, self._deserialize
        )
        self.extension_type = ExtensionTypeOperations(self._client, self._config, self._serialize, self._deserialize)
        self.extension_publisher = ExtensionPublisherOperations(
            self._client, self._config, self._serialize, self._deserialize
        )
        self.operations = Operations(self._client, self._config, self._serialize, self._deserialize)
        self.network_profile = NetworkProfileOperations(self._client, self._config, self._serialize, self._deserialize)
        self.machine_run_commands = MachineRunCommandsOperations(
            self._client, self._config, self._serialize, self._deserialize
        )
        self.gateways = GatewaysOperations(self._client, self._config, self._serialize, self._deserialize)
        self.settings = SettingsOperations(self._client, self._config, self._serialize, self._deserialize)
        self.private_link_scopes = PrivateLinkScopesOperations(
            self._client, self._config, self._serialize, self._deserialize
        )
        self.private_link_resources = PrivateLinkResourcesOperations(
            self._client, self._config, self._serialize, self._deserialize
        )
        self.private_endpoint_connections = PrivateEndpointConnectionsOperations(
            self._client, self._config, self._serialize, self._deserialize
        )
        self.network_security_perimeter_configurations = NetworkSecurityPerimeterConfigurationsOperations(
            self._client, self._config, self._serialize, self._deserialize
        )

    def _send_request(self, request: HttpRequest, *, stream: bool = False, **kwargs: Any) -> HttpResponse:
        """Runs the network request through the client's chained policies.

        >>> from azure.core.rest import HttpRequest
        >>> request = HttpRequest("GET", "https://www.example.org/")
        <HttpRequest [GET], url: 'https://www.example.org/'>
        >>> response = client._send_request(request)
        <HttpResponse: 200 OK>

        For more information on this code flow, see https://aka.ms/azsdk/dpcodegen/python/send_request

        :param request: The network request you want to make. Required.
        :type request: ~azure.core.rest.HttpRequest
        :keyword bool stream: Whether the response payload will be streamed. Defaults to False.
        :return: The response of your network call. Does not do error handling on your response.
        :rtype: ~azure.core.rest.HttpResponse
        """

        request_copy = deepcopy(request)
        request_copy.url = self._client.format_url(request_copy.url)
        return self._client.send_request(request_copy, stream=stream, **kwargs)  # type: ignore

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        self._client.__enter__()
        return self

    def __exit__(self, *exc_details: Any) -> None:
        self._client.__exit__(*exc_details)
