# Copyright 2020 HuaWei Technologies. All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import logging

import requests
from requests.auth import HTTPBasicAuth

from networking_mlnx_baremetal.ufmclient import constants
from networking_mlnx_baremetal.ufmclient import exceptions

LOG = logging.getLogger(__name__)

HEAD = 'HEAD'
"""http method HEAD"""

GET = 'GET'
"""http method get"""

POST = 'POST'
"""http method POST"""

PATCH = 'PATCH'
"""http method PATCH"""

PUT = 'PUT'
"""http method PUT"""

DELETE = 'DELETE'


class UfmSession(object):
    """UFM REST API session"""

    # Default timeout in seconds for requests connect and read
    # http://docs.python-requests.org/en/master/user/advanced/#timeouts
    _DEFAULT_TIMEOUT = 60

    def __init__(self, endpoint, username, password, verify_ca, timeout=None):
        self.endpoint = endpoint
        self.base_url = '%s/ufmRest' % endpoint
        self._timeout = timeout if timeout else self._DEFAULT_TIMEOUT

        # Initial request session
        self._session = requests.Session()
        self._session.verify = verify_ca
        self._session.auth = HTTPBasicAuth(username, password)

        from networking_mlnx_baremetal import __version__ as version
        self._session.headers.update({
            'User-Agent': 'python-ufmclient - v%s' % version
        })

    def get_url(self, path):
        """get absolute URL for UFM REST API resource

        :param path: path of resource, can be relative path or absolute path
        :return:
        """
        if path.startswith(self.base_url):
            return path
        elif path.startswith('/ufmRest'):
            return '%s%s' % (self.endpoint, path)
        else:
            return '%s%s' % (self.base_url, path)

    def get(self, url, headers=None):
        return self.request(GET, url, headers=headers)

    def post(self, url, payload, headers=None):
        return self.request(POST, url, json=payload, headers=headers)

    def put(self, url, payload, headers=None):
        return self.request(PUT, url, json=payload, headers=headers)

    def patch(self, url, payload, headers=None):
        return self.request(PATCH, url, json=payload, headers=headers)

    def delete(self, url, headers=None):
        return self.request(DELETE, url, headers=headers)

    def request(self, method, url, json=None, headers=None):
        try:
            url = self.get_url(url)
            return self._request(method, url, json=json, headers=headers)
        except requests.exceptions.RequestException as e:
            response = e.response
            if response is not None:
                LOG.warning('UFM responses -> %(method)s %(url)s, '
                            'code: %(code)s, response: %(resp_txt)s',
                            {'method': method, 'url': url,
                             'code': response.status_code,
                             'resp_txt': response.content})
                raise exceptions.raise_for_response(method, url, response)
            else:
                raise exceptions.UfmConnectionError(url=url, error=e)

    def _request(self, method, url, json=None, headers=None):
        if method.upper() in [constants.POST, constants.PATCH, constants.PUT]:
            headers = headers or {}
            headers.update({constants.HEADER_CONTENT_TYPE: 'application/json'})

        req = requests.Request(method, url, json=json, headers=headers)
        prepped_req = self._session.prepare_request(req)
        res = self._session.send(prepped_req, timeout=self._timeout)
        res.raise_for_status()
        LOG.debug('UFM responses -> %(method)s %(url)s, code: %(code)s, '
                  'content:: %(content)s',
                  {'method': method, 'url': url, 'code': res.status_code,
                   'content': res.text})
        return res
