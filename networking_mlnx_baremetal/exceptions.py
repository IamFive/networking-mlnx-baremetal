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

from networking_mlnx_baremetal._i18n import _

LOG = logging.getLogger(__name__)


class MlnxIbBmDriverException(Exception):
    """Basic exception"""

    message = None

    def __init__(self, **kwargs):
        if self.message and kwargs:
            self.message = self.message % kwargs

        super(MlnxIbBmDriverException, self).__init__(self.message)


class InvalidConfigValueException(MlnxIbBmDriverException):
    message = _('Invalid value "%(value)s" was set to configuration '
                'option: %(option)s. %(details)s')


class PortBindingException(MlnxIbBmDriverException):
    message = _("Failed to add guids %(guids)s to UFM partition "
                "key %(pkey)s, reason is %(reason)s.")
