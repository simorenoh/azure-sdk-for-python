# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from io import BytesIO
from typing import (
    Any, AnyStr, AsyncGenerator, AsyncIterable, cast,
    Dict, IO, Iterable, Optional, Union,
    TYPE_CHECKING,
)

from ._serialize import (
    add_metadata_headers,
    get_access_conditions,
    get_cpk_info,
    get_lease_action_properties,
    get_mod_conditions,
    get_path_http_headers
)
from ._shared.request_handlers import get_length, read_length
from ._shared.response_handlers import return_response_headers
from ._shared.uploads import IterStreamer
from ._shared.uploads_async import AsyncIterStreamer

if TYPE_CHECKING:
    from ._generated.operations import PathOperations
    from ._models import ContentSettings
    from ._shared.models import StorageConfiguration


def _append_data_options(
    data: Union[bytes, str, Iterable[AnyStr], AsyncIterable[AnyStr], IO[AnyStr]],
    offset: int,
    scheme: str,
    length: Optional[int] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    if isinstance(data, str):
        data = data.encode(kwargs.pop('encoding', 'UTF-8'))  # type: ignore
    if length is None:
        length = get_length(data)
        if length is None:
            length, data = read_length(data)
    if isinstance(data, bytes):
        data = data[:length]

    cpk_info = get_cpk_info(scheme, kwargs)
    kwargs.update(get_lease_action_properties(kwargs))

    options = {
        'body': data,
        'position': offset,
        'content_length': length,
        'validate_content': kwargs.pop('validate_content', False),
        'cpk_info': cpk_info,
        'timeout': kwargs.pop('timeout', None),
        'cls': return_response_headers
    }
    options.update(kwargs)
    return options


def _flush_data_options(
    offset: int,
    scheme: str,
    content_settings: Optional["ContentSettings"] = None,
    retain_uncommitted_data: Optional[bool] = False,
    **kwargs
) -> Dict[str, Any]:
    mod_conditions = get_mod_conditions(kwargs)

    path_http_headers = None
    if content_settings:
        path_http_headers = get_path_http_headers(content_settings)

    cpk_info = get_cpk_info(scheme, kwargs)
    kwargs.update(get_lease_action_properties(kwargs))

    options = {
        'position': offset,
        'content_length': 0,
        'path_http_headers': path_http_headers,
        'retain_uncommitted_data': retain_uncommitted_data,
        'close': kwargs.pop('close', False),
        'modified_access_conditions': mod_conditions,
        'cpk_info': cpk_info,
        'timeout': kwargs.pop('timeout', None),
        'cls': return_response_headers
    }
    options.update(kwargs)
    return options


def _upload_options(
    data: Union[bytes, str, Iterable[AnyStr], AsyncIterable[AnyStr], IO[AnyStr]],
    scheme: str,
    config: "StorageConfiguration",
    path: "PathOperations",
    length: Optional[int] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    encoding = kwargs.pop('encoding', 'UTF-8')
    if isinstance(data, str):
        data = data.encode(encoding)
    if length is None:
        length = get_length(data)
    if isinstance(data, bytes):
        data = data[:length]

    stream: Optional[Any] = None
    if isinstance(data, bytes):
        stream = BytesIO(data)
    elif hasattr(data, 'read'):
        stream = data
    elif hasattr(data, '__iter__'):
        stream = IterStreamer(data, encoding=encoding)
    elif hasattr(data, '__aiter__'):
        stream = AsyncIterStreamer(cast(AsyncGenerator, data), encoding=encoding)
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")

    validate_content = kwargs.pop('validate_content', False)
    content_settings = kwargs.pop('content_settings', None)
    metadata = kwargs.pop('metadata', None)
    max_concurrency = kwargs.pop('max_concurrency', 1)

    kwargs['properties'] = add_metadata_headers(metadata)
    kwargs['lease_access_conditions'] = get_access_conditions(kwargs.pop('lease', None))
    kwargs['modified_access_conditions'] = get_mod_conditions(kwargs)
    kwargs['cpk_info'] = get_cpk_info(scheme, kwargs)

    if content_settings:
        kwargs['path_http_headers'] = get_path_http_headers(content_settings)

    kwargs['stream'] = stream
    kwargs['length'] = length
    kwargs['validate_content'] = validate_content
    kwargs['max_concurrency'] = max_concurrency
    kwargs['client'] = path
    kwargs['file_settings'] = config

    return kwargs
