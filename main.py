import mirai_server
import os
import web_api
from gcores.logger import *
import sys
import json

config = {}
try:
    with open("config/config.json.rd", "r") as file:
        config = json.load(file)
except:
    with open("config/config.json.rd", "w") as file:
        config = {}
        json.dump(config, file)


def start_server():
    mirai_server.init_mirai_servers()
    if len(sys.argv) > 1:
        mirai_server.deal_post_status(sys.argv[1])
    mirai_server.start_mirai_servers()


if __name__ == '__main__':
    web_api.init_http()
    if not web_api.get_mirai_status():
        general_message("Fail", "Make sure you started mirai server")
        os.system("explorer " + config["mirai_path"])
        exit()
    log_message("Connected to mirai service")
    start_server()
