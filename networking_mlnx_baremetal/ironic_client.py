# -*- coding: utf-8 -*

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

from ironicclient import client
from keystoneauth1 import loading
from networking_mlnx_baremetal import constants
from networking_mlnx_baremetal._i18n import _
from oslo_config import cfg


CONF = cfg.CONF
KEYSTONE_SESSION = None


IRONIC_OPTS = [
    cfg.StrOpt('os_region',
               help=_('Keystone region used to get Ironic endpoints.')),
    cfg.StrOpt('auth_strategy',
               default='keystone',
               choices=('keystone', 'noauth'),
               help=_('Authentication method: noauth or keystone.')),
    cfg.StrOpt('endpoint',
               default='http://localhost:6385/',
               help=_('Ironic API endpoint, used to connect to Ironic when '
                      'auth_strategy option is noauth to work with standalone '
                      'Ironic without keystone.')),
    cfg.IntOpt('retry_interval',
               default=2,
               help=_('Interval between retries in case of conflict error '
                      '(HTTP 409).')),
    cfg.IntOpt('max_retries',
               default=30,
               help=_('Maximum number of retries in case of conflict error '
                      '(HTTP 409).')),
]

CONF.register_opts(IRONIC_OPTS, group=constants.IRONIC_GROUP_NAME)


def list_opts():
    return [(constants.IRONIC_GROUP_NAME, IRONIC_OPTS +
             loading.get_session_conf_options() +
             loading.get_auth_plugin_conf_options('v3password'))]


def create_keystone_session(group):
    """create new keystone session from conf

    :param group: the conf group name
    :return: keystone session
    """
    loading.register_session_conf_options(CONF, group)
    loading.register_auth_conf_options(CONF, group)
    auth = loading.load_auth_from_conf_options(CONF, group)
    session = loading.load_session_from_conf_options(
        CONF, group, auth=auth)
    return session


def get_client(api_version=constants.DEFAULT_IRONIC_API_VERSION):
    """Create an Ironic client instance.

    :param api_version: ironic api version, default latest.
    :return: an Ironic Client instance
    """
    if CONF.ironic.auth_strategy == 'noauth':
        # To support standalone ironic without keystone
        args = {'token': 'noauth',
                'endpoint': CONF.ironic.endpoint}
    else:
        # To support keystone authentication
        global KEYSTONE_SESSION
        if not KEYSTONE_SESSION:
            KEYSTONE_SESSION = create_keystone_session(
                constants.IRONIC_GROUP_NAME)
        args = {'session': KEYSTONE_SESSION,
                'region_name': CONF.ironic.os_region}

    args['os_ironic_api_version'] = api_version
    args['max_retries'] = CONF.ironic.max_retries
    args['retry_interval'] = CONF.ironic.retry_interval

    # initialize an IronicClient instance
    return client.Client(1, **args)
