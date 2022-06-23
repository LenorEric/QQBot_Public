import os
import time
import sys
import requests
from PIL import Image
from io import BytesIO
from gcores.rules_operator import *
from gcores.logger import *

__all__ = ["get_git_version", "restart_program", "save_image_from_url"]


def get_git_version():
    return os.popen("git rev-parse --short HEAD").read().strip()


def restart_program(*argv_add):
    time.sleep(3)
    log_message("Program Exit\n")
    save_rules()
    sys.stdout.flush()
    os.execl(sys.executable, sys.executable, *argv_add)
    exit()


def save_image_from_url(url, path, name):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    if not os.path.exists(path):
        os.makedirs(path)
    image.save(os.path.join(path, name))
    return os.path.join(path, name)
