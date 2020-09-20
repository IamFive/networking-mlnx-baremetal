============
Installation
============

This section describes how to install and configure the
``networking-baremetal`` plugin and ``ironic-neutron-agent``.

The ``ironic-neutron-agent`` is a neutron agent that populates the host to
physical network mapping for baremetal nodes in neutron. Neutron uses this to
calculate the segment to host mapping information.

Install the networking-baremetal plugin and agent
-------------------------------------------------

At the command line:

.. code-block:: shell

    $ pip install networking-baremetal

Or, if you have neutron installed in a virtualenv,
install the ``networking-baremetal`` plugin to the same virtualenv:

.. code-block:: shell

    $ . <path-to-neutron-venv>/bin/activate
    $ pip install networking-baremetal

Or, use the package from your distribution.
For RHEL7/CentOS7:

.. code-block:: shell

    $ yum install python2-networking-baremetal python2-ironic-neutron-agent

Enable baremetal mechanism driver in the Networking service
-----------------------------------------------------------

To enable mechanism drivers in the ML2 plug-in, edit the
``/etc/neutron/plugins/ml2/ml2_conf.ini`` configuration file. For example, this
enables the ``openvswitch`` and ``baremetal`` mechanism drivers:

.. code-block:: ini

  [ml2]
  mechanism_drivers = openvswitch,baremetal

Configure ironic-neutron-agent
------------------------------

To configure the baremetal neutron agent, edit the neutron configuration
``/etc/neutron/plugins/ml2/ironic_neutron_agent.ini`` file. Add an ``[ironic]``
section. For example:

.. code-block:: ini

  [ironic]
  project_domain_name = Default
  project_name = service
  user_domain_name = Default
  password = password
  username = ironic
  auth_url = http://identity-server.example.com/identity
  auth_type = password
  region_name = RegionOne


Start ironic-neutron-agent service
----------------------------------

To start the agent either run it from the command line like in the example
below or add it to the init system.

.. code-block:: shell

   $ ironic-neutron-agent \
       --config-dir /etc/neutron \
       --config-file /etc/neutron/plugins/ml2/ironic_neutron_agent.ini \
       --log-file /var/log/neutron/ironic_neutron_agent.log

You can create a systemd service file ``/etc/systemd/system/ironic-neutron-agent.service``
for ``ironic-neutron-agent`` for systemd based distributions.
For example:

.. code-block:: ini

  [Unit]
  Description=OpenStack Ironic Neutron Agent
  After=syslog.target network.target

  [Service]
  Type=simple
  User=neutron
  PermissionsStartOnly=true
  TimeoutStartSec=0
  Restart=on-failure
  ExecStart=/usr/bin/ironic-neutron-agent --config-dir /etc/neutron --config-file /etc/neutron/plugins/ml2/ironic_neutron_agent.ini --log-file /var/log/neutron/ironic-neutron-agent.log
  PrivateTmp=true
  KillMode=process

  [Install]
  WantedBy=multi-user.target

.. Note:: systemd service file may be already available if you are installing from package released by linux distributions.

Enable and start the ``ironic-neutron-agent`` service:

.. code-block:: shell

    $ sudo systemctl enable ironic-neutron-agent.service
    $ sudo systemctl start ironic-neutron-agent.service
