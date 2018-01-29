# Copyright 2018 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import charms_openstack.adapters
import charms_openstack.charm
import charmhelpers.contrib.openstack.utils as ch_utils

from charmhelpers.contrib.python.packages import pip_install


ML2_CONF = '/etc/neutron/plugins/ml2/ml2_conf.ini'
ML2_CONF_ARISTA = '/etc/neutron/plugins/ml2/ml2_conf_arista.ini'
VLAN = 'vlan'
VXLAN = 'vxlan'
GRE = 'gre'
OVERLAY_NET_TYPES = [VLAN]
NETWORKING_ARISTA_PACKAGE = 'networking-arista'


@charms_openstack.adapters.config_property
def overlay_net_types(config):
    overlay_networks = config.overlay_network_type.split()
    for overlay_net in overlay_networks:
        if overlay_net not in OVERLAY_NET_TYPES:
            raise ValueError(
                'Unsupported overlay-network-type {}'.format(overlay_net))
    return ','.join(overlay_networks)


@charms_openstack.charm.register_os_release_selector
def choose_charm_class():
    """Choose the charm class based on the neutron-common package installed"""
    return ch_utils.os_release('neutron-common')


class IcehouseNeutronAPIAristaCharm(charms_openstack.charm.OpenStackCharm):

    name = 'neutron-api-arista'
    release = 'icehouse'

    packages = ['neutron-common', 'neutron-plugin-ml2', 'python-pip']

    required_relations = ['neutron-plugin-api-subordinate']

    restart_map = {ML2_CONF: [], ML2_CONF_ARISTA: []}
    adapters_class = charms_openstack.adapters.OpenStackRelationAdapters

    # Custom configure for the class
    service_plugins = 'router,firewall,lbaas,vpnaas,metering'

    def configure_plugin(self, api_principle):
        """Add sections and tuples to insert values into neutron-server's
        neutron.conf
        """
        inject_config = {
            "neutron-api": {
                "/etc/neutron/neutron.conf": {
                    "sections": {
                        'DEFAULT': [
                        ],
                    }
                }
            }
        }

        api_principle.configure_plugin(
            neutron_plugin='ovs',
            core_plugin='neutron.plugins.ml2.plugin.Ml2Plugin',
            neutron_plugin_config='/etc/neutron/plugins/ml2/ml2_conf.ini',
            service_plugins=self.service_plugins,
            subordinate_configuration=inject_config)

    def install(self):
        """In addition to other commands, install our arista package.

        TODO: add an http proxy?
        TODO: add version
        TODO: stick the pip package in the wheelhouse instead
        """
        pip_install(NETWORKING_ARISTA_PACKAGE)
        super().install()


class KiloNeutronAPIAristaCharm(IcehouseNeutronAPIAristaCharm):
    """For the kilo release we have an additional package to install:
    'python-networking-arista'
    """

    release = 'kilo'

class NewtonNeutronAPIAristaCharm(KiloNeutronAPIAristaCharm):
    """For Newton, the service_plugins on the configuration is different.
    """

    release = 'newton'

    # NOTE: LBaaS v2 for >= newton
    service_plugins = ('router,firewall,vpnaas,metering,'
                       'neutron_lbaas.services.loadbalancer.'
                       'plugin.LoadBalancerPluginv2')

class PikeNeutronAPIAristaCharm(NewtonNeutronAPIAristaCharm):
    """Nothing fancy for Pike."""
    
    release = 'pike'

