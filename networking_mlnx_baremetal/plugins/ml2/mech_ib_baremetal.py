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
import copy

from ironicclient.common.apiclient import exceptions as ironic_exc
from neutron.db import provisioning_blocks
from neutron_lib import constants as n_const
from neutron_lib.api.definitions import portbindings
from neutron_lib.callbacks import resources
from neutron_lib.plugins.ml2 import api
from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils

from networking_mlnx_baremetal import constants as const
from networking_mlnx_baremetal import exceptions
from networking_mlnx_baremetal import ironic_client
from networking_mlnx_baremetal import ufm_client
from networking_mlnx_baremetal import utils
from networking_mlnx_baremetal._i18n import _
from networking_mlnx_baremetal.plugins.ml2 import config
from networking_mlnx_baremetal.ufmclient import exceptions as ufm_exc
from networking_mlnx_baremetal.ufmclient import utils as ufm_utils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)
config.register_opts(CONF)

MLNX_IB_BAREMETAL_ENTITY = 'MLNX-IB-Baremetal'

BF_ENABLE_SRIOV = 'enable_sriov'
BF_DFT_LIMITED_PKEYS = 'default_limited_pkeys'
BF_PHYSICAL_GUIDS = 'physical_guids'
BF_VIRTUAL_GUIDS = 'virtual_guids'
BF_DYNAMIC_PKEY = 'dynamic_pkey'


class InfiniBandBaremetalMechanismDriver(api.MechanismDriver):
    """OpenStack neutron ml2 mechanism driver for mellanox infini-band PKey
    configuration when provisioning baremetal using Ironic.
    """

    def initialize(self):
        """Perform driver initialization.

        Called after all drivers have been loaded and the database has
        been initialized. No abstract methods defined below will be
        called prior to this method being called.
        """
        self.ironic_client = ironic_client.get_client()
        self.ufm_client = ufm_client.get_client()
        self.conf = CONF[const.MLNX_BAREMETAL_DRIVER_GROUP_NAME]
        self.allowed_network_types = const.SUPPORTED_NETWORK_TYPES
        self.allowed_physical_networks = self.conf.physical_networks

    def create_network_precommit(self, context):
        """Allocate resources for a new network.

        :param context: NetworkContext instance describing the new
            network.

        Create a new network, allocating resources as necessary in the
        database. Called inside transaction context on session. Call
        cannot block.  Raising an exception will result in a rollback
        of the current transaction.
        """
        pass

    def create_network_postcommit(self, context):
        """Create a network.

        :param context: NetworkContext instance describing the new
            network.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.
        """
        pass

    def update_network_precommit(self, context):
        """Update resources of a network.

        :param context: NetworkContext instance describing the new
             state of the network, as well as the original state prior
             to the update_network call.

        Update values of a network, updating the associated resources
        in the database. Called inside transaction context on session.
        Raising an exception will result in rollback of the
        transaction.

        update_network_precommit is called for all changes to the
        network state. It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        pass

    def update_network_postcommit(self, context):
        """Update a network.

        :param context: NetworkContext instance describing the new
            state of the network, as well as the original state prior
            to the update_network call.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.

        update_network_postcommit is called for all changes to the
        network state.  It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        pass

    def delete_network_precommit(self, context):
        """Delete resources for a network.

        :param context: NetworkContext instance describing the current
            state of the network, prior to the call to delete it.

        Delete network resources previously allocated by this
        mechanism driver for a network. Called inside transaction
        context on session. Runtime errors are not expected, but
        raising an exception will result in rollback of the
        transaction.
        """
        pass

    def delete_network_postcommit(self, context):
        """Delete a network.

        :param context: NetworkContext instance describing the current
            state of the network, prior to the call to delete it.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Runtime errors are not
        expected, and will not prevent the resource from being
        deleted.
        """
        # TODO(qianbiao.ng): if an UFM partition has no guid, it will be auto
        #  deleted. So, if port unbound logic is stable (remove guid when
        #  unbound), we may ignore delete_network_postcommit callback?
        for segment in context.network_segments:
            if self._is_segment_supported(segment):
                segmentation_id = segment.get(api.SEGMENTATION_ID)
                pkey = hex(segmentation_id)
                try:
                    self.ufm_client.pkey.delete(pkey)
                except ufm_exc.ResourceNotFoundError:
                    # NOTE(turnbig): ignore 404 exception, because of that the
                    #  UFM partition key may have not been setup at this point.
                    LOG.info(_("UFM partition key %(pkey)s does not exists, "
                               "could not be deleted."),
                             {'pkey': pkey})
                except ufm_exc.UfmClientError as e:
                    LOG.error(_("Failed to delete UFM partition key %(pkey)s, "
                                "reason is %(reason)s."),
                              {'pkey': pkey, 'reason': e})
                    raise

    def create_subnet_precommit(self, context):
        """Allocate resources for a new subnet.

        :param context: SubnetContext instance describing the new
            subnet.

        rt = context.current
        device_id = port['device_id']
        device_owner = port['device_owner']
        Create a new subnet, allocating resources as necessary in the
        database. Called inside transaction context on session. Call
        cannot block.  Raising an exception will result in a rollback
        of the current transaction.
        """
        pass

    def create_subnet_postcommit(self, context):
        """Create a subnet.

        :param context: SubnetContext instance describing the new
            subnet.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.
        """
        pass

    def update_subnet_precommit(self, context):
        """Update resources of a subnet.

        :param context: SubnetContext instance describing the new
            state of the subnet, as well as the original state prior
            to the update_subnet call.

        Update values of a subnet, updating the associated resources
        in the database. Called inside transaction context on session.
        Raising an exception will result in rollback of the
        transaction.

        update_subnet_precommit is called for all changes to the
        subnet state. It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        pass

    def update_subnet_postcommit(self, context):
        """Update a subnet.

        :param context: SubnetContext instance describing the new
            state of the subnet, as well as the original state prior
            to the update_subnet call.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.

        update_subnet_postcommit is called for all changes to the
        subnet state.  It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        pass

    def delete_subnet_precommit(self, context):
        """Delete resources for a subnet.

        :param context: SubnetContext instance describing the current
            state of the subnet, prior to the call to delete it.

        Delete subnet resources previously allocated by this
        mechanism driver for a subnet. Called inside transaction
        context on session. Runtime errors are not expected, but
        raising an exception will result in rollback of the
        transaction.
        """
        pass

    def delete_subnet_postcommit(self, context):
        """Delete a subnet.

        :param context: SubnetContext instance describing the current
            state of the subnet, prior to the call to delete it.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Runtime errors are not
        expected, and will not prevent the resource from being
        deleted.
        """
        pass

    def create_port_precommit(self, context):
        """Allocate resources for a new port.

        :param context: PortContext instance describing the port.

        Create a new port, allocating resources as necessary in the
        database. Called inside transaction context on session. Call
        cannot block.  Raising an exception will result in a rollback
        of the current transaction.
        """
        pass

    def create_port_postcommit(self, context):
        """Create a port.

        :param context: PortContext instance describing the port.

        Called after the transaction completes. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance.  Raising an exception will
        result in the deletion of the resource.
        """
        pass

    def update_port_precommit(self, context):
        """Update resources of a port.

        :param context: PortContext instance describing the new
            state of the port, as well as the original state prior
            to the update_port call.

        Called inside transaction context on session to complete a
        port update as defined by this mechanism driver. Raising an
        exception will result in rollback of the transaction.

        update_port_precommit is called for all changes to the port
        state. It is up to the mechanism driver to ignore state or
        state changes that it does not know or care about.
        """
        pass

    def update_port_postcommit(self, context):
        # type: (api.PortContext) -> None
        """Update a port.

        :param context: PortContext instance describing the new
            state of the port, as well as the original state prior
            to the update_port call.

        Called after the transaction completes. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance.  Raising an exception will
        result in the deletion of the resource.

        update_port_postcommit is called for all changes to the port
        state. It is up to the mechanism driver to ignore state or
        state changes that it does not know or care about.
        """
        port = context.current
        original_port = context.original

        if not self._is_baremetal_port(port):
            LOG.info(_('Port is not a baremetal port, '
                       'skip update_port_postcommit callback.'))
            return

        if not self._is_port_bound(context):
            LOG.info(_('Port is not bound by current driver, '
                       'skip update_port_postcommit callback.'))
            return

        binding_level = self._get_binding_level(context)
        LOG.info(_('Port is bound by current driver with binding '
                   'level %(binding_level)s.'),
                 {'binding_level': binding_level})

        current_vif_type = context.vif_type
        original_vif_type = context.original_vif_type

        # when port is unbound, unbind relevant guids from IB partition.
        if (current_vif_type == portbindings.VIF_TYPE_UNBOUND
                and original_vif_type not in const.UNBOUND_VIF_TYPES):
            LOG.info(_("Port's VIF type changed from bound to unbound"))
            LOG.info(_("Remove infiniband guids from partition key now."))

            # binding:host_id has been clear in current port
            node_uuid = original_port.get(portbindings.HOST_ID)
            node_ib_ports = self._get_ironic_ib_ports(node_uuid)
            if not node_ib_ports or len(node_ib_ports) == 0:
                LOG.error(_(
                    'For current port(%(port)s), could not find any '
                    'infiniband port presents in the same ironic '
                    'node(%(node_uuid)s), could not remove guids from '
                    'partition key.'),
                    {port: port, 'node_uuid': node_uuid})
                return

            node_ib_client_ids = [ib_port.extra.get('client-id')
                                  for ib_port in node_ib_ports
                                  if ib_port.extra.get('client-id')]
            node_ib_guids = [ufm_utils.mlnx_ib_client_id_to_guid(client_id)
                             for client_id in node_ib_client_ids]
            if len(node_ib_guids) == 0:
                LOG.error(_(
                    'For current port(%(port)s), could not find any '
                    'infiniband port presents in the same ironic '
                    'node(%(node_uuid)s), could not remove guids from '
                    'partition key.'),
                    {port: port, 'node_uuid': node_uuid})
                return

            # step1: remove physical guids from dynamic pkeys
            segmentation_id = binding_level.get(api.SEGMENTATION_ID)
            LOG.info(_('To be unbound dynamic pkey %(pkey)s, '
                       'physical guids %(guids)s.'),
                     {'guids': node_ib_guids,
                      'pkey': hex(segmentation_id)})
            self.ufm_client.pkey.remove_guids(hex(segmentation_id),
                                              node_ib_guids)
            LOG.info(_('Infiniband port physical guids %(guids)s has been '
                       'removed from pkey %(pkey)s.'),
                     {'guids': node_ib_guids,
                      'pkey': hex(segmentation_id)})

            # step2: unbound default limited pkeys
            # self.unbind_default_limited_pkeys(port, node_ib_guids)
            if self.conf.default_limited_pkeys:
                sriov_enabled = self.conf.enable_sriov
                if sriov_enabled:
                    LOG.info(_('SR-IOV is enabled, remove virtual guids '
                               'from default limited pkeys now.'))
                    vf_count = len(self.conf.default_limited_pkeys)
                    virtual_guids = [
                        list(utils.generate_virtual_guids(client_id,
                                                          count=vf_count))
                        for client_id in node_ib_client_ids]
                    grouped_guids = dict(zip(self.conf.default_limited_pkeys,
                                             zip(*virtual_guids)))
                    LOG.info(_('Virtual guids for default limited pkeys is '
                               '%(grouped_guids)s .'),
                             {'grouped_guids': grouped_guids})
                    for pkey, vf_guids in grouped_guids.iteritems():
                        self.ufm_client.pkey.remove_guids(pkey, vf_guids)
                        LOG.info(_('Successfully remove IB virtual guids '
                                   '%(guids)s from limited pkey %(pkey)s.'),
                                 {'guids': vf_guids, 'pkey': pkey})
                else:
                    for pkey in self.conf.default_limited_pkeys:
                        self.ufm_client.pkey.remove_guids(pkey, node_ib_guids)
                        LOG.info(_('Successfully remove IB physical guids '
                                   '%(guids)s from limited pkey %(pkey)s.'),
                                 {'guids': node_ib_guids, 'pkey': pkey})

        # when port is bound, mark port as provision completed.
        if (current_vif_type not in const.UNBOUND_VIF_TYPES
                and original_vif_type in const.UNBOUND_VIF_TYPES):
            LOG.info(_("Port's VIF type changed from unbound to bound."))
            # NOTE(qianbiao.ng): this provisioning_complete action maps to
            #  provisioning_blocks.add_provisioning_component called in
            #  bind_port process.
            provisioning_blocks.provisioning_complete(
                context._plugin_context, port['id'], resources.PORT,
                MLNX_IB_BAREMETAL_ENTITY)

        # when port binding fails, raise exception
        if (port.get('status') == n_const.PORT_STATUS_ERROR
                and current_vif_type == portbindings.VIF_TYPE_BINDING_FAILED):
            LOG.info(_("Port binding failed, Port's VIF details: "
                       "%(vif_details)s."),
                     {'vif_details': context.vif_details})
            if context.vif_details.get('driver') == const.DRIVE_NAME:
                LOG.info(_("Port binding failure is caused by current driver. "
                           "Raise an exception to abort port update "
                           "process."))
                raise exceptions.PortBindingException(**context.vif_details)

    def unbind_default_limited_pkeys(self, port, node_ib_guids):
        """unbind virtual guids from default limited pkeys

        NOTE(qianbiao.ng): port can not be updated when node is locked, so,
        binding profile can not be set when binding port (node is locked).
        This solution is deprecated for now.

        :param port:
        :param node_ib_guids:
        :return:
        """
        mac_address = port.get('mac_address')
        eth_port = self._get_ironic_port_by_mac(mac_address)
        binding_profile = eth_port.extra or {}
        default_limited_pkeys = binding_profile.get(BF_DFT_LIMITED_PKEYS)
        if default_limited_pkeys:
            sriov_enabled = binding_profile.get(BF_ENABLE_SRIOV)
            if sriov_enabled:
                LOG.info(_('SR-IOV is enabled, remove virtual guids '
                           'from default limited pkeys now.'))
                virtual_guids = binding_profile.get(BF_VIRTUAL_GUIDS)
                grouped_guids = dict(zip(default_limited_pkeys,
                                         virtual_guids))
                LOG.info(_('Virtual guids for default limited pkeys is '
                           '%(grouped_guids)s .'),
                         {'grouped_guids': grouped_guids})
                for pkey, vf_guids in grouped_guids.iteritems():
                    self.ufm_client.pkey.remove_guids(pkey, vf_guids)
                    LOG.info(_('Successfully remove IB virtual guids '
                               '%(guids)s from limited pkey %(pkey)s.'),
                             {'guids': vf_guids, 'pkey': pkey})
            else:
                for pkey in default_limited_pkeys:
                    self.ufm_client.pkey.remove_guids(pkey, node_ib_guids)
                    LOG.info(_('Successfully remove IB physical guids '
                               '%(guids)s from limited pkey %(pkey)s.'),
                             {'guids': node_ib_guids, 'pkey': pkey})

            # restore Ironic PXE port extra
            mac_address = port.get('mac_address')
            self.remove_ironic_port_extra(mac_address)

    def delete_port_precommit(self, context):
        """Delete resources of a port.

        :param context: PortContext instance describing the current
            state of the port, prior to the call to delete it.

        Called inside transaction context on session. Runtime errors
        are not expected, but raising an exception will result in
        rollback of the transaction.
        """
        pass

    def delete_port_postcommit(self, context):
        """Delete a port.

        :param context: PortContext instance describing the current
            state of the port, prior to the call to delete it.

        Called after the transaction completes. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance.  Runtime errors are not
        expected, and will not prevent the resource from being
        deleted.
        """
        # NOTE(turnbig): it's impossible to get relevant infiniband ports
        #  here, the relevant Ironic Node(binding:host_id) has been clear
        #  before deleted.
        pass

    def bind_port(self, context):
        """Attempt to bind a port.

        :param context: PortContext instance describing the port

        This method is called outside any transaction to attempt to
        establish a port binding using this mechanism driver. Bindings
        may be created at each of multiple levels of a hierarchical
        network, and are established from the top level downward. At
        each level, the mechanism driver determines whether it can
        bind to any of the network segments in the
        context.segments_to_bind property, based on the value of the
        context.host property, any relevant port or network
        attributes, and its own knowledge of the network topology. At
        the top level, context.segments_to_bind contains the static
        segments of the port's network. At each lower level of
        binding, it contains static or dynamic segments supplied by
        the driver that bound at the level above. If the driver is
        able to complete the binding of the port to any segment in
        context.segments_to_bind, it must call context.set_binding
        with the binding details. If it can partially bind the port,
        it must call context.continue_binding with the network
        segments to be used to bind at the next lower level.

        If the binding results are committed after bind_port returns,
        they will be seen by all mechanism drivers as
        update_port_precommit and update_port_postcommit calls. But if
        some other thread or process concurrently binds or updates the
        port, these binding results will not be committed, and
        update_port_precommit and update_port_postcommit will not be
        called on the mechanism drivers with these results. Because
        binding results can be discarded rather than committed,
        drivers should avoid making persistent state changes in
        bind_port, or else must ensure that such state changes are
        eventually cleaned up.

        Implementing this method explicitly declares the mechanism
        driver as having the intention to bind ports. This is inspected
        by the QoS service to identify the available QoS rules you
        can use with ports.
        """

        port = context.current
        is_baremetal_port = self._is_baremetal_port(port)
        if not is_baremetal_port:
            LOG.info(_('Port is not a baremetal port, skip binding.'))
            return

        # NOTE(turnbig): it seems ml2 driver will auto check whether a
        #  driver has been bound by a driver through binding_levels
        # has_port_bound = self._is_port_bound(port)
        # if has_port_bound:
        #     LOG.info(_('Port has been bound by this driver, skip binding.'))
        #     return

        # try to bind segment now
        LOG.info(_('Port is supported, will try binding IB partition now.'))
        for segment in context.segments_to_bind:
            if self._is_segment_supported(segment):
                node_uuid = port.get(portbindings.HOST_ID)
                node_ib_ports = self._get_ironic_ib_ports(node_uuid)
                if not node_ib_ports or len(node_ib_ports) == 0:
                    LOG.warning(_(
                        'For current port(%(port)s), could not find any IB '
                        'port presents in the same ironic '
                        'node(%(node_uuid)s), break bind port process now.'),
                        {port: port, 'node_uuid': node_uuid})
                    return

                node_ib_client_ids = [ib_port.extra.get('client-id')
                                      for ib_port in node_ib_ports
                                      if ib_port.extra.get('client-id')]
                node_ib_guids = [ufm_utils.mlnx_ib_client_id_to_guid(client_id)
                                 for client_id in node_ib_client_ids]
                LOG.info(_('Ironic node infiniband port guids: %s.')
                         % node_ib_guids)

                LOG.debug(_('Try to bind IB ports using segment: %s'), segment)
                # update partition key for relevant guids
                segment_id = segment[api.ID]
                segmentation_id = segment[api.SEGMENTATION_ID]

                try:
                    provisioning_blocks.add_provisioning_component(
                        context._plugin_context, port['id'], resources.PORT,
                        MLNX_IB_BAREMETAL_ENTITY)

                    # step1: bind PF guids to dynamic pkey
                    self.ufm_client.pkey.add_guids(hex(segmentation_id),
                                                   guids=node_ib_guids,
                                                   index0=True)
                    LOG.info(_('Successfully bound IB physical guids '
                               '%(guids)s to dynamic partition %(pkey)s.'),
                             {'guids': node_ib_guids,
                              'pkey': hex(segmentation_id)})

                    # step2: if there are default limited pkeys to bound,
                    binding_profile = self.bind_default_limited_pkeys(
                        node_ib_client_ids)
                    binding_profile[BF_DYNAMIC_PKEY] = segmentation_id
                    binding_profile[BF_PHYSICAL_GUIDS] = node_ib_guids
                    LOG.info(_("Mellanox infiniband port binding profile: "
                               "%(profile)s."),
                             {'profile': binding_profile})

                    # NOTE(turnbig): node is locked when deploying, and port
                    # can not be updated when node is locked
                    # mac_address = port.get('mac_address')
                    # self.append_ironic_port_extra(mac_address,
                    #                               binding_profile)

                    # NOTE(turnbig): setting VIF details has no effect here.
                    # details = {
                    #     const.MLNX_EXTRA_NS: {
                    #         'guids': node_ib_guids,
                    #         'pkey': segmentation_id,
                    #     }
                    # }
                    # LOG.info(_('Update bound IB port vif info: '
                    #            '%(vif_details)s.'),
                    #          {'vif_details': details})
                    context._binding.vif_details = jsonutils.dumps(
                        binding_profile)

                    # NOTE(turnbig): chain current segment again to next driver
                    new_segment = copy.deepcopy(segment)
                    context.continue_binding(segment_id, [new_segment])
                    return
                except ufm_exc.UfmClientError as e:
                    LOG.error(_("Failed to add guids %(guids)s to UFM "
                                "partition key %(pkey)s, "
                                "reason is %(reason)s."),
                              {'guids': node_ib_client_ids,
                               'pkey': hex(segmentation_id),
                               'reason': str(e)})

                    # TODO(qianbiao.ng): if IB partition binding fails,
                    #   we should abort the bind_port process and exit.
                    vif_details = {'guids': node_ib_client_ids,
                                   'pkey': hex(segmentation_id),
                                   'driver': const.DRIVE_NAME,
                                   'reason': str(e)}
                    context.set_binding(segment[api.ID],
                                        portbindings.VIF_TYPE_BINDING_FAILED,
                                        vif_details,
                                        status=n_const.PORT_STATUS_ERROR)

    def bind_default_limited_pkeys(self, node_ib_client_ids):
        """Binding guids to default limited pkeys, if SR-IOV is enable,
        will auto generate virtual GUID from source physical GUID.

        :param node_ib_client_ids:  source physical infiniband client-id list
        :return: binding profiles of those default limited pkeys
        """
        if not self.conf.default_limited_pkeys:
            LOG.info(_('No default limited pkeys is configured.'))
            return

        LOG.info(_('Default limited pkeys %(pkeys)s is configured.'),
                 {'pkeys': self.conf.default_limited_pkeys})
        binding_profile = {
            BF_ENABLE_SRIOV: self.conf.enable_sriov,
            BF_DFT_LIMITED_PKEYS: self.conf.default_limited_pkeys
        }

        if self.conf.enable_sriov:
            LOG.info(_('SR-IOV is enabled, will generate virtual guids for '
                       'default limited pkeys.'))
            vf_count = len(self.conf.default_limited_pkeys)
            virtual_guids = [
                list(utils.generate_virtual_guids(client_id, count=vf_count))
                for client_id in node_ib_client_ids]
            grouped_guids = dict(zip(self.conf.default_limited_pkeys,
                                     zip(*virtual_guids)))
            LOG.info(_('Virtual guids for default limited pkeys is '
                       '%(grouped_guids)s .'),
                     {'grouped_guids': grouped_guids})
            for pkey, vf_guids in grouped_guids.iteritems():
                self.ufm_client.pkey.add_guids(pkey, guids=vf_guids,
                                               index0=True,
                                               full_membership=False)
                LOG.info(_('Successfully bound IB virtual guids %(guids)s to '
                           'limited pkey %(pkey)s.'),
                         {'guids': vf_guids, 'pkey': pkey})

            binding_profile[BF_VIRTUAL_GUIDS] = zip(*virtual_guids)
        else:
            guids = [ufm_utils.mlnx_ib_client_id_to_guid(client_id)
                     for client_id in node_ib_client_ids]
            for pkey in self.conf.default_limited_pkeys:
                self.ufm_client.pkey.add_guids(pkey, guids=guids,
                                               index0=False,
                                               full_membership=False)
                LOG.info(_('Successfully bound IB physical guids %(guids)s to '
                           'limited pkey %(pkey)s with option index0 False.'),
                         {'guids': guids, 'pkey': pkey})

        return binding_profile

    @staticmethod
    def _is_baremetal_port(port):
        """Return whether a port's VNIC_TYPE is baremetal.

        Ports supported by this driver must have VNIC type 'baremetal'.

        :param port: The port to check
        :returns: true if the port's VNIC_TYPE is baremetal
        """
        vnic_type = port[portbindings.VNIC_TYPE]
        return vnic_type == portbindings.VNIC_BAREMETAL

    @staticmethod
    def _is_network_supported(self, network):
        """Return whether a network is supported by this driver.

        :param network: The network(
            :class: openstack.network.v2.network.Network) instance to check
        :returns: true if network is supported else false
        """
        _this = InfiniBandBaremetalMechanismDriver
        LOG.debug("Checking whether network is supported: %(network)s.",
                  {'network': network})

        network_id = network.get('id')
        network_type = network.get('provider_network_type')
        segmentation_id = network.get('provider_segmentation_id')
        physical_network = network.get('provider_physical_network')

        if network_type not in self.allowed_network_types:
            LOG.debug(_(
                'Network %(network_id)s with segmentation-id '
                '%(segmentation_id)s has network type %(network_type)s '
                'but mlnx_ib_bm mechanism driver only '
                'support %(allowed_network_types)s.'),
                {'network_id': network_id,
                 'segmentation_id': segmentation_id,
                 'network_type': network_type,
                 'allowed_network_types': self.allowed_network_types})
            return False

        if not segmentation_id:
            LOG.debug(_(
                'Network %(network_id)s with segment %(id)s does not has a '
                'segmentation id, mlnx_ib_bm requires a segmentation id to '
                'create UFM partition.'),
                {'network_id': network_id, 'id': segmentation_id})
            return False

        if not self._is_physical_network_matches(physical_network):
            LOG.debug(_(
                'Network %(network_id)s with segment %(id)s is connected '
                'to physical network %(physnet)s, but mlnx_ib_bm mechanism '
                'driver was pre-configured to watch on physical networks '
                '%(allowed_physical_networks)s.'),
                {'network_id': network_id,
                 'id': segmentation_id,
                 'physnet': physical_network,
                 'allowed_physical_networks': self.allowed_physical_networks})
            return False

        return True

    def _is_segment_supported(self, segment):
        """Return whether a network segment is supported by this driver. A
        segment dictionary looks like:

        {
            "network_id": "9425b757-339d-4954-a17b-dbb3f7061006",
            "segmentation_id": 15998,
            "physical_network": null,
            "id": "3a0946cc-1f61-4211-8a33-b8e2b0b7a2a0",
            "network_type": "vxlan"
        },

        Segment supported by this driver must:
         - have network type 'vxlan' or 'vlan'.
         - have physical networks in pre-configured physical-networks
         - have a segmentation_id

        :param segment: indicates the segment to check
        :returns: true if segment is supported else false
        """
        LOG.debug("Checking whether segment is supported: %(segment)s ",
                  {'segment': segment})

        segment_id = segment[api.ID]
        network_id = segment[api.NETWORK_ID]
        network_type = segment[api.NETWORK_TYPE]
        segmentation_id = segment[api.SEGMENTATION_ID]
        physical_network = segment[api.PHYSICAL_NETWORK]

        if network_type not in self.allowed_network_types:
            LOG.debug(_(
                'Network %(network_id)s with segment %(id)s has '
                'network type %(network_type)s but mlnx_ib_bm mechanism '
                'driver only support %(allowed_network_types)s.'),
                {'network_id': network_id,
                 'id': segment_id,
                 'network_type': network_type,
                 'allowed_network_types': self.allowed_network_types})
            return False

        if not segmentation_id:
            LOG.debug(_(
                'Network %(network_id)s with segment %(id)s does not has a '
                'segmentation id, mlnx_ib_bm requires a segmentation id to '
                'create UFM partition.'),
                {'network_id': network_id, 'id': segment_id})
            return False

        if not self._is_physical_network_matches(physical_network):
            LOG.debug(_(
                'Network %(network_id)s with segment %(id)s is connected '
                'to physical network %(physnet)s, but mlnx_ib_bm mechanism '
                'driver was pre-configured to watch on physical networks '
                '%(allowed_physical_networks)s.'),
                {'network_id': network_id,
                 'id': segment_id,
                 'physnet': physical_network,
                 'allowed_physical_networks': self.allowed_physical_networks})
            return False

        return True

    def _is_physical_network_matches(self, physical_network):
        """Return whether the physical network matches the pre-configured
        physical-networks of this driver. pre-configured physical-network '*'
        means matches anything include none.

        :param physical_network: the physical network to check
        :return: true if match else false
        """
        if (const.PHYSICAL_NETWORK_ANY in self.allowed_physical_networks
                or physical_network in self.allowed_physical_networks):
            return True
        return False

    @staticmethod
    def _is_port_supported(port_context):
        # type: (api.PortContext) -> bool
        """NOTE(turnbig): deprecated, Return whether a port binding is
        supported by this driver

        Ports supported by this driver must:
         - have VNIC type 'baremetal'.
         - have physical networks in pre-configured physical-networks
         - have
         - others maybe? (like Huawei-ml2-driver use prefix)

        :param port_context: The port-context to check
        :returns: true if supported else false
        """
        # TODO(qianbiao.ng): add same strategy like huawei ml2 driver do later.
        network = port_context.network.current
        physical_network = network.provider_physical_network
        this = InfiniBandBaremetalMechanismDriver
        return (this._is_baremetal_port(port_context)
                and this._is_network_type_supported(network)
                and this._is_physical_network_matches(physical_network))

    @staticmethod
    def _is_port_bound(port_context):
        # type: (api.PortContext) -> bool
        """Return whether a port has been bound by this driver.

        Ports bound by this driver have their binding:levels contains a level
        generated by this driver and the segment of that level is in the
        network segments of this port.

        NOTE(turnbig): this driver does not has a realistic neutron port
         connected to an infiniband port, the port here is a baremetal PXE
         ethernet port in the same Ironic node which owns the realistic
         infiniband ports.

        :param port_context: The PortContext to check
        :returns: true if port has been bound by this driver else false
        """
        this = InfiniBandBaremetalMechanismDriver
        port_id = port_context.current.get('id')

        binding_level = this._get_binding_level(port_context)
        if binding_level:
            segmentation_id = binding_level.get(api.SEGMENTATION_ID)
            LOG.info("Port %(port_id)s has been bound to segmentation "
                     "%(segmentation_id)s by driver %(driver)s",
                     {"port_id": port_id,
                      "segmentation_id": segmentation_id,
                      "driver": const.DRIVE_NAME})
            return True

        LOG.info("Port %(port_id)s is not bound to any known segmentation "
                 "of its network by driver %(driver)s",
                 {"port_id": port_id,
                  "driver": const.DRIVE_NAME})
        return False

    @staticmethod
    def _get_binding_level(port_context):
        # type: (api.PortContext) -> dict
        """Return the binding level relevant to this driver.

        Ports bound by this driver have their binding:levels contains a level
        generated by this driver and the segment of that level is in the
        network segments of this port.

        NOTE(turnbig): this driver does not has a realistic neutron port
         connected to an infiniband port, the port here is a baremetal PXE
         ethernet port in the same Ironic node which owns the realistic
         infiniband ports.

        :param port_context: The PortContext to check
        :returns: binding level if port has been bound by this driver else None
        """
        network_segments = port_context.network.network_segments
        network_segment_id_list = {s.get(api.SEGMENTATION_ID)
                                   for s in network_segments}

        # NOTE(qianbiao.ng): It's impossible to get binding_levels from
        # PortContext.binding_levels in this place (only in bind_port
        # callback). But, binding_levels is passed as a property in port
        # dictionary. Remember this binding_levels property has different
        # data structure from PortContext.binding_levels.
        """binding_levels property examples:
            [
                {
                    "physical_network": "",
                    "driver": "mlnx_ib_bm",
                    "network_type": "vxlan",
                    "segmentation_id": 15998,
                    "level": 0
                },
                ....
            ]
        """
        binding_levels = port_context.current.get('binding_levels', [])
        LOG.info("Get binding_level of current driver from "
                 "network segments: %(segments)s, "
                 "binding levels: %(binding_levels)s.",
                 {'segments': network_segments,
                  'binding_levels': binding_levels})
        for level in binding_levels:
            bound_driver = level.get('driver')
            segmentation_id = level.get(api.SEGMENTATION_ID)
            if (bound_driver == const.DRIVE_NAME and
                    segmentation_id in network_segment_id_list):
                return level

        return None

    def _get_ironic_ib_ports(self, node):
        """Get infiniband port list of an Ironic node.

        :param node: indicates the uuid of ironic node
        :return: infiniband port instance list present in this node
        """
        node_ports = self._get_ironic_ports(node)
        node_ib_ports = [node_port
                         for node_port in node_ports
                         if node_port.extra.get('client-id')]
        return node_ib_ports

    def _get_ironic_ports(self, node_uuid):
        """Get all ports of an Ironic node.

        :param node_uuid: indicates the uuid of ironic node
        :return: ironic port instance list
        """
        try:
            node_ports = self.ironic_client.port.list(node=node_uuid,
                                                      detail=True)
            return node_ports
        except ironic_exc.UnsupportedVersion:
            LOG.exception(
                "Failed to get ironic port list, Ironic Client is "
                "using unsupported version of the API.")
            raise
        except (ironic_exc.AuthPluginOptionsMissing,
                ironic_exc.AuthSystemNotFound):
            LOG.exception("Failed to get ironic port list due to Ironic "
                          "Client authentication failure.")
            raise
        except Exception:
            LOG.exception("Failed to get ironic port list.")
            raise

    def _get_ironic_port_by_mac(self, mac_address):
        """Get ironic port by mac address

        :param mac_address: indicates the MAC address of port
        :return: ironic port instance
        """
        try:
            node_port = self.ironic_client.port.get_by_address(mac_address)
            return node_port
        except ironic_exc.UnsupportedVersion:
            LOG.exception(
                "Failed to get ironic port by mac address, Ironic Client is "
                "using unsupported version of the API.")
            raise
        except (ironic_exc.AuthPluginOptionsMissing,
                ironic_exc.AuthSystemNotFound):
            LOG.exception("Failed to get ironic port list due to Ironic "
                          "Client authentication failure.")
            raise
        except Exception:
            LOG.exception(
                "Failed to get ironic port has MAC address: " + mac_address)
            raise

    def append_ironic_port_extra(self, mac_address, to_append):
        """append data to ironic port's extra field

        :param mac_address: indicates the MAC address of the port to be updated
        :param to_append:   to append dictionary data for extra field
        """
        ironic_port = self._get_ironic_port_by_mac(mac_address)
        original_extra = ironic_port.extra
        original_extra.update(to_append)
        patch = [{'op': 'replace',
                  'value': original_extra,
                  'path': '/extra'}]
        self.ironic_client.port.update(ironic_port.uuid, patch)

    def remove_ironic_port_extra(self, mac_address):
        """remove ironic port's extra field

        :param mac_address: indicates the MAC address of the port to be updated
        """
        ironic_port = self._get_ironic_port_by_mac(mac_address)
        patch = [{'op': 'remove',
                  'path': '/extra'}]
        self.ironic_client.port.update(ironic_port.uuid, patch)
