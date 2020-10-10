# Copyright 2019 HUAWEI, Inc. All Rights Reserved.
# Copyright 2017 Red Hat, Inc. All Rights Reserved.
# Modified upon https://github.com/openstack/sushy
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from six.moves import http_client

LOG = logging.getLogger(__name__)


class UfmClientError(Exception):
    """Basic exception for errors"""

    message = None

    def __init__(self, **kwargs):
        if self.message and kwargs:
            self.message = self.message % kwargs

        super(UfmClientError, self).__init__(self.message)


class UfmClientOperationError(UfmClientError):

    def __init__(self, error, **kwargs):
        self.message = error
        super(UfmClientOperationError, self).__init__(**kwargs)


class UfmConnectionError(UfmClientError):
    message = 'Unable to connect to %(url)s. Error: %(error)s'


class ArchiveParsingError(UfmClientError):
    message = 'Failed parsing archive "%(path)s": %(error)s'


class UfmHttpRequestError(UfmClientError):
    """Basic exception for HTTP errors"""

    status_code = None
    """HTTP status code."""

    message = 'HTTP %(method)s %(url)s returned code %(code)s. %(error)s'

    def __init__(self, method, url, response):
        self.status_code = response.status_code
        kwargs = {'url': url,
                  'method': method,
                  'code': self.status_code,
                  'error': response.content}
        LOG.info(('HTTP response for %(method)s %(url)s -> '
                  'status code: %(code)s, error: %(error)s'), kwargs)
        super(UfmHttpRequestError, self).__init__(**kwargs)


class BadRequestError(UfmHttpRequestError):
    pass


class ResourceNotFoundError(UfmHttpRequestError):
    # Overwrite the complex generic message with a simpler one.
    message = 'Resource %(url)s not found'


class ServerSideError(UfmHttpRequestError):
    pass


class AccessError(UfmHttpRequestError):
    pass


def raise_for_response(method, url, response):
    """Raise a correct error class, if needed."""
    if response.status_code < http_client.BAD_REQUEST:
        return
    elif response.status_code == http_client.NOT_FOUND:
        raise ResourceNotFoundError(method, url, response)
    elif response.status_code == http_client.BAD_REQUEST:
        raise BadRequestError(method, url, response)
    elif response.status_code in (http_client.UNAUTHORIZED,
                                  http_client.FORBIDDEN):
        raise AccessError(method, url, response)
    elif response.status_code >= http_client.INTERNAL_SERVER_ERROR:
        raise ServerSideError(method, url, response)
    else:
        raise UfmHttpRequestError(method, url, response)
