# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------
import pytest
from azure.mgmt.azurestackhci import AzureStackHCIClient

from devtools_testutils import AzureMgmtRecordedTestCase, RandomNameResourceGroupPreparer, recorded_by_proxy

AZURE_LOCATION = "eastus"


@pytest.mark.skip("you may need to update the auto-generated test case before run it")
class TestAzureStackHCIUpdateRunsOperations(AzureMgmtRecordedTestCase):
    def setup_method(self, method):
        self.client = self.create_mgmt_client(AzureStackHCIClient)

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy
    def test_list(self, resource_group):
        response = self.client.update_runs.list(
            resource_group_name=resource_group.name,
            cluster_name="str",
            update_name="str",
            api_version="2024-04-01",
        )
        result = [r for r in response]
        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy
    def test_begin_delete(self, resource_group):
        response = self.client.update_runs.begin_delete(
            resource_group_name=resource_group.name,
            cluster_name="str",
            update_name="str",
            update_run_name="str",
            api_version="2024-04-01",
        ).result()  # call '.result()' to poll until service return final result

        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy
    def test_put(self, resource_group):
        response = self.client.update_runs.put(
            resource_group_name=resource_group.name,
            cluster_name="str",
            update_name="str",
            update_run_name="str",
            update_runs_properties={
                "description": "str",
                "duration": "str",
                "endTimeUtc": "2020-02-20 00:00:00",
                "errorMessage": "str",
                "expectedExecutionTime": "str",
                "id": "str",
                "lastUpdatedTime": "2020-02-20 00:00:00",
                "lastUpdatedTimeUtc": "2020-02-20 00:00:00",
                "location": "str",
                "name": "str",
                "provisioningState": "str",
                "startTimeUtc": "2020-02-20 00:00:00",
                "state": "str",
                "status": "str",
                "steps": [
                    {
                        "description": "str",
                        "endTimeUtc": "2020-02-20 00:00:00",
                        "errorMessage": "str",
                        "expectedExecutionTime": "str",
                        "lastUpdatedTimeUtc": "2020-02-20 00:00:00",
                        "name": "str",
                        "startTimeUtc": "2020-02-20 00:00:00",
                        "status": "str",
                        "steps": [...],
                    }
                ],
                "systemData": {
                    "createdAt": "2020-02-20 00:00:00",
                    "createdBy": "str",
                    "createdByType": "str",
                    "lastModifiedAt": "2020-02-20 00:00:00",
                    "lastModifiedBy": "str",
                    "lastModifiedByType": "str",
                },
                "timeStarted": "2020-02-20 00:00:00",
                "type": "str",
            },
            api_version="2024-04-01",
        )

        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy
    def test_get(self, resource_group):
        response = self.client.update_runs.get(
            resource_group_name=resource_group.name,
            cluster_name="str",
            update_name="str",
            update_run_name="str",
            api_version="2024-04-01",
        )

        # please add some check logic here by yourself
        # ...
