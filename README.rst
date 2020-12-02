networking-mlnx-baremetal
=========================


Overview
========

This project aims to provide a OpenStack Neutron ML2 mechanism driver for
binding or unbinding partition key for mellanox infiniband port when
provisioning baremetal node using OpenStack Ironic component.

Those baremetal nodes are expected to have "VLAN" or "VXLAN" ethernet segment
bound by other driver[1], and ``networking-mlnx-baremetal`` will bind partition
key which have exactly the same segmentation-id as former ethernet segment for
Mellanox infiniband ports on the same node.

This hierarchical network topologies is supported by Neutron and mentioned
on spec `Hierarchical Port Binding`_. The final network topology looks like:

::

     +-----------------+                +-------------+
     | Mellanox Switch |                | Core Switch |
     +---+-----+-------+                +-------+-----+
         |     |                                |
         |     |                                |
         |     |                         +------+-----+               
         |     |                         | ToR Switch |            
         |     |                         +--+------+--+            
         |     |                                |
         |     |                            |      |           
         |     |                            |      |                
         |     |  IB  +--------------+  eth |      |  
         |     +------+ Ironic Node  +------+      |  
         |   PKey     +--------------+    VXLAN    |
         |                                         |
         |     IB     +--------------+    eth      |  
         +------------+ Ironic Node  +-------------+    
       PKey           +--------------+           VXLAN


Currently, this driver is only tested along with ``networking-huawei`` driver
 and Ironic ``ramdisk`` deploy interface on OpenStack ``stable/train`` release.


Installation
=============

Before using this driver, it should be installed on OpenStack Neutron
controller node. You may install it:

From PyPi:

.. code-block:: bash

   $ pip install networking-mlnx-baremetal


or

.. code-block:: bash

   $ easy_install networking-mlnx-baremetal


Or from source:

.. code-block:: bash

   $ git clone https://github.com/IamFive/networking-mlnx-baremetal.git
   $ cd networking-mlnx-baremetal
   $ git checkout stable/train
   $ pip install -r requirements.txt -c upper-constraints.txt
   $ python setup.py install


Usage
=====

Configuration
^^^^^^^^^^^^^

This driver will load configuration options in two namespaces:

- mlnx.baremetal.driver: configuration options for driver itself
- mlnx.ironic.client: configuration options for connecting to Ironic controller

So, after ``networking-mlnx-baremetal`` is installed, you may run this
command to get a full list of ``mlnx.baremetal.driver`` configuration options:

.. code-block:: shell

    $ oslo-config-generator --namespace mlnx.baremetal.driver

The default configurations may looks like:

.. code-block:: ini

    [DEFAULT]


    [mlnx:baremetal]

    #
    # From mlnx.baremetal.driver
    #

    # UFM REST API endpoint. (string value)
    #endpoint = http://127.0.0.1

    # Username for UFM REST API authentication. (string value)
    #username = <None>

    # Password for UFM REST API authentication. (string value)
    #password = <None>

    # Either a Boolean value, a path to a CA_BUNDLE file or directory with
    # certificates of trusted CAs. If set to True the driver will verify
    # the UFMhost certificates; if False the driver will ignore verifying
    # the SSL certificate. If it's a path the driver will use the
    # specified certificate or one of the certificates in the directory.
    # Defaults to True. Optional. (string value)
    #verify_ca = True

    # UFM REST API HTTP timeout in seconds. (integer value)
    #timeout = 10

    # Comma-separated list of physical_network which this driver should
    # watch. * means any physical_networks including None. (list value)
    #physical_networks = *

    # Whether SR-IOV is enabled for binding infiniband port to different
    # pkeys when necessary. Defaults to False. Optional. (boolean value)
    #enable_sriov = false

    # Comma-separated list of limited pkey to bound by default, examples:
    # 0x0001,0x0002. For every limited pkey, if SR-IOV is enabled, driver
    # will virtualize a new port with unique GUID and MAC, then bind the
    # virtual port GUID to the limited pkey. If SR-IOV is not enabled,
    # driver will bind the physical infiniband port to the pkey with
    # option index0 valued False. Defaults None. Optional. (list value)
    #default_limited_pkeys = <None>



Of course, you should generate options for ``mlnx.ironic.client`` too, then
update those options and add them to neutron config-file.


Enable driver
^^^^^^^^^^^^^

The entry point name of this driver is ``mlnx_ib_bm``. To enable, add
``mlnx_ib_bm`` to ML2 mechanism driver list:

.. code-block:: ini

    [ml2]
    tenant_network_types = vxlan
    mechanism_drivers = mlnx_ib_bm,other_vxlan_driver,...,openvswitch


Enable SR-IOV
^^^^^^^^^^^^^

To enable SR-IOV feature of Mellanox infiniband port for binding
``default_limited_pkeys``, extra three steps is required:

- Enable SR-IOV in node's Mellanox firmware (reboot required)
- Using crafted image with Mellanox SR-IOV component
- Build a customer vendor-data metadata service

Step 1 and 2 would be provided through ``mellanox-sriov`` element of `DIB`_.
Step 1 is the prerequisites of step 2 and a reboot is required, so step 1 is
usually scheduled along with inspection. Step 3 would be provided through
`PCSS vendor metadata`_ project (this is a private project).


Config Ironic-Inspector
^^^^^^^^^^^^^^^^^^^^^^^

By default, inspector will only detect PXE port information. To also get
infiniband port, ``add_port`` should be set to ``all``.

.. code-block:: ini

    [processing]
    processing_hooks = $default_processing_hooks,extra_hardware,lldp_basic,local_link_connection
    add_ports=all

Also, remember Mellanox infiniband hardware driver should be packaged in
inspect ramdisk image. If SR-IOV is enabled, ``mellanox-sriov`` element
should be included in inspection ramdisk image.


.. _Hierarchical Port Binding: https://specs.openstack.org/openstack/neutron-specs/specs/kilo/ml2-hierarchical-port-binding.html
.. _DIB: https://github.com/IamFive/diskimage-builder
.. _PCSS vendor metadata: https://github.com/IamFive/pcss-vendor-metadata
