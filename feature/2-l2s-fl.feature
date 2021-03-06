Feature: l2switch flow learning

    Scenario: l2switch logicalport on different node
        Given create vxlan physicalnetwork "edac6346"
        and create logicalnetwork "1fd3954a" "edac6346"
        and create logicalport "d13f31a2" "1fd3954a" "76:b8:46:68:eb:ac"
        and ovs add interface "veth1" "d13f31a2" "host1" "76:b8:46:68:eb:ac"
        and create logicalport "963008a6" "1fd3954a" "be:cf:72:24:77:b0"
        and ovs add interface "veth1" "963008a6" "host2" "be:cf:72:24:77:b0"
        when create physicalport "vxlan0" "edac6346"
        then check l2switch flow learn flow
        and check two logicalport ping "host1" "veth1" "host2" "veth1"
        and check l2switch learn "be:cf:72:24:77:b0" on "host1"
        and check l2switch learn "76:b8:46:68:eb:ac" on "host2"
        and check l2switch learn "76:b8:46:68:eb:ac" on "host1"
        and check l2switch learn "be:cf:72:24:77:b0" on "host2"


