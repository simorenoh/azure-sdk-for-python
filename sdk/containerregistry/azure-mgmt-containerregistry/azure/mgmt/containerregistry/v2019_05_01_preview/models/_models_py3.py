# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------

import datetime
from typing import Any, List, Optional, TYPE_CHECKING, Union

from .._utils import serialization as _serialization

if TYPE_CHECKING:
    from .. import models as _models


class ActiveDirectoryObject(_serialization.Model):
    """The Active Directory Object that will be used for authenticating the token of a container
    registry.

    :ivar object_id: The user/group/application object ID for Active Directory Object that will be
     used for authenticating the token of a container registry.
    :vartype object_id: str
    :ivar tenant_id: The tenant ID of user/group/application object Active Directory Object that
     will be used for authenticating the token of a container registry.
    :vartype tenant_id: str
    """

    _attribute_map = {
        "object_id": {"key": "objectId", "type": "str"},
        "tenant_id": {"key": "tenantId", "type": "str"},
    }

    def __init__(self, *, object_id: Optional[str] = None, tenant_id: Optional[str] = None, **kwargs: Any) -> None:
        """
        :keyword object_id: The user/group/application object ID for Active Directory Object that will
         be used for authenticating the token of a container registry.
        :paramtype object_id: str
        :keyword tenant_id: The tenant ID of user/group/application object Active Directory Object that
         will be used for authenticating the token of a container registry.
        :paramtype tenant_id: str
        """
        super().__init__(**kwargs)
        self.object_id = object_id
        self.tenant_id = tenant_id


class GenerateCredentialsParameters(_serialization.Model):
    """The parameters used to generate credentials for a specified token or user of a container
    registry.

    :ivar token_id: The resource ID of the token for which credentials have to be generated.
    :vartype token_id: str
    :ivar expiry: The expiry date of the generated credentials after which the credentials become
     invalid.
    :vartype expiry: ~datetime.datetime
    :ivar name: Specifies name of the password which should be regenerated if any -- password1 or
     password2. Known values are: "password1" and "password2".
    :vartype name: str or
     ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenPasswordName
    """

    _attribute_map = {
        "token_id": {"key": "tokenId", "type": "str"},
        "expiry": {"key": "expiry", "type": "iso-8601"},
        "name": {"key": "name", "type": "str"},
    }

    def __init__(
        self,
        *,
        token_id: Optional[str] = None,
        expiry: Optional[datetime.datetime] = None,
        name: Optional[Union[str, "_models.TokenPasswordName"]] = None,
        **kwargs: Any
    ) -> None:
        """
        :keyword token_id: The resource ID of the token for which credentials have to be generated.
        :paramtype token_id: str
        :keyword expiry: The expiry date of the generated credentials after which the credentials
         become invalid.
        :paramtype expiry: ~datetime.datetime
        :keyword name: Specifies name of the password which should be regenerated if any -- password1
         or password2. Known values are: "password1" and "password2".
        :paramtype name: str or
         ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenPasswordName
        """
        super().__init__(**kwargs)
        self.token_id = token_id
        self.expiry = expiry
        self.name = name


class GenerateCredentialsResult(_serialization.Model):
    """The response from the GenerateCredentials operation.

    :ivar username: The username for a container registry.
    :vartype username: str
    :ivar passwords: The list of passwords for a container registry.
    :vartype passwords:
     list[~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenPassword]
    """

    _attribute_map = {
        "username": {"key": "username", "type": "str"},
        "passwords": {"key": "passwords", "type": "[TokenPassword]"},
    }

    def __init__(
        self,
        *,
        username: Optional[str] = None,
        passwords: Optional[List["_models.TokenPassword"]] = None,
        **kwargs: Any
    ) -> None:
        """
        :keyword username: The username for a container registry.
        :paramtype username: str
        :keyword passwords: The list of passwords for a container registry.
        :paramtype passwords:
         list[~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenPassword]
        """
        super().__init__(**kwargs)
        self.username = username
        self.passwords = passwords


class ProxyResource(_serialization.Model):
    """The resource model definition for a ARM proxy resource. It will have everything other than
    required location and tags.

    Variables are only populated by the server, and will be ignored when sending a request.

    :ivar id: The resource ID.
    :vartype id: str
    :ivar name: The name of the resource.
    :vartype name: str
    :ivar type: The type of the resource.
    :vartype type: str
    :ivar system_data: Metadata pertaining to creation and last modification of the resource.
    :vartype system_data: ~azure.mgmt.containerregistry.v2019_05_01_preview.models.SystemData
    """

    _validation = {
        "id": {"readonly": True},
        "name": {"readonly": True},
        "type": {"readonly": True},
        "system_data": {"readonly": True},
    }

    _attribute_map = {
        "id": {"key": "id", "type": "str"},
        "name": {"key": "name", "type": "str"},
        "type": {"key": "type", "type": "str"},
        "system_data": {"key": "systemData", "type": "SystemData"},
    }

    def __init__(self, **kwargs: Any) -> None:
        """ """
        super().__init__(**kwargs)
        self.id: Optional[str] = None
        self.name: Optional[str] = None
        self.type: Optional[str] = None
        self.system_data: Optional["_models.SystemData"] = None


class ScopeMap(ProxyResource):
    """An object that represents a scope map for a container registry.

    Variables are only populated by the server, and will be ignored when sending a request.

    :ivar id: The resource ID.
    :vartype id: str
    :ivar name: The name of the resource.
    :vartype name: str
    :ivar type: The type of the resource.
    :vartype type: str
    :ivar system_data: Metadata pertaining to creation and last modification of the resource.
    :vartype system_data: ~azure.mgmt.containerregistry.v2019_05_01_preview.models.SystemData
    :ivar description: The user friendly description of the scope map.
    :vartype description: str
    :ivar type_properties_type: The type of the scope map. E.g. BuildIn scope map.
    :vartype type_properties_type: str
    :ivar creation_date: The creation date of scope map.
    :vartype creation_date: ~datetime.datetime
    :ivar provisioning_state: Provisioning state of the resource. Known values are: "Creating",
     "Updating", "Deleting", "Succeeded", "Failed", and "Canceled".
    :vartype provisioning_state: str or
     ~azure.mgmt.containerregistry.v2019_05_01_preview.models.ProvisioningState
    :ivar actions: The list of scoped permissions for registry artifacts.
     E.g. repositories/repository-name/content/read,
     repositories/repository-name/metadata/write.
    :vartype actions: list[str]
    """

    _validation = {
        "id": {"readonly": True},
        "name": {"readonly": True},
        "type": {"readonly": True},
        "system_data": {"readonly": True},
        "type_properties_type": {"readonly": True},
        "creation_date": {"readonly": True},
        "provisioning_state": {"readonly": True},
    }

    _attribute_map = {
        "id": {"key": "id", "type": "str"},
        "name": {"key": "name", "type": "str"},
        "type": {"key": "type", "type": "str"},
        "system_data": {"key": "systemData", "type": "SystemData"},
        "description": {"key": "properties.description", "type": "str"},
        "type_properties_type": {"key": "properties.type", "type": "str"},
        "creation_date": {"key": "properties.creationDate", "type": "iso-8601"},
        "provisioning_state": {"key": "properties.provisioningState", "type": "str"},
        "actions": {"key": "properties.actions", "type": "[str]"},
    }

    def __init__(
        self, *, description: Optional[str] = None, actions: Optional[List[str]] = None, **kwargs: Any
    ) -> None:
        """
        :keyword description: The user friendly description of the scope map.
        :paramtype description: str
        :keyword actions: The list of scoped permissions for registry artifacts.
         E.g. repositories/repository-name/content/read,
         repositories/repository-name/metadata/write.
        :paramtype actions: list[str]
        """
        super().__init__(**kwargs)
        self.description = description
        self.type_properties_type: Optional[str] = None
        self.creation_date: Optional[datetime.datetime] = None
        self.provisioning_state: Optional[Union[str, "_models.ProvisioningState"]] = None
        self.actions = actions


class ScopeMapListResult(_serialization.Model):
    """The result of a request to list scope maps for a container registry.

    :ivar value: The list of scope maps. Since this list may be incomplete, the nextLink field
     should be used to request the next list of scope maps.
    :vartype value: list[~azure.mgmt.containerregistry.v2019_05_01_preview.models.ScopeMap]
    :ivar next_link: The URI that can be used to request the next list of scope maps.
    :vartype next_link: str
    """

    _attribute_map = {
        "value": {"key": "value", "type": "[ScopeMap]"},
        "next_link": {"key": "nextLink", "type": "str"},
    }

    def __init__(
        self, *, value: Optional[List["_models.ScopeMap"]] = None, next_link: Optional[str] = None, **kwargs: Any
    ) -> None:
        """
        :keyword value: The list of scope maps. Since this list may be incomplete, the nextLink field
         should be used to request the next list of scope maps.
        :paramtype value: list[~azure.mgmt.containerregistry.v2019_05_01_preview.models.ScopeMap]
        :keyword next_link: The URI that can be used to request the next list of scope maps.
        :paramtype next_link: str
        """
        super().__init__(**kwargs)
        self.value = value
        self.next_link = next_link


class ScopeMapUpdateParameters(_serialization.Model):
    """The properties for updating the scope map.

    :ivar description: The user friendly description of the scope map.
    :vartype description: str
    :ivar actions: The list of scope permissions for registry artifacts.
     E.g. repositories/repository-name/pull,
     repositories/repository-name/delete.
    :vartype actions: list[str]
    """

    _attribute_map = {
        "description": {"key": "properties.description", "type": "str"},
        "actions": {"key": "properties.actions", "type": "[str]"},
    }

    def __init__(
        self, *, description: Optional[str] = None, actions: Optional[List[str]] = None, **kwargs: Any
    ) -> None:
        """
        :keyword description: The user friendly description of the scope map.
        :paramtype description: str
        :keyword actions: The list of scope permissions for registry artifacts.
         E.g. repositories/repository-name/pull,
         repositories/repository-name/delete.
        :paramtype actions: list[str]
        """
        super().__init__(**kwargs)
        self.description = description
        self.actions = actions


class SystemData(_serialization.Model):
    """Metadata pertaining to creation and last modification of the resource.

    :ivar created_by: The identity that created the resource.
    :vartype created_by: str
    :ivar created_by_type: The type of identity that created the resource. Known values are:
     "User", "Application", "ManagedIdentity", and "Key".
    :vartype created_by_type: str or
     ~azure.mgmt.containerregistry.v2019_05_01_preview.models.CreatedByType
    :ivar created_at: The timestamp of resource creation (UTC).
    :vartype created_at: ~datetime.datetime
    :ivar last_modified_by: The identity that last modified the resource.
    :vartype last_modified_by: str
    :ivar last_modified_by_type: The type of identity that last modified the resource. Known values
     are: "User", "Application", "ManagedIdentity", and "Key".
    :vartype last_modified_by_type: str or
     ~azure.mgmt.containerregistry.v2019_05_01_preview.models.LastModifiedByType
    :ivar last_modified_at: The timestamp of resource modification (UTC).
    :vartype last_modified_at: ~datetime.datetime
    """

    _attribute_map = {
        "created_by": {"key": "createdBy", "type": "str"},
        "created_by_type": {"key": "createdByType", "type": "str"},
        "created_at": {"key": "createdAt", "type": "iso-8601"},
        "last_modified_by": {"key": "lastModifiedBy", "type": "str"},
        "last_modified_by_type": {"key": "lastModifiedByType", "type": "str"},
        "last_modified_at": {"key": "lastModifiedAt", "type": "iso-8601"},
    }

    def __init__(
        self,
        *,
        created_by: Optional[str] = None,
        created_by_type: Optional[Union[str, "_models.CreatedByType"]] = None,
        created_at: Optional[datetime.datetime] = None,
        last_modified_by: Optional[str] = None,
        last_modified_by_type: Optional[Union[str, "_models.LastModifiedByType"]] = None,
        last_modified_at: Optional[datetime.datetime] = None,
        **kwargs: Any
    ) -> None:
        """
        :keyword created_by: The identity that created the resource.
        :paramtype created_by: str
        :keyword created_by_type: The type of identity that created the resource. Known values are:
         "User", "Application", "ManagedIdentity", and "Key".
        :paramtype created_by_type: str or
         ~azure.mgmt.containerregistry.v2019_05_01_preview.models.CreatedByType
        :keyword created_at: The timestamp of resource creation (UTC).
        :paramtype created_at: ~datetime.datetime
        :keyword last_modified_by: The identity that last modified the resource.
        :paramtype last_modified_by: str
        :keyword last_modified_by_type: The type of identity that last modified the resource. Known
         values are: "User", "Application", "ManagedIdentity", and "Key".
        :paramtype last_modified_by_type: str or
         ~azure.mgmt.containerregistry.v2019_05_01_preview.models.LastModifiedByType
        :keyword last_modified_at: The timestamp of resource modification (UTC).
        :paramtype last_modified_at: ~datetime.datetime
        """
        super().__init__(**kwargs)
        self.created_by = created_by
        self.created_by_type = created_by_type
        self.created_at = created_at
        self.last_modified_by = last_modified_by
        self.last_modified_by_type = last_modified_by_type
        self.last_modified_at = last_modified_at


class Token(ProxyResource):
    """An object that represents a token for a container registry.

    Variables are only populated by the server, and will be ignored when sending a request.

    :ivar id: The resource ID.
    :vartype id: str
    :ivar name: The name of the resource.
    :vartype name: str
    :ivar type: The type of the resource.
    :vartype type: str
    :ivar system_data: Metadata pertaining to creation and last modification of the resource.
    :vartype system_data: ~azure.mgmt.containerregistry.v2019_05_01_preview.models.SystemData
    :ivar creation_date: The creation date of scope map.
    :vartype creation_date: ~datetime.datetime
    :ivar provisioning_state: Provisioning state of the resource. Known values are: "Creating",
     "Updating", "Deleting", "Succeeded", "Failed", and "Canceled".
    :vartype provisioning_state: str or
     ~azure.mgmt.containerregistry.v2019_05_01_preview.models.ProvisioningState
    :ivar scope_map_id: The resource ID of the scope map to which the token will be associated
     with.
    :vartype scope_map_id: str
    :ivar credentials: The credentials that can be used for authenticating the token.
    :vartype credentials:
     ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenCredentialsProperties
    :ivar status: The status of the token example enabled or disabled. Known values are: "enabled"
     and "disabled".
    :vartype status: str or ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenStatus
    """

    _validation = {
        "id": {"readonly": True},
        "name": {"readonly": True},
        "type": {"readonly": True},
        "system_data": {"readonly": True},
        "creation_date": {"readonly": True},
        "provisioning_state": {"readonly": True},
    }

    _attribute_map = {
        "id": {"key": "id", "type": "str"},
        "name": {"key": "name", "type": "str"},
        "type": {"key": "type", "type": "str"},
        "system_data": {"key": "systemData", "type": "SystemData"},
        "creation_date": {"key": "properties.creationDate", "type": "iso-8601"},
        "provisioning_state": {"key": "properties.provisioningState", "type": "str"},
        "scope_map_id": {"key": "properties.scopeMapId", "type": "str"},
        "credentials": {"key": "properties.credentials", "type": "TokenCredentialsProperties"},
        "status": {"key": "properties.status", "type": "str"},
    }

    def __init__(
        self,
        *,
        scope_map_id: Optional[str] = None,
        credentials: Optional["_models.TokenCredentialsProperties"] = None,
        status: Optional[Union[str, "_models.TokenStatus"]] = None,
        **kwargs: Any
    ) -> None:
        """
        :keyword scope_map_id: The resource ID of the scope map to which the token will be associated
         with.
        :paramtype scope_map_id: str
        :keyword credentials: The credentials that can be used for authenticating the token.
        :paramtype credentials:
         ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenCredentialsProperties
        :keyword status: The status of the token example enabled or disabled. Known values are:
         "enabled" and "disabled".
        :paramtype status: str or ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenStatus
        """
        super().__init__(**kwargs)
        self.creation_date: Optional[datetime.datetime] = None
        self.provisioning_state: Optional[Union[str, "_models.ProvisioningState"]] = None
        self.scope_map_id = scope_map_id
        self.credentials = credentials
        self.status = status


class TokenCertificate(_serialization.Model):
    """The properties of a certificate used for authenticating a token.

    :ivar name: Known values are: "certificate1" and "certificate2".
    :vartype name: str or
     ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenCertificateName
    :ivar expiry: The expiry datetime of the certificate.
    :vartype expiry: ~datetime.datetime
    :ivar thumbprint: The thumbprint of the certificate.
    :vartype thumbprint: str
    :ivar encoded_pem_certificate: Base 64 encoded string of the public certificate1 in PEM format
     that will be used for authenticating the token.
    :vartype encoded_pem_certificate: str
    """

    _attribute_map = {
        "name": {"key": "name", "type": "str"},
        "expiry": {"key": "expiry", "type": "iso-8601"},
        "thumbprint": {"key": "thumbprint", "type": "str"},
        "encoded_pem_certificate": {"key": "encodedPemCertificate", "type": "str"},
    }

    def __init__(
        self,
        *,
        name: Optional[Union[str, "_models.TokenCertificateName"]] = None,
        expiry: Optional[datetime.datetime] = None,
        thumbprint: Optional[str] = None,
        encoded_pem_certificate: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        :keyword name: Known values are: "certificate1" and "certificate2".
        :paramtype name: str or
         ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenCertificateName
        :keyword expiry: The expiry datetime of the certificate.
        :paramtype expiry: ~datetime.datetime
        :keyword thumbprint: The thumbprint of the certificate.
        :paramtype thumbprint: str
        :keyword encoded_pem_certificate: Base 64 encoded string of the public certificate1 in PEM
         format that will be used for authenticating the token.
        :paramtype encoded_pem_certificate: str
        """
        super().__init__(**kwargs)
        self.name = name
        self.expiry = expiry
        self.thumbprint = thumbprint
        self.encoded_pem_certificate = encoded_pem_certificate


class TokenCredentialsProperties(_serialization.Model):
    """The properties of the credentials that can be used for authenticating the token.

    :ivar active_directory_object: The Active Directory Object that will be used for authenticating
     the token of a container registry.
    :vartype active_directory_object:
     ~azure.mgmt.containerregistry.v2019_05_01_preview.models.ActiveDirectoryObject
    :ivar certificates:
    :vartype certificates:
     list[~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenCertificate]
    :ivar passwords:
    :vartype passwords:
     list[~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenPassword]
    """

    _attribute_map = {
        "active_directory_object": {"key": "activeDirectoryObject", "type": "ActiveDirectoryObject"},
        "certificates": {"key": "certificates", "type": "[TokenCertificate]"},
        "passwords": {"key": "passwords", "type": "[TokenPassword]"},
    }

    def __init__(
        self,
        *,
        active_directory_object: Optional["_models.ActiveDirectoryObject"] = None,
        certificates: Optional[List["_models.TokenCertificate"]] = None,
        passwords: Optional[List["_models.TokenPassword"]] = None,
        **kwargs: Any
    ) -> None:
        """
        :keyword active_directory_object: The Active Directory Object that will be used for
         authenticating the token of a container registry.
        :paramtype active_directory_object:
         ~azure.mgmt.containerregistry.v2019_05_01_preview.models.ActiveDirectoryObject
        :keyword certificates:
        :paramtype certificates:
         list[~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenCertificate]
        :keyword passwords:
        :paramtype passwords:
         list[~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenPassword]
        """
        super().__init__(**kwargs)
        self.active_directory_object = active_directory_object
        self.certificates = certificates
        self.passwords = passwords


class TokenListResult(_serialization.Model):
    """The result of a request to list tokens for a container registry.

    :ivar value: The list of tokens. Since this list may be incomplete, the nextLink field should
     be used to request the next list of tokens.
    :vartype value: list[~azure.mgmt.containerregistry.v2019_05_01_preview.models.Token]
    :ivar next_link: The URI that can be used to request the next list of tokens.
    :vartype next_link: str
    """

    _attribute_map = {
        "value": {"key": "value", "type": "[Token]"},
        "next_link": {"key": "nextLink", "type": "str"},
    }

    def __init__(
        self, *, value: Optional[List["_models.Token"]] = None, next_link: Optional[str] = None, **kwargs: Any
    ) -> None:
        """
        :keyword value: The list of tokens. Since this list may be incomplete, the nextLink field
         should be used to request the next list of tokens.
        :paramtype value: list[~azure.mgmt.containerregistry.v2019_05_01_preview.models.Token]
        :keyword next_link: The URI that can be used to request the next list of tokens.
        :paramtype next_link: str
        """
        super().__init__(**kwargs)
        self.value = value
        self.next_link = next_link


class TokenPassword(_serialization.Model):
    """The password that will be used for authenticating the token of a container registry.

    Variables are only populated by the server, and will be ignored when sending a request.

    :ivar creation_time: The creation datetime of the password.
    :vartype creation_time: ~datetime.datetime
    :ivar expiry: The expiry datetime of the password.
    :vartype expiry: ~datetime.datetime
    :ivar name: The password name "password1" or "password2". Known values are: "password1" and
     "password2".
    :vartype name: str or
     ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenPasswordName
    :ivar value: The password value.
    :vartype value: str
    """

    _validation = {
        "value": {"readonly": True},
    }

    _attribute_map = {
        "creation_time": {"key": "creationTime", "type": "iso-8601"},
        "expiry": {"key": "expiry", "type": "iso-8601"},
        "name": {"key": "name", "type": "str"},
        "value": {"key": "value", "type": "str"},
    }

    def __init__(
        self,
        *,
        creation_time: Optional[datetime.datetime] = None,
        expiry: Optional[datetime.datetime] = None,
        name: Optional[Union[str, "_models.TokenPasswordName"]] = None,
        **kwargs: Any
    ) -> None:
        """
        :keyword creation_time: The creation datetime of the password.
        :paramtype creation_time: ~datetime.datetime
        :keyword expiry: The expiry datetime of the password.
        :paramtype expiry: ~datetime.datetime
        :keyword name: The password name "password1" or "password2". Known values are: "password1" and
         "password2".
        :paramtype name: str or
         ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenPasswordName
        """
        super().__init__(**kwargs)
        self.creation_time = creation_time
        self.expiry = expiry
        self.name = name
        self.value: Optional[str] = None


class TokenUpdateParameters(_serialization.Model):
    """The parameters for updating a token.

    :ivar scope_map_id: The resource ID of the scope map to which the token will be associated
     with.
    :vartype scope_map_id: str
    :ivar status: The status of the token example enabled or disabled. Known values are: "enabled"
     and "disabled".
    :vartype status: str or ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenStatus
    :ivar credentials: The credentials that can be used for authenticating the token.
    :vartype credentials:
     ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenCredentialsProperties
    """

    _attribute_map = {
        "scope_map_id": {"key": "properties.scopeMapId", "type": "str"},
        "status": {"key": "properties.status", "type": "str"},
        "credentials": {"key": "properties.credentials", "type": "TokenCredentialsProperties"},
    }

    def __init__(
        self,
        *,
        scope_map_id: Optional[str] = None,
        status: Optional[Union[str, "_models.TokenStatus"]] = None,
        credentials: Optional["_models.TokenCredentialsProperties"] = None,
        **kwargs: Any
    ) -> None:
        """
        :keyword scope_map_id: The resource ID of the scope map to which the token will be associated
         with.
        :paramtype scope_map_id: str
        :keyword status: The status of the token example enabled or disabled. Known values are:
         "enabled" and "disabled".
        :paramtype status: str or ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenStatus
        :keyword credentials: The credentials that can be used for authenticating the token.
        :paramtype credentials:
         ~azure.mgmt.containerregistry.v2019_05_01_preview.models.TokenCredentialsProperties
        """
        super().__init__(**kwargs)
        self.scope_map_id = scope_map_id
        self.status = status
        self.credentials = credentials
