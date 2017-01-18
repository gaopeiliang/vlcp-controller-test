import logging

from utils import init_environment, uninit_environment

logging.basicConfig()
logger = logging.getLogger(__name__)

def before_all(context):
    base = "vlcp-controller/test"
    tag = "python2.7"
    
    if "tag" in context.config.userdata:
        tag = context.config.userdata["tag"]

    if "base" in context.config.userdata:
        base = context.config.userdata["base"]

    docker_base_image = base + ":" + tag

    try:
        init_environment(context,docker_base_image)
    except Exception :
        uninit_environment(context)

def after_all(context):
    
    uninit_environment(context)