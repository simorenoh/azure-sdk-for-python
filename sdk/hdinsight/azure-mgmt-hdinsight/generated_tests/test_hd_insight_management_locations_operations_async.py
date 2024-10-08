# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------
import pytest
from azure.mgmt.hdinsight.aio import HDInsightManagementClient

from devtools_testutils import AzureMgmtRecordedTestCase, RandomNameResourceGroupPreparer
from devtools_testutils.aio import recorded_by_proxy_async

AZURE_LOCATION = "eastus"


@pytest.mark.skip("you may need to update the auto-generated test case before run it")
class TestHDInsightManagementLocationsOperationsAsync(AzureMgmtRecordedTestCase):
    def setup_method(self, method):
        self.client = self.create_mgmt_client(HDInsightManagementClient, is_async=True)

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy_async
    async def test_get_capabilities(self, resource_group):
        response = await self.client.locations.get_capabilities(
            location="str",
            api_version="2024-08-01-preview",
        )

        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy_async
    async def test_list_usages(self, resource_group):
        response = await self.client.locations.list_usages(
            location="str",
            api_version="2024-08-01-preview",
        )

        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy_async
    async def test_list_billing_specs(self, resource_group):
        response = await self.client.locations.list_billing_specs(
            location="str",
            api_version="2024-08-01-preview",
        )

        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy_async
    async def test_get_azure_async_operation_status(self, resource_group):
        response = await self.client.locations.get_azure_async_operation_status(
            location="str",
            operation_id="str",
            api_version="2024-08-01-preview",
        )

        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy_async
    async def test_check_name_availability(self, resource_group):
        response = await self.client.locations.check_name_availability(
            location="str",
            parameters={"name": "str", "type": "str"},
            api_version="2024-08-01-preview",
        )

        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy_async
    async def test_validate_cluster_create_request(self, resource_group):
        response = await self.client.locations.validate_cluster_create_request(
            location="str",
            parameters={
                "fetchAaddsResource": bool,
                "identity": {
                    "principalId": "str",
                    "tenantId": "str",
                    "type": "str",
                    "userAssignedIdentities": {"str": {"clientId": "str", "principalId": "str", "tenantId": "str"}},
                },
                "location": "str",
                "name": "str",
                "properties": {
                    "clusterDefinition": {
                        "blueprint": "str",
                        "componentVersion": {"str": "str"},
                        "configurations": {},
                        "kind": "str",
                    },
                    "clusterVersion": "str",
                    "computeIsolationProperties": {"enableComputeIsolation": False, "hostSku": "str"},
                    "computeProfile": {
                        "roles": [
                            {
                                "VMGroupName": "str",
                                "autoscale": {
                                    "capacity": {"maxInstanceCount": 0, "minInstanceCount": 0},
                                    "recurrence": {
                                        "schedule": [
                                            {
                                                "days": ["str"],
                                                "timeAndCapacity": {
                                                    "maxInstanceCount": 0,
                                                    "minInstanceCount": 0,
                                                    "time": "str",
                                                },
                                            }
                                        ],
                                        "timeZone": "str",
                                    },
                                },
                                "dataDisksGroups": [{"diskSizeGB": 0, "disksPerNode": 0, "storageAccountType": "str"}],
                                "encryptDataDisks": False,
                                "hardwareProfile": {"vmSize": "str"},
                                "minInstanceCount": 0,
                                "name": "str",
                                "osProfile": {
                                    "linuxOperatingSystemProfile": {
                                        "password": "str",
                                        "sshProfile": {"publicKeys": [{"certificateData": "str"}]},
                                        "username": "str",
                                    }
                                },
                                "scriptActions": [{"name": "str", "parameters": "str", "uri": "str"}],
                                "targetInstanceCount": 0,
                                "virtualNetworkProfile": {"id": "str", "subnet": "str"},
                            }
                        ]
                    },
                    "diskEncryptionProperties": {
                        "encryptionAlgorithm": "str",
                        "encryptionAtHost": False,
                        "keyName": "str",
                        "keyVersion": "str",
                        "msiResourceId": "str",
                        "vaultUri": "str",
                    },
                    "encryptionInTransitProperties": {"isEncryptionInTransitEnabled": False},
                    "kafkaRestProperties": {
                        "clientGroupInfo": {"groupId": "str", "groupName": "str"},
                        "configurationOverride": {"str": "str"},
                    },
                    "minSupportedTlsVersion": "str",
                    "networkProperties": {
                        "outboundDependenciesManagedType": "str",
                        "privateLink": "str",
                        "publicIpTag": {"ipTagType": "str", "tag": "str"},
                        "resourceProviderConnection": "str",
                    },
                    "osType": "str",
                    "privateLinkConfigurations": [
                        {
                            "groupId": "str",
                            "ipConfigurations": [
                                {
                                    "name": "str",
                                    "id": "str",
                                    "primary": bool,
                                    "privateIPAddress": "str",
                                    "privateIPAllocationMethod": "str",
                                    "provisioningState": "str",
                                    "subnet": {"id": "str"},
                                    "type": "str",
                                }
                            ],
                            "name": "str",
                            "id": "str",
                            "provisioningState": "str",
                            "type": "str",
                        }
                    ],
                    "securityProfile": {
                        "aaddsResourceId": "str",
                        "clusterUsersGroupDNs": ["str"],
                        "directoryType": "str",
                        "domain": "str",
                        "domainUserPassword": "str",
                        "domainUsername": "str",
                        "ldapsUrls": ["str"],
                        "msiResourceId": "str",
                        "organizationalUnitDN": "str",
                    },
                    "storageProfile": {
                        "storageaccounts": [
                            {
                                "container": "str",
                                "enableSecureChannel": bool,
                                "fileSystem": "str",
                                "fileshare": "str",
                                "isDefault": bool,
                                "key": "str",
                                "msiResourceId": "str",
                                "name": "str",
                                "resourceId": "str",
                                "saskey": "str",
                            }
                        ]
                    },
                    "tier": "str",
                },
                "tags": {"str": "str"},
                "tenantId": "str",
                "type": "str",
                "zones": ["str"],
            },
            api_version="2024-08-01-preview",
        )

        # please add some check logic here by yourself
        # ...
