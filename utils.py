import subprocess
import os
import re
import logging

logger = logging.getLogger(__name__)


def init_environment(context,base_image):

    logger.info("init kvdb ..")
    # 1. create redis kvdb
    kvdb_docker = create_docker("redis")

    # store docker instance id to context
    context.kvdb = kvdb_docker

    # 2. we should rewrite kvdb url to every conf file
    kvdb_ip_address = get_docker_ip(kvdb_docker)

    config_path = os.getcwd() + "Features/config"
    kvdb_url_format = re.compile(r'(module.redisdb.url=*)')
    for file in os.listdir(config_path):
        if file.endswith(".conf"):
            # config file is so small, so read all .. write all
            with open(config_path + "/" + file) as f:
                lines = [line for line in f.readlines() if not kvdb_url_format.match(line)]
                lines.append("module.redisdb.url=http://" + str(kvdb_ip_address))

            with open(config_path + "/" + file,"w") as f:
                f.truncate()
                f.writelines(lines)

    logger.info("init host ..")
    # 3. start two docker container as host !
    host1 = create_docker(base_image)
    context.host1 = host1
    host1_ip_address = get_docker_ip(host1)

    host2 = create_docker(base_image)
    context.host2 = host2
    host2_ip_address = get_docker_ip(host2)

    init_docker_host(context, host1)
    init_docker_host(context,host2)

    logger.info("add vxlan interface ..")
    # add host vxlan interface
    add_host_vxlan_interface(host1,host1_ip_address,host2_ip_address)
    add_host_vxlan_interface(host2,host2_ip_address,host1_ip_address)

    # add host vlan interface

    logger.info("init bridge ..")
    # vlan interface , user other ovs bridge in docker
    bridge = create_docker(base_image)
    context.bridge = bridge
    init_docker_bridge(bridge)

    logger.info("add vlan interface ..")
    add_host_vlan_interface(bridge,host1)
    add_host_vlan_interface(bridge,host2)


def uninit_environment(context):

    if hasattr(context,"bridge"):
        if hasattr(context,"host1"):
            remove_host_vlan_interface(context.bridge,context.host1)

        if hasattr(context,"host2"):
            remove_host_vlan_interface(context.bridge,context.host2)

        remove_docker(context.bridge)
        delattr(context,"bridge")

    if hasattr(context,"kvdb"):
        remove_docker(context.kvdb)
        delattr(context,"kvdb")

    if hasattr(context,"host1"):
        remove_host_vxlan_interface(context.host1)
        remove_docker(context.host1)
        delattr(context,"host1")

    if hasattr(context,"host2"):
        remove_host_vxlan_interface(context.host2)
        remove_docker(context.host2)
        delattr(context,"host2")

def create_docker(image):
    cmd = "docker run -it -d --privileged " + image

    kvdb_id = subprocess.check_output(cmd,shell=True)

    return kvdb_id.strip(b'\n')


def remove_docker(image):
    cmd = "docker rm -f %s" % image
    subprocess.check_call(cmd,shell=True)


def get_docker_ip(docker):

    cmd = "docker inspect --format={{.NetworkSettings.Networks.bridge.IPAddress}} " + docker

    ip = subprocess.check_output(cmd,shell=True)

    return ip.strip(b'\n')


def init_docker_host(context,docker):

    # install ovs ; do in base image Dockerfile

    # start ovs server
    cmd = "service openvswitch-switch start"
    call_in_docker(docker,cmd)

    # copy wheel file
    vlcp_wheel = "vlcp-1.2.3-py2-none-any.whl"

    if "vlcp" in context.config.userdata["vlcp"]:
        vlcp_wheel = context.config.userdata["vlcp"]

    cmd = "docker cp %s %s:/opt" % (vlcp_wheel,docker)
    subprocess.check_call(cmd,shell=True)

    # add ovs bridge br0
    cmd = "ovs-vsctl add-br br0"
    call_in_docker(docker,cmd)

    # set br0 controller to 127.0.0.1
    cmd = "ovs-vsctl set-controller br0 tcp:127.0.0.1"
    call_in_docker(docker,cmd)


def init_docker_bridge(bridge):

    # start ovs server
    cmd = "service openvswitch-switch start"
    call_in_docker(bridge,cmd)

    cmd = "ovs-vsctl add-br br0"
    call_in_docker(bridge,cmd)


def call_in_docker(docker,cmd):
    c = "docker exec %s %s" % (docker,cmd)
    subprocess.check_output(c,shell=True)


def add_host_vxlan_interface(docker,local_ip,remote_ip):
    cmd = "ovs-vsctl add-port br0 vxlan0 -- set interface vxlan0 " \
          "type=vxlan options:key=flow options:local_ip=%s options:remote_ip=%s" % (local_ip,remote_ip)

    call_in_docker(docker,cmd)


def remove_host_vxlan_interface(docker):
    pass


def add_host_vlan_interface(bridge,docker):

    # create link file , so we can operate network namespace
    link_docker_namespace(bridge)
    link_docker_namespace(docker)

    # create veth pair link bridge and docker
    cmd = "ip link add %s type veth peer name %s" % ("docker-"+docker[0:4],"bridge")
    subprocess.check_call(cmd,shell=True)

    # add link to namespace
    cmd = "ip link set %s netns %s" % ("bridge",docker)
    subprocess.check_call(cmd,shell=True)
    cmd = "ip link set %s netns %s" % ("docker-"+docker[0:4],bridge)
    subprocess.check_call(cmd,shell=True)

    cmd = "ip netns exec %s ip link set %s up" % (bridge,"docker-"+docker[0:4])
    subprocess.check_call(cmd,shell=True)

    cmd = "ip netns exec %s ip link set %s up" % (docker,"bridge")
    subprocess.check_call(cmd,shell=True)

    cmd = "ovs-vsctl add-port br0 %s" % "bridge"
    call_in_docker(docker,cmd)

    cmd = "ovs-vsctl add-port br0 %s" % "docker-"+docker[0:4]
    call_in_docker(bridge,cmd)

    unlink_docker_namespace(bridge)
    unlink_docker_namespace(docker)

def remove_host_vlan_interface(bridge,docker):

    cmd = "ip link del %s" % "bridge"
    call_in_docker(docker,cmd)


def link_docker_namespace(docker):

    # get docker pid
    cmd = "docker inspect --format={{.State.Pid}} %s" % docker
    pid = subprocess.check_output(cmd,shell=True)
    pid = pid.strip(b'\n')

    # link docker namespace file
    cmd = "ln -sf /proc/%s/ns/net /var/run/netns/%s" % (pid,docker)
    subprocess.check_call(cmd,shell=True)

def unlink_docker_namespace(docker):
    cmd = "rm /var/run/netns/%s" % docker
    subprocess.check_call(cmd,shell=True)