from behave import *
from utils import *
from apis import *

@Given('create vxlan physicalnetwork "{network_id}"')
def create_vxlan_physicalnetwork(context, network_id):
    c = create_physical_network(network_id, type="vxlan")

    command = 'python -c "%s"' % c

    call_in_docker(context.host1, command)


@Given ('delete physicalport "{name}"')
def delete_physical_port(context, name):
    c = remove_physical_port(name)

    command = 'python -c "%s"' % c

    call_in_docker(context.host1, command)


@then("check vxlan physicalport online")
def check_vxlan_physicalport_online(context):
    # table 0 have tun_id flow > 0
    cmd = "ovs-ofctl dump-flows br0 -O Openflow13 | grep 'table=0' | grep 'tun_id=' | wc -l"

    result = call_in_docker(context.host1, cmd)

    assert int(result) >= 1


@Then("check vxlan physicalport offline")
def check_vxlan_physicalport_offline(context):

    # table 0 have tun_id flow < 1
    cmd = "ovs-ofctl dump-flows br0 -O Openflow13 | grep 'table=0' | grep 'tun_id=' | wc -l"

    result = call_in_docker(context.host1, cmd)

    assert int(result) <= 0


@Then('check prepush "{mac}" on "{host}"')
def check_vxlan_prepush(context, mac, host):
    host_map = {"host1": context.host1, "host2": context.host2}

    # vxlanoutput table should have prepush flow
    cmd = "ovs-ofctl dump-flows br0 -O Openflow13 | grep 'table=5' | grep %s | wc -l" % mac

    result = call_in_docker(host_map[host], cmd)

    assert int(result) >= 1

