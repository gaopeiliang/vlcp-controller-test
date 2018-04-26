Feature: l3switch external network
    Scenario: l3switch external mode
        Given create vlan physicalnetwork "e8e386fa"
        and create physicalport "bridge" "e8e386fa"
        and create logicalnetwork "17f3d580" "e8e386fa"
        and create external subnet "257af374","17f3d580","172.100.200.0/24" "172.100.200.253"

        # we remove host2 ovs interface 'bridge', the vm on host2
        # can to external through host1 forward
        and ovs remove interface "bridge" "host2"

        and create vxlan physicalnetwork "edac6346"
        and create physicalport "vxlan0" "edac6346"
        and create logicalnetwork "1fd3954a" "edac6346"
        and create subnet "236fae62","1fd3954a","172.100.101.0/24" "172.100.101.1"
        and create l3 logicalport "d13f31a2" "1fd3954a" "236fae62" "76:b8:46:68:eb:ac" "172.100.101.2"
        and ovs add interface "veth1" "d13f31a2" "host1" "76:b8:46:68:eb:ac"
        and dhcp get ip "host1" "veth1"
        and check get ip "host1" "veth1" "172.100.101.2"

        and create router "c707aa9c"
        and add router interface "c707aa9c" "257af374"
        and add router interface "c707aa9c" "236fae62"
        and config bridge as external "172.100.101.0/24" gateway "172.100.200.253"

        and create l3 logicalport "963008a6" "1fd3954a" "236fae62" "be:cf:72:24:77:b0" "172.100.101.3"
        and ovs add interface "veth1" "963008a6" "host2" "be:cf:72:24:77:b0"
        and dhcp get ip "host2" "veth1"
        and check get ip "host1" "veth1" "172.100.101.2"

        then check l3 logicalport ping address "host1" "veth1" "172.100.101.1"
        and check l3 logicalport ping address "host1" "veth1" "172.100.200.253"
        and check l3 logicalport ping address "host2" "veth1" "172.100.101.1"
        and check l3 logicalport ping address "host2" "veth1" "172.100.200.253"
        
        # the last we add 'bridge' to ovs on host2
        and ovs add interface "bridge" "-" "host2" "00:00:00:00:00:00"
        
        # update external subnet pre_host_config, before v1.5 , l3router don't care it
        # after l3router will union the config 
        and update subnet pre host config "257af374" "host1" "br0" "%" "172.100.200.0/24" "172.100.200.100" "172.100.200.253"
        
        and check l3 logicalport ping address "host1" "veth1" "172.100.101.1"
        and check l3 logicalport ping address "host1" "veth1" "172.100.200.253"
        and check l3 logicalport ping address "host2" "veth1" "172.100.101.1"
        and check l3 logicalport ping address "host2" "veth1" "172.100.200.253"