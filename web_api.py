import requests
import json
import websockets
import asyncio
from functools import wraps
import threading
import nest_asyncio
import time
from gcores.logger import *
from gcores.wrappers import *

__all__ = ["get_mirai_status", "get_group_list", "send_group_message1", "recall_message", "get_message_count",
           "fetch_message", "send_group_image1", "acquire_message", "send_group_mixed", "get_member_name",
           "get_member_info", "set_member_name", "send_friend_message1", "require_message", "send_friend_mixed",
           "send_temp_message1", "send_temp_mixed", "send_friend_image1", "send_temp_image1"]
mode = None

nest_asyncio.apply()

mirai_http_port = "http://localhost:33454/"
mirai_ws_all_port = "ws://localhost:33455/all"
mirai_ws_message_port = "ws://localhost:33455/message"
mirai_ws_event_port = "ws://localhost:33455/event"

"""http service"""

https = requests.session()


@safe_run
def init_http():
    global mode
    if mode is None:
        mode = "http"
        log_message("http inited")
    else:
        return


@safe_run
def http_get(sub_address, data=None):
    r = https.get(mirai_http_port + sub_address, data=data)
    return json.loads(r.text)


@safe_run
def http_post(sub_address, data):
    data = json.dumps(data)
    r = https.post(mirai_http_port + sub_address, data=data)
    return json.loads(r.text)


"""WS service"""

wss_all = None
wss_message = None
wss_event = None

wss_lock = threading.Lock()
wss_loop = asyncio.new_event_loop()


@safe_run
def wait_sync(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if func is not None:
            return wss_loop.run_until_complete(func(*args, **kwargs))
        else:
            return None

    return wrapper


# noinspection PyUnresolvedReferences
@wait_sync
@safe_run
async def ws_send(data, wss=wss_all):
    await wss.send(data)


# noinspection PyUnresolvedReferences
@wait_sync
@safe_run
async def ws_recv(wss=None):
    recv = await wss.recv()
    return recv


@safe_run
def init_ws():
    @wait_sync
    @safe_run
    async def ws_connect():
        global wss_all, wss_message, wss_event
        wss_all = await websockets.connect("ws://localhost:33455/all")
        # wss_message = await websockets.connect("ws://localhost:33455/message")
        # wss_event = await websockets.connect("ws://localhost:33455/event")
        await wss_all.recv()
        # await wss_message.recv()

    global mode
    if mode is None:
        mode = "ws"
    else:
        return
    global wss_all, wss_message, wss_event
    ws_connect()
    ws_recv_refresh_task = WsRecvRefresh(1, "ws_recv_refresh_task", wss_all)
    ws_recv_refresh_task.setDaemon(True)
    ws_recv_refresh_task.start()
    log_message("ws inited")


@safe_run
def ws_send_cmd(command, content, wss=wss_all):
    sync_id = str(hash(command) % 65535)
    ws_send(json.dumps({"syncId": sync_id, "command": command, "content": content}), wss=wss)
    recv = ws_recv_for(sync_id)
    return recv


ws_recv_cache = []
ws_recv_cache_lock = threading.Lock()


class WsRecvRefresh(threading.Thread):
    def __init__(self, thread_id, name, wss=wss_all):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.wss = wss

    # noinspection PyTypeChecker
    def run(self):
        while True:
            recv = ws_recv(wss_all)
            new = json.loads(recv)
            if new['syncId'] == '-1':
                ws_recv_cache.append(new)
                continue
            for cache in ws_recv_cache:
                if cache['syncId'] == new['syncId']:
                    continue
            ws_recv_cache.append(new)


@safe_run
def ws_recv_for(sync_id):
    while True:
        ws_recv_cache_lock.acquire()
        for cache in ws_recv_cache:
            if str(cache['syncId']) == str(sync_id):
                ws_recv_cache.remove(cache)
                ws_recv_cache_lock.release()
                return cache['data']
        ws_recv_cache_lock.release()
        time.sleep(0.1)


"""Mirai server api"""


@safe_run
def get_mirai_status():
    try:
        if mode == "http":
            data = http_get("about")
        elif mode == "ws":
            data = ws_send_cmd("about", "", wss=wss_all)
        else:
            return None
        if data['code'] == 0:
            return True
        else:
            return False
    except Exception as error:
        print(error)
        return False


@safe_run
def get_group_list():
    if mode == "http":
        data = http_get("groupList")
    elif mode == "ws":
        data = ws_send_cmd("groupList", "", wss=wss_all)
    else:
        return None
    if data['code'] == 0:
        return data['data']
    else:
        return None


@safe_run
def send_friend_message1(qq_id, message, quote=None):
    if quote is None:
        data = {"target": qq_id, "messageChain": [{"type": "Plain", "text": message}]}
    else:
        data = {"target": qq_id, "quote": quote, "messageChain": [{"type": "Plain", "text": message}]}
    if mode == "http":
        message_id = http_post("sendFriendMessage", data)
    elif mode == "ws":
        message_id = ws_send_cmd("sendFriendMessage", data, wss=wss_all)
    else:
        message_id = None
    return message_id


@safe_run
def send_friend_image1(qq_id, image, quote=None):
    """
    发送单条群图片
    :param quote: quote message id
    :param qq_id: qq id
    :param image: one single image to send
    :return: message id
    """
    if quote is None:
        data = {"target": qq_id, "messageChain": [{"type": "Image", "url": image}]}
    else:
        data = {"target": qq_id, "quote": quote, "messageChain": [{"type": "Image", "url": image}]}
    if mode == "http":
        message_id = int(http_post("sendFriendMessage", data, )['messageId'])
    elif mode == "ws":
        message_id = int(ws_send_cmd("sendFriendMessage", data, wss=wss_all)['messageId'])
    else:
        message_id = None
    return message_id


@safe_run
def send_friend_mixed(qq_id, message_chain, quote=None):
    """
    发送一条 qq 消息
    :param quote: quote message id
    :param qq_id: qq id
    :param message_chain: one single message to send
    eg: [{"type":"Plain/Image/At","text/url/target":xxxx }]
    :return: message id
    """
    if quote is None:
        data = {"target": qq_id, "messageChain": message_chain}
    else:
        data = {"target": qq_id, "quote": quote, "messageChain": message_chain}
    if mode == "http":
        message_id = int(http_post("sendFriendMessage", data, )['messageId'])
    elif mode == "ws":
        message_id = int(ws_send_cmd("sendFriendMessage", data, wss=wss_all)['messageId'])
    else:
        message_id = None
    return message_id


@safe_run
def send_temp_message1(qq_id, group_id, message, quote=None):
    qq_id = int(qq_id)
    group_id = int(group_id)
    if quote is None:
        data = {"qq": qq_id, "group": group_id, "messageChain": [{"type": "Plain", "text": message}]}
    else:
        data = {"qq": qq_id, "group": group_id, "quote": quote, "messageChain": [{"type": "Plain", "text": message}]}
    if mode == "http":
        message_id = http_post("sendTempMessage", data)
    elif mode == "ws":
        message_id = ws_send_cmd("sendTempMessage", data, wss=wss_all)
    else:
        message_id = None
    return message_id


@safe_run
def send_temp_image1(qq_id, group_id, image, quote=None):
    """
    发送单条群图片
    :param group_id: group id
    :param qq_id: qq id
    :param quote: quote message id
    :param image: one single image to send
    :return: message id
    """
    if quote is None:
        data = {"qq": qq_id, "group": group_id, "messageChain": [{"type": "Image", "url": image}]}
    else:
        data = {"qq": qq_id, "group": group_id, "messageChain": [{"type": "Image", "url": image}]}
    if mode == "http":
        message_id = int(http_post("sendTempMessage", data, )['messageId'])
    elif mode == "ws":
        message_id = int(ws_send_cmd("sendTempMessage", data, wss=wss_all)['messageId'])
    else:
        message_id = None
    return message_id


@safe_run
def send_temp_mixed(qq_id, group_id, message_chain, quote=None):
    """
    发送一条 qq 消息
    :param group_id: group id
    :param quote: quote message id
    :param qq_id: qq id
    :param message_chain: one single message to send
    eg: [{"type":"Plain/Image/At","text/url/target":xxxx }]
    :return: message id
    """
    if quote is None:
        data = {"qq": qq_id, "group": group_id, "messageChain": message_chain}
    else:
        data = {"qq": qq_id, "group": group_id, "messageChain": message_chain}
    if mode == "http":
        message_id = int(http_post("sendTempMessage", data, )['messageId'])
    elif mode == "ws":
        message_id = int(ws_send_cmd("sendTempMessage", data, wss=wss_all)['messageId'])
    else:
        message_id = None
    return message_id


@safe_run
def send_group_message1(group_id, message, quote=None):
    """
    发送单条群消息
    :param quote: quote message id
    :param group_id: group id
    :param message: one single message to send
    :return: message id
    """
    if quote is None:
        data = {"target": group_id, "messageChain": [{"type": "Plain", "text": message}]}
    else:
        data = {"target": group_id, "quote": quote, "messageChain": [{"type": "Plain", "text": message}]}
    if mode == "http":
        message_id = int(http_post("sendGroupMessage", data, )['messageId'])
    elif mode == "ws":
        message_id = int(ws_send_cmd("sendGroupMessage", data, wss=wss_all)['messageId'])
    else:
        message_id = None
    return message_id


@safe_run
def send_group_image1(group_id, image, quote=None):
    """
    发送单条群图片
    :param quote: quote message id
    :param group_id: group id
    :param image: one single image to send
    :return: message id
    """
    if quote is None:
        data = {"target": group_id, "messageChain": [{"type": "Image", "url": image}]}
    else:
        data = {"target": group_id, "quote": quote, "messageChain": [{"type": "Image", "url": image}]}
    if mode == "http":
        message_id = int(http_post("sendGroupMessage", data, )['messageId'])
    elif mode == "ws":
        message_id = int(ws_send_cmd("sendGroupMessage", data, wss=wss_all)['messageId'])
    else:
        message_id = None
    return message_id


@safe_run
def send_group_mixed(group_id, message_chain, quote=None):
    """
    发送一条混合群消息
    :param quote: quote message id
    :param group_id: group id
    :param message_chain: one single message to send
    eg: [{"type":"Plain/Image/At","text/url/target":xxxx }]
    :return: message id
    """
    if quote is None:
        data = {"target": group_id, "messageChain": message_chain}
    else:
        data = {"target": group_id, "quote": quote, "messageChain": message_chain}
    if mode == "http":
        message_id = int(http_post("sendGroupMessage", data, )['messageId'])
    elif mode == "ws":
        message_id = int(ws_send_cmd("sendGroupMessage", data, wss=wss_all)['messageId'])
    else:
        message_id = None
    return message_id


@safe_run
def recall_message(message_id):
    """
    撤回消息
    :param message_id: message id
    :return: status
    """
    data = {"target": message_id}
    if mode == "http":
        return http_post("recall", data)['msg']
    elif mode == "ws":
        return ws_send_cmd("recall", data, wss=wss_all)['msg']
    else:
        return None


@safe_run
def get_member_name(group_id, member_id):
    """
    获取群成员名称
    :param group_id: group id
    :param member_id: member id
    :return: member name
    """
    member_info = get_member_info(group_id, member_id)
    try:
        return member_info["memberName"]
    except:
        return None


@safe_run
def get_member_info(group_id, member_id):
    """
    获取群成员信息
    :param group_id: group id
    :param member_id: member id
    :return: member info
    """
    if mode == "http":
        data = "?target=" + str(group_id) + "&memberId=" + str(member_id)
        info = http_get("memberInfo" + data)
        return info
    elif mode == "ws":
        data = {"target": group_id, "memberId": member_id}
        return ws_send_cmd("getMemberInfo", data, wss=wss_all)['data']
    else:
        return None


@safe_run
def set_member_name(group_id, member_id, member_name):
    member_info = get_member_info(group_id, member_id)
    if member_info["memberName"] == member_name:
        return 2
    else:
        data = {"target": int(group_id), "memberId": int(member_id), "info": {"name": str(member_name)}}
        if mode == "http":
            return http_post("memberInfo", data)['msg']
        elif mode == "ws":
            return ws_send_cmd("memberInfo", data, wss=wss_all)['msg']
        else:
            return None


@safe_run
def get_message_count():
    """
    获取消息数量
    :return: message count
    """
    data = http_get("countMessage")
    if data['code'] == 0:
        return data['data']
    else:
        return None


@safe_run
def fetch_message(count):
    """
    获取消息
    :return: message
    """
    data = http_get("fetchMessage?count=" + str(count))
    if data['code'] == 0:
        return data['data']
    else:
        return None


@safe_run
def require_message(message_id):
    """
    获取消息
    :return: message
    """
    if mode == "http":
        data = http_get("messageFromId?id=" + str(message_id))
        if data['code'] == 0:
            return data['data']
        else:
            return None
    else:
        return None


@safe_run
def acquire_message():
    if mode == "ws":
        return ws_recv_for("-1")
    else:
        return None


if __name__ == '__main__':
    init_ws()
    print(send_group_message1(314760465, "hello"))
    while True:
        pass
