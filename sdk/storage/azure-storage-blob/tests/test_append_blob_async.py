# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import aiohttp
import tempfile
import uuid
from datetime import datetime, timedelta
from os import path, remove

import pytest
from azure.core import MatchConditions
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError, ResourceModifiedError
from azure.mgmt.storage.aio import StorageManagementClient
from azure.storage.blob import BlobSasPermissions, generate_blob_sas, BlobImmutabilityPolicyMode, ImmutabilityPolicy
from azure.storage.blob._shared.policies import StorageContentValidation
from azure.storage.blob import BlobType
from azure.storage.blob.aio import BlobServiceClient, BlobClient

from devtools_testutils.aio import recorded_by_proxy_async
from devtools_testutils.storage.aio import AsyncStorageRecordedTestCase
from settings.testcase import BlobPreparer
from test_helpers_async import (
    NonSeekableStream,
    ProgressTracker,
    _build_base_file_share_headers,
    _create_file_share_oauth
)

# ------------------------------------------------------------------------------
TEST_BLOB_PREFIX = 'blob'
SMALL_BLOB_SIZE = 1024
LARGE_BLOB_SIZE = 64 * 1024
# ------------------------------------------------------------------------------


class TestStorageAppendBlobAsync(AsyncStorageRecordedTestCase):
    # --Helpers-----------------------------------------------------------------
    async def _setup(self, bsc):
        self.config = bsc._config
        self.container_name = self.get_resource_name('utcontainer')
        self.source_container_name = self.get_resource_name('utcontainersource')
        if self.is_live:
            try:
                await bsc.create_container(self.container_name)
                await bsc.create_container(self.source_container_name)
            except:
                pass

    def _get_blob_reference(self):
        return self.get_resource_name(TEST_BLOB_PREFIX)

    async def _get_bearer_token_string(self, resource: str = "https://storage.azure.com/.default") -> str:
        access_token = await self.get_credential(BlobServiceClient, is_async=True).get_token(resource)
        return "Bearer " + access_token.token

    async def _create_blob(self, bsc, tags=None):
        blob_name = self._get_blob_reference()
        blob = bsc.get_blob_client(
            self.container_name,
            blob_name)
        await blob.create_append_blob(tags=tags)
        return blob

    async def _create_source_blob(self, data, bsc):
        blob_client = bsc.get_blob_client(self.source_container_name, self.get_resource_name(TEST_BLOB_PREFIX))
        await blob_client.create_append_blob()
        await blob_client.append_block(data)
        return blob_client

    async def assertBlobEqual(self, blob, expected_data):
        stream = await blob.download_blob()
        actual_data = await stream.readall()
        assert actual_data == expected_data
    # --------------------------------------------------------------------------

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_with_oauth(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        destination_blob_client = await self._create_blob(bsc)
        access_token = await self.get_credential(BlobServiceClient, is_async=True).get_token("https://storage.azure.com/.default")
        token = "Bearer {}".format(access_token.token)

        # Assert this operation fails without a credential
        with pytest.raises(HttpResponseError):
            await destination_blob_client.append_block_from_url(source_blob_client.url)
        # Assert it passes after passing an oauth credential
        await destination_blob_client.append_block_from_url(source_blob_client.url, source_authorization=token)
        destination_blob = await destination_blob_client.download_blob()
        destination_blob_data = await destination_blob.readall()
        assert source_blob_data == destination_blob_data

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_create_blob(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob_name = self._get_blob_reference()

        # Act
        blob = bsc.get_blob_client(self.container_name, blob_name)
        create_resp = await blob.create_append_blob()

        # Assert
        blob_properties = await blob.get_blob_properties()
        assert blob_properties is not None
        assert blob_properties.etag == create_resp.get('etag')
        assert blob_properties.last_modified == create_resp.get('last_modified')

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_get_blob_properties_using_vid(self, **kwargs):
        versioned_storage_account_name = kwargs.pop("versioned_storage_account_name")
        versioned_storage_account_key = kwargs.pop("versioned_storage_account_key")

        bsc = BlobServiceClient(self.account_url(versioned_storage_account_name, "blob"), versioned_storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob_name = self._get_blob_reference()

        # Act
        blob = bsc.get_blob_client(self.container_name, blob_name)
        create_resp = await blob.create_append_blob()
        # create operation will return a version id
        assert create_resp['version_id'] is not None

        # Assert
        blob_properties = await blob.get_blob_properties(version_id=create_resp['version_id'])
        assert blob_properties is not None
        assert blob_properties.etag == create_resp.get('etag')
        assert blob_properties.last_modified == create_resp.get('last_modified')

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_create_blob_with_lease_id(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)

        # Act
        lease = await blob.acquire_lease(lease_id='00000000-1111-2222-3333-444444444444')
        create_resp = await blob.create_append_blob(lease=lease)

        # Assert
        blob_properties = await blob.get_blob_properties()
        assert blob_properties is not None
        assert blob_properties.etag == create_resp.get('etag')
        assert blob_properties.last_modified == create_resp.get('last_modified')

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_create_blob_with_metadata(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        metadata = {'hello': 'world', 'number': '42'}
        blob_name = self._get_blob_reference()
        blob = bsc.get_blob_client(self.container_name, blob_name)

        # Act
        await blob.create_append_blob(metadata=metadata)

        # Assert
        md = await blob.get_blob_properties()
        assert md.metadata == metadata

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)

        # Act
        for i in range(5):
            resp = await blob.append_block(u'block {0}'.format(i).encode('utf-8'))
            assert int(resp['blob_append_offset']) == 7 * i
            assert resp['blob_committed_block_count'] == i + 1
            assert resp['etag'] is not None
            assert resp['last_modified'] is not None

        # Assert
        await self.assertBlobEqual(blob, b'block 0block 1block 2block 3block 4')

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_high_throughput(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=100 * 1024 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(5 * 1024)

        # Act
        for i in range(2):
            await blob.append_block(data=data)

        # Assert
        await self.assertBlobEqual(blob, data * 2)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_unicode(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)

        # Act
        resp = await blob.append_block(u'啊齄丂狛狜', encoding='utf-16')
        assert int(resp['blob_append_offset']) == 0
        assert resp['blob_committed_block_count'] == 1
        assert resp['etag'] is not None
        assert resp['last_modified'] is not None

        # Assert

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_with_if_tags(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        tags = {"tag1 name": "my tag", "tag2": "secondtag", "tag3": "thirdtag"}
        blob = await self._create_blob(bsc, tags=tags)
        with pytest.raises(ResourceModifiedError):
            await blob.append_block(u'啊齄丂狛狜', encoding='utf-16', if_tags_match_condition="\"tag1\"='first tag'")
        resp = await blob.append_block(u'啊齄丂狛狜', encoding='utf-16', if_tags_match_condition="\"tag1 name\"='my tag' AND \"tag2\"='secondtag'")

        assert int(resp['blob_append_offset']) == 0
        assert resp['blob_committed_block_count'] == 1
        assert resp['etag'] is not None
        assert resp['last_modified'] is not None

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_with_md5(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)

        # Act
        resp = await blob.append_block(b'block', validate_content=True)
        assert int(resp['blob_append_offset']) == 0
        assert resp['blob_committed_block_count'] == 1
        assert resp['etag'] is not None
        assert resp['last_modified'] is not None

        # Assert

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_client = await self._create_blob(bsc)

        # Act: make append block from url calls
        split = 4 * 1024
        resp = await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                   source_offset=0, source_length=split)
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        tags = {"tag1 name": "my tag", "tag2": "secondtag", "tag3": "thirdtag"}
        await destination_blob_client.set_blob_tags(tags=tags)
        with pytest.raises(ResourceModifiedError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_offset=split,
                                                                source_length=LARGE_BLOB_SIZE - split,
                                                                if_tags_match_condition="\"tag1\"='first tag'")
        resp = await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                   source_offset=split,
                                                                   source_length=LARGE_BLOB_SIZE - split,
                                                                   if_tags_match_condition="\"tag1 name\"='my tag' AND \"tag2\"='secondtag'")

        assert resp.get('blob_append_offset') == str(4 * 1024)
        assert resp.get('blob_committed_block_count') == 2
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        blob = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert blob.get('etag') == resp.get('etag')
        assert blob.get('last_modified') == resp.get('last_modified')
        assert blob.get('size') == LARGE_BLOB_SIZE

        # Missing start range shouldn't pass the validation
        with pytest.raises(ValueError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_length=LARGE_BLOB_SIZE)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_and_validate_content_md5(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        src_md5 = StorageContentValidation.get_content_md5(source_blob_data)
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_client = await self._create_blob(bsc)

        # Act part 1: make append block from url calls with correct md5
        resp = await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                   source_content_md5=src_md5)
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        destination_blob_properties = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert destination_blob_properties.get('etag') == resp.get('etag')
        assert destination_blob_properties.get('last_modified') == resp.get('last_modified')

        # Act part 2: put block from url with wrong md5
        with pytest.raises(HttpResponseError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_content_md5=StorageContentValidation.get_content_md5(
                                                                    b"POTATO"))

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_with_source_if_modified(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        source_blob_properties = await source_blob_client.get_blob_properties()
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_client = await self._create_blob(bsc)

        # Act part 1: make append block from url calls
        resp = await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                   source_offset=0,
                                                                   source_length=LARGE_BLOB_SIZE,
                                                                   source_if_modified_since=source_blob_properties.get(
                                                                       'last_modified') - timedelta(hours=15))
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        destination_blob_properties = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert destination_blob_properties.get('etag') == resp.get('etag')
        assert destination_blob_properties.get('last_modified') == resp.get('last_modified')

        # Act part 2: put block from url with failing condition
        with pytest.raises(ResourceNotFoundError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_offset=0,
                                                                source_length=LARGE_BLOB_SIZE,
                                                                source_if_modified_since=source_blob_properties.get(
                                                                    'last_modified'))

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_with_source_if_unmodified(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        source_blob_properties = await source_blob_client.get_blob_properties()
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_client = await self._create_blob(bsc)

        # Act part 1: make append block from url calls
        resp = await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                   source_offset=0,
                                                                   source_length=LARGE_BLOB_SIZE,
                                                                   source_if_unmodified_since=source_blob_properties.get(
                                                                       'last_modified'))
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        destination_blob_properties = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert destination_blob_properties.get('etag') == resp.get('etag')
        assert destination_blob_properties.get('last_modified') == resp.get('last_modified')
        assert destination_blob_properties.get('size') == LARGE_BLOB_SIZE

        # Act part 2: put block from url with failing condition
        with pytest.raises(ResourceModifiedError):
            await destination_blob_client \
                .append_block_from_url(source_blob_client.url + '?' + sas,
                                       source_offset=0, source_length=LARGE_BLOB_SIZE,
                                       if_unmodified_since=source_blob_properties.get('last_modified') - timedelta(
                                           hours=15))

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_with_source_if_match(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        source_properties = await source_blob_client.get_blob_properties()
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_client = await self._create_blob(bsc)

        # Act part 1: make append block from url calls
        resp = await destination_blob_client. \
            append_block_from_url(source_blob_client.url + '?' + sas,
                                  source_offset=0, source_length=LARGE_BLOB_SIZE,
                                  source_etag=source_properties.get('etag'),
                                  source_match_condition=MatchConditions.IfNotModified)
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        destination_blob_properties = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert destination_blob_properties.get('etag') == resp.get('etag')
        assert destination_blob_properties.get('last_modified') == resp.get('last_modified')

        # Act part 2: put block from url with failing condition
        with pytest.raises(ResourceNotFoundError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_offset=0,
                                                                source_length=LARGE_BLOB_SIZE,
                                                                source_etag='0x111111111111111',
                                                                source_match_condition=MatchConditions.IfNotModified)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_with_source_if_none_match(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        source_properties = await source_blob_client.get_blob_properties()
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_client = await self._create_blob(bsc)

        # Act part 1: make append block from url calls
        resp = await destination_blob_client. \
            append_block_from_url(source_blob_client.url + '?' + sas,
                                  source_offset=0, source_length=LARGE_BLOB_SIZE,
                                  source_etag='0x111111111111111',
                                  source_match_condition=MatchConditions.IfModified)
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        destination_blob_properties = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert destination_blob_properties.get('etag') == resp.get('etag')
        assert destination_blob_properties.get('last_modified') == resp.get('last_modified')

        # Act part 2: put block from url with failing condition
        with pytest.raises(ResourceNotFoundError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_offset=0,
                                                                source_length=LARGE_BLOB_SIZE,
                                                                source_etag=source_properties.get('etag'),
                                                                source_match_condition=MatchConditions.IfModified)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_with_if_match(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_name = self._get_blob_reference()
        destination_blob_client = bsc.get_blob_client(
            self.container_name,
            destination_blob_name)
        destination_blob_properties_on_creation = await destination_blob_client.create_append_blob()

        # Act part 1: make append block from url calls
        resp = await destination_blob_client. \
            append_block_from_url(source_blob_client.url + '?' + sas,
                                  source_offset=0, source_length=LARGE_BLOB_SIZE,
                                  etag=destination_blob_properties_on_creation.get('etag'),
                                  match_condition=MatchConditions.IfNotModified)
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        destination_blob_properties = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert destination_blob_properties.get('etag') == resp.get('etag')
        assert destination_blob_properties.get('last_modified') == resp.get('last_modified')

        # Act part 2: put block from url with failing condition
        with pytest.raises(ResourceModifiedError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_offset=0,
                                                                source_length=LARGE_BLOB_SIZE,
                                                                etag='0x111111111111111',
                                                                match_condition=MatchConditions.IfNotModified)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_with_if_none_match(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_client = await self._create_blob(bsc)

        # Act part 1: make append block from url calls
        resp = await destination_blob_client. \
            append_block_from_url(source_blob_client.url + '?' + sas,
                                  source_offset=0, source_length=LARGE_BLOB_SIZE,
                                  etag='0x111111111111111', match_condition=MatchConditions.IfModified)
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        destination_blob_properties = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert destination_blob_properties.get('etag') == resp.get('etag')
        assert destination_blob_properties.get('last_modified') == resp.get('last_modified')
        assert destination_blob_properties.get('size') == LARGE_BLOB_SIZE

        # Act part 2: put block from url with failing condition
        with pytest.raises(ResourceModifiedError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_offset=0,
                                                                source_length=LARGE_BLOB_SIZE,
                                                                etag=destination_blob_properties.get('etag'),
                                                                match_condition=MatchConditions.IfModified)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_with_maxsize_condition(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_client = await self._create_blob(bsc)

        # Act part 1: make append block from url calls
        resp = await destination_blob_client. \
            append_block_from_url(source_blob_client.url + '?' + sas,
                                  source_offset=0, source_length=LARGE_BLOB_SIZE,
                                  maxsize_condition=LARGE_BLOB_SIZE + 1)
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        destination_blob_properties = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert destination_blob_properties.get('etag') == resp.get('etag')
        assert destination_blob_properties.get('last_modified') == resp.get('last_modified')
        assert destination_blob_properties.get('size') == LARGE_BLOB_SIZE

        # Act part 2: put block from url with failing condition
        with pytest.raises(HttpResponseError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_offset=0,
                                                                source_length=LARGE_BLOB_SIZE,
                                                                maxsize_condition=LARGE_BLOB_SIZE + 1)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_with_appendpos_condition(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_client = await self._create_blob(bsc)

        # Act part 1: make append block from url calls
        resp = await destination_blob_client. \
            append_block_from_url(source_blob_client.url + '?' + sas,
                                  source_offset=0, source_length=LARGE_BLOB_SIZE,
                                  appendpos_condition=0)
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        destination_blob_properties = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert destination_blob_properties.get('etag') == resp.get('etag')
        assert destination_blob_properties.get('last_modified') == resp.get('last_modified')
        assert destination_blob_properties.get('size') == LARGE_BLOB_SIZE

        # Act part 2: put block from url with failing condition
        with pytest.raises(HttpResponseError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_offset=0,
                                                                source_length=LARGE_BLOB_SIZE,
                                                                appendpos_condition=0)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_with_if_modified(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        source_properties = await source_blob_client.get_blob_properties()
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_client = await self._create_blob(bsc)

        # Act part 1: make append block from url calls
        resp = await destination_blob_client. \
            append_block_from_url(source_blob_client.url + '?' + sas,
                                  source_offset=0, source_length=LARGE_BLOB_SIZE,
                                  if_modified_since=source_properties.get('last_modified') - timedelta(minutes=15))
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        destination_blob_properties = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert destination_blob_properties.get('etag') == resp.get('etag')
        assert destination_blob_properties.get('last_modified') == resp.get('last_modified')
        assert destination_blob_properties.get('size') == LARGE_BLOB_SIZE

        # Act part 2: put block from url with failing condition
        with pytest.raises(HttpResponseError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_offset=0,
                                                                source_length=LARGE_BLOB_SIZE,
                                                                if_modified_since=destination_blob_properties.get(
                                                                    'last_modified'))

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_url_with_if_unmodified(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        source_blob_data = self.get_random_bytes(LARGE_BLOB_SIZE)
        source_blob_client = await self._create_source_blob(source_blob_data, bsc)
        source_properties = await source_blob_client.get_blob_properties()
        sas = self.generate_sas(
            generate_blob_sas,
            source_blob_client.account_name,
            source_blob_client.container_name,
            source_blob_client.blob_name,
            snapshot=source_blob_client.snapshot,
            account_key=source_blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True, delete=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        destination_blob_client = await self._create_blob(bsc)

        # Act part 1: make append block from url calls
        resp = await destination_blob_client. \
            append_block_from_url(source_blob_client.url + '?' + sas,
                                  source_offset=0, source_length=LARGE_BLOB_SIZE,
                                  if_unmodified_since=source_properties.get('last_modified') + timedelta(minutes=15))
        assert resp.get('blob_append_offset') == '0'
        assert resp.get('blob_committed_block_count') == 1
        assert resp.get('etag') is not None
        assert resp.get('last_modified') is not None

        # Assert the destination blob is constructed correctly
        destination_blob_properties = await destination_blob_client.get_blob_properties()
        await self.assertBlobEqual(destination_blob_client, source_blob_data)
        assert destination_blob_properties.get('etag') == resp.get('etag')
        assert destination_blob_properties.get('last_modified') == resp.get('last_modified')
        assert destination_blob_properties.get('size') == LARGE_BLOB_SIZE

        # Act part 2: put block from url with failing condition
        with pytest.raises(ResourceModifiedError):
            await destination_blob_client.append_block_from_url(source_blob_client.url + '?' + sas,
                                                                source_offset=0,
                                                                source_length=LARGE_BLOB_SIZE,
                                                                if_unmodified_since=destination_blob_properties.get(
                                                                    'last_modified') - timedelta(minutes=15))

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_create_append_blob_with_no_overwrite(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob_name = self._get_blob_reference()
        blob = bsc.get_blob_client(
            self.container_name,
            blob_name)
        data1 = self.get_random_bytes(LARGE_BLOB_SIZE)
        data2 = self.get_random_bytes(LARGE_BLOB_SIZE + 512)

        # Act
        create_resp = await blob.upload_blob(
            data1,
            overwrite=True,
            blob_type=BlobType.AppendBlob,
            metadata={'blobdata': 'Data1'})

        update_resp = await blob.upload_blob(
            data2,
            overwrite=False,
            blob_type=BlobType.AppendBlob,
            metadata={'blobdata': 'Data2'})

        props = await blob.get_blob_properties()

        # Assert
        appended_data = data1 + data2
        await self.assertBlobEqual(blob, appended_data)
        assert props.etag == update_resp.get('etag')
        assert props.blob_type == BlobType.AppendBlob
        assert props.last_modified == update_resp.get('last_modified')
        assert props.metadata == {'blobdata': 'Data1'}
        assert props.size == LARGE_BLOB_SIZE + LARGE_BLOB_SIZE + 512

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_create_append_blob_with_overwrite(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob_name = self._get_blob_reference()
        blob = bsc.get_blob_client(
            self.container_name,
            blob_name)
        data1 = self.get_random_bytes(LARGE_BLOB_SIZE)
        data2 = self.get_random_bytes(LARGE_BLOB_SIZE + 512)

        # Act
        create_resp = await blob.upload_blob(
            data1,
            overwrite=True,
            blob_type=BlobType.AppendBlob,
            metadata={'blobdata': 'Data1'})
        update_resp = await blob.upload_blob(
            data2,
            overwrite=True,
            blob_type=BlobType.AppendBlob,
            metadata={'blobdata': 'Data2'})

        props = await blob.get_blob_properties()

        # Assert
        await self.assertBlobEqual(blob, data2)
        assert props.etag == update_resp.get('etag')
        assert props.last_modified == update_resp.get('last_modified')
        assert props.metadata == {'blobdata': 'Data2'}
        assert props.blob_type == BlobType.AppendBlob
        assert props.size == LARGE_BLOB_SIZE + 512

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_bytes(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)

        # Act
        data = b'abcdefghijklmnopqrstuvwxyz'
        append_resp = await blob.upload_blob(data, blob_type=BlobType.AppendBlob)
        blob_properties = await blob.get_blob_properties()

        # Assert
        await self.assertBlobEqual(blob, data)
        assert blob_properties.etag == append_resp['etag']
        assert blob_properties.last_modified == append_resp['last_modified']

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_0_bytes(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)

        # Act
        data = b''
        append_resp = await blob.upload_blob(data, blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, data)
        # appending nothing should not make any network call
        assert append_resp.get('etag') is None
        assert append_resp.get('last_modified') is None

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_bytes_with_progress(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = b'abcdefghijklmnopqrstuvwxyz'

        # Act
        progress = []

        def progress_gen(upload):
            progress.append((0, len(upload)))
            yield upload

        upload_data = progress_gen(data)
        await blob.upload_blob(upload_data, blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, data)
        self.assert_upload_progress(len(data), self.config.max_block_size, progress)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_bytes_with_index(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)

        # Act
        data = b'abcdefghijklmnopqrstuvwxyz'
        await blob.upload_blob(data[3:], blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, data[3:])

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_bytes_with_index_and_count(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)

        # Act
        data = b'abcdefghijklmnopqrstuvwxyz'
        await blob.upload_blob(data[3:], length=5, blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, data[3:8])

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_bytes_chunked_upload(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(LARGE_BLOB_SIZE)

        # Act
        append_resp = await blob.upload_blob(data, blob_type=BlobType.AppendBlob)
        blob_properties = await blob.get_blob_properties()

        # Assert
        await self.assertBlobEqual(blob, data)
        assert blob_properties.etag == append_resp['etag']
        assert blob_properties.last_modified == append_resp.get('last_modified')

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_app_blob_from_bytes_progress_chnked_upload(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(LARGE_BLOB_SIZE)

        # Act
        progress = []

        def progress_gen(upload):
            n = self.config.max_block_size
            total = len(upload)
            current = 0
            while upload:
                progress.append((current, total))
                yield upload[:n]
                current += len(upload[:n])
                upload = upload[n:]

        upload_data = progress_gen(data)
        await blob.upload_blob(upload_data, blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, data)
        self.assert_upload_progress(len(data), self.config.max_block_size, progress)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_appblob_frm_bytes_chnked_upload_w_idx_n_count(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(LARGE_BLOB_SIZE)
        index = 33
        blob_size = len(data) - 66

        # Act
        await blob.upload_blob(data[index:], length=blob_size, blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, data[index:index + blob_size])

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_path_chunked_upload(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(LARGE_BLOB_SIZE)

        # Act
        with tempfile.TemporaryFile() as temp_file:
            temp_file.write(data)
            temp_file.seek(0)
            append_resp = await blob.upload_blob(temp_file, blob_type=BlobType.AppendBlob)
        blob_properties = await blob.get_blob_properties()

        # Assert
        await self.assertBlobEqual(blob, data)
        assert blob_properties.etag == append_resp.get('etag')
        assert blob_properties.last_modified == append_resp.get('last_modified')

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_path_with_progress_chunked_upload(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(LARGE_BLOB_SIZE)

        # Act
        progress = []

        def progress_gen(upload):
            n = self.config.max_block_size
            total = LARGE_BLOB_SIZE
            current = 0
            while upload:
                chunk = upload.read(n)
                if not chunk:
                    break
                progress.append((current, total))
                yield chunk
                current += len(chunk)

        with tempfile.TemporaryFile() as temp_file:
            temp_file.write(data)
            temp_file.seek(0)
            upload_data = progress_gen(temp_file)
            await blob.upload_blob(upload_data, blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, data)
        self.assert_upload_progress(len(data), self.config.max_block_size, progress)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_stream_chunked_upload(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(LARGE_BLOB_SIZE)

        # Act
        with tempfile.TemporaryFile() as temp_file:
            temp_file.write(data)
            temp_file.seek(0)
            append_resp = await blob.upload_blob(temp_file, blob_type=BlobType.AppendBlob)
        blob_properties = await blob.get_blob_properties()

        # Assert
        await self.assertBlobEqual(blob, data)
        assert blob_properties.etag == append_resp.get('etag')
        assert blob_properties.last_modified == append_resp.get('last_modified')

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_stream_non_seekable_chunked_upload_known_size(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(LARGE_BLOB_SIZE)
        blob_size = len(data) - 66

        # Act
        with tempfile.TemporaryFile() as temp_file:
            temp_file.write(data)
            temp_file.seek(0)
            non_seekable_file = NonSeekableStream(temp_file)
            await blob.upload_blob(non_seekable_file, length=blob_size, blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, data[:blob_size])

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_stream_non_seekable_chunked_upload_unknown_size(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(LARGE_BLOB_SIZE)

        # Act
        with tempfile.TemporaryFile() as temp_file:
            temp_file.write(data)
            temp_file.seek(0)
            non_seekable_file = NonSeekableStream(temp_file)
            await blob.upload_blob(non_seekable_file, blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, data)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_stream_with_multiple_appends(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(LARGE_BLOB_SIZE)

        # Act
        with tempfile.TemporaryFile() as temp_file:
            temp_file.write(data)
            temp_file.seek(0)
            await blob.upload_blob(temp_file, blob_type=BlobType.AppendBlob)
        with tempfile.TemporaryFile() as temp_file2:
            temp_file2.write(data)
            temp_file2.seek(0)
            await blob.upload_blob(temp_file2, blob_type=BlobType.AppendBlob)

        # Assert
        data = data * 2
        await self.assertBlobEqual(blob, data)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_stream_chunked_upload_with_count(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(LARGE_BLOB_SIZE)

        # Act
        blob_size = len(data) - 301
        with tempfile.TemporaryFile() as temp_file:
            temp_file.write(data)
            temp_file.seek(0)
            await blob.upload_blob(temp_file, length=blob_size, blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, data[:blob_size])

    @pytest.mark.live_test_only
    @BlobPreparer()
    async def test_append_blob_from_stream_chunked_upload_with_count_parallel(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # parallel tests introduce random order of requests, can only run live
        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_bytes(LARGE_BLOB_SIZE)

        # Act
        blob_size = len(data) - 301
        with tempfile.TemporaryFile() as temp_file:
            temp_file.write(data)
            temp_file.seek(0)
            append_resp = await blob.upload_blob(temp_file, length=blob_size, blob_type=BlobType.AppendBlob)
        blob_properties = await blob.get_blob_properties()

        # Assert
        await self.assertBlobEqual(blob, data[:blob_size])
        assert blob_properties.etag == append_resp.get('etag')
        assert blob_properties.last_modified == append_resp.get('last_modified')

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_text(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        text = u'hello 啊齄丂狛狜 world'
        data = text.encode('utf-8')

        # Act
        append_resp = await blob.upload_blob(text, blob_type=BlobType.AppendBlob)
        blob_properties = await blob.get_blob_properties()

        # Assert
        await self.assertBlobEqual(blob, data)
        assert blob_properties.etag == append_resp.get('etag')
        assert blob_properties.last_modified == append_resp.get('last_modified')

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_text_with_encoding(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        text = u'hello 啊齄丂狛狜 world'
        data = text.encode('utf-16')

        # Act
        await blob.upload_blob(text, encoding='utf-16', blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, data)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_text_with_encoding_and_progress(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        text = u'hello 啊齄丂狛狜 world'
        data = text.encode('utf-16')

        # Act
        progress = []

        def progress_gen(upload):
            progress.append((0, len(data)))
            yield upload

        upload_data = progress_gen(text)
        await blob.upload_blob(upload_data, encoding='utf-16', blob_type=BlobType.AppendBlob)

        # Assert
        self.assert_upload_progress(len(data), self.config.max_block_size, progress)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_from_text_chunked_upload(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = self.get_random_text_data(LARGE_BLOB_SIZE)
        encoded_data = data.encode('utf-8')

        # Act
        await blob.upload_blob(data, blob_type=BlobType.AppendBlob)

        # Assert
        await self.assertBlobEqual(blob, encoded_data)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_blob_with_md5(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        data = b'hello world'

        # Act
        await blob.append_block(data, validate_content=True)

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_seal_append_blob(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        resp = await blob.seal_append_blob()
        assert resp['blob_sealed']

        with pytest.raises(HttpResponseError):
            await blob.append_block("abc")

        await blob.set_blob_metadata({'isseal': 'yes'})
        prop = await blob.get_blob_properties()

        assert prop.metadata['isseal'] == 'yes'

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_seal_append_blob_with_append_condition(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)
        with pytest.raises(HttpResponseError):
            await blob.seal_append_blob(appendpos_condition=1)

        resp = await blob.seal_append_blob(appendpos_condition=0)
        assert resp['blob_sealed']

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_copy_sealed_blob_will_get_a_sealed_blob(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)

        # copy sealed blob will get a sealed blob
        await blob.seal_append_blob()
        copied_blob = bsc.get_blob_client(self.container_name, "copiedblob")
        await copied_blob.start_copy_from_url(blob.url)
        prop = await copied_blob.get_blob_properties()

        assert prop.is_append_blob_sealed
        with pytest.raises(HttpResponseError):
            await copied_blob.append_block("abc")

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_copy_unsealed_blob_will_get_a_sealed_blob(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)

        # copy unsealed blob with seal_destination_blob=True will get a sealed blob
        copied_blob2 = bsc.get_blob_client(self.container_name, "copiedblob2")
        await copied_blob2.start_copy_from_url(blob.url, seal_destination_blob=True)
        prop = await copied_blob2.get_blob_properties()

        assert prop.is_append_blob_sealed
        with pytest.raises(HttpResponseError):
            await copied_blob2.append_block("abc")

        blobs_gen = bsc.get_container_client(self.container_name).list_blobs()
        async for blob in blobs_gen:
            if blob.name == "copiedblob2":
                assert blob.is_append_blob_sealed

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_copy_sealed_blob_with_seal_blob_will_get_a_sealed_blob(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)
        blob = await self._create_blob(bsc)

        # copy sealed blob with seal_destination_blob=True will get a sealed blob
        await blob.seal_append_blob()
        copied_blob3 = bsc.get_blob_client(self.container_name, "copiedblob3")
        await copied_blob3.start_copy_from_url(blob.url, seal_destination_blob=False)

        prop = await copied_blob3.get_blob_properties()

        assert prop.is_append_blob_sealed is None
        await copied_blob3.append_block("abc")

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_create_append_blob_with_immutability_policy(self, **kwargs):
        versioned_storage_account_name = kwargs.pop("versioned_storage_account_name")
        versioned_storage_account_key = kwargs.pop("versioned_storage_account_key")
        storage_resource_group_name = kwargs.pop("storage_resource_group_name")
        variables = kwargs.pop("variables", {})

        bsc = BlobServiceClient(self.account_url(versioned_storage_account_name, "blob"), versioned_storage_account_key, max_block_size=4 * 1024)
        await self._setup(bsc)

        container_name = self.get_resource_name('vlwcontainerasync')
        if self.is_live:
            token_credential = self.get_credential(BlobServiceClient, is_async=True)
            subscription_id = self.get_settings_value("SUBSCRIPTION_ID")
            mgmt_client = StorageManagementClient(token_credential, subscription_id, '2021-04-01')
            property = mgmt_client.models().BlobContainer(
                immutable_storage_with_versioning=mgmt_client.models().ImmutableStorageWithVersioning(enabled=True))
            await mgmt_client.blob_containers.create(storage_resource_group_name, versioned_storage_account_name, container_name, blob_container=property)

        # Act
        blob_name = self.get_resource_name('vlwblob')
        blob = bsc.get_blob_client(container_name, blob_name)

        expiry_time = self.get_datetime_variable(variables, 'expiry_time', datetime.utcnow() + timedelta(seconds=10))
        immutability_policy = ImmutabilityPolicy(expiry_time=expiry_time, policy_mode=BlobImmutabilityPolicyMode.Unlocked)
        await blob.create_append_blob(immutability_policy=immutability_policy,
                                      legal_hold=True)

        props = await blob.get_blob_properties()

        with pytest.raises(HttpResponseError):
            await blob.delete_blob()

        assert props['has_legal_hold']
        assert props['immutability_policy']['expiry_time'] is not None
        assert props['immutability_policy']['policy_mode'] is not None

        if self.is_live:
            await blob.delete_immutability_policy()
            await blob.set_legal_hold(False)
            await blob.delete_blob()
            await mgmt_client.blob_containers.delete(storage_resource_group_name, versioned_storage_account_name, container_name)

        return variables

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_upload_progress_chunked(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        bsc = BlobServiceClient(self.account_url(storage_account_name, "blob"), storage_account_key)
        await self._setup(bsc)

        blob_name = self._get_blob_reference()
        data = b'a' * 5 * 1024

        progress = ProgressTracker(len(data), 1024)

        # Act
        blob_client = BlobClient(
            self.account_url(storage_account_name, 'blob'),
            self.container_name, blob_name,
            credential=storage_account_key,
            max_single_put_size=1024, max_block_size=1024)

        await blob_client.upload_blob(
            data,
            blob_type=BlobType.AppendBlob,
            overwrite=True,
            max_concurrency=1,
            progress_hook=progress.assert_progress)

        # Assert
        progress.assert_complete()

    @BlobPreparer()
    @recorded_by_proxy_async
    async def test_append_block_from_file_to_blob_with_oauth(self, **kwargs):
        storage_account_name = kwargs.pop("storage_account_name")
        storage_account_key = kwargs.pop("storage_account_key")

        # Arrange
        account_url = self.account_url(storage_account_name, "blob")
        bsc = BlobServiceClient(account_url, storage_account_key)
        await self._setup(bsc)
        bearer_token_string = await self._get_bearer_token_string()

        # Set up source file share with random data
        source_data = self.get_random_bytes(SMALL_BLOB_SIZE)
        file_name, base_url = await _create_file_share_oauth(
            self.get_resource_name("utshare"),
            self.get_resource_name("file"),
            bearer_token_string,
            storage_account_name,
            source_data
        )

        # Set up destination blob without data
        destination_blob_client = BlobClient(
            account_url=account_url,
            container_name=self.source_container_name,
            blob_name=self.get_resource_name(TEST_BLOB_PREFIX + "1"),
            credential=storage_account_key
        )
        await destination_blob_client.create_append_blob()

        try:
            # Act
            await destination_blob_client.append_block_from_url(
                copy_source_url=base_url + "/" + file_name,
                source_authorization=bearer_token_string,
                source_token_intent='backup'
            )
            destination_blob = await destination_blob_client.download_blob()
            destination_blob_data = await destination_blob.readall()

            # Assert
            assert destination_blob_data == source_data
        finally:
            async with aiohttp.ClientSession() as session:
                await session.delete(
                    url=base_url,
                    headers=_build_base_file_share_headers(bearer_token_string, 0),
                    params={'restype': 'share'}
                )
            await bsc.delete_container(self.source_container_name)

# ------------------------------------------------------------------------------
