# -*- coding: UTF-8 -*-

import threading
import os
import time
import json
import base64
from func_timeout import FunctionTimedOut
from web_api import *
from pcores.routine_task import *
from pcores.message_processor import *
from pcores.event_processor import *
from pcores.wait_message import *
from gcores.general import *
from gcores.logger import *
from gcores.wrappers import *

__all__ = ["deal_message", "init_mirai_servers", "deal_post_status", "start_mirai_servers"]

group_list = None


@safe_run
def init_group_server():
    scan_group_list()
    log_message("Group inited")


@safe_run
def hello_world():
    # noinspection PyTypeChecker
    for group in group_list:
        msg_id = send_group_message1(group['id'], "Server Online")
        recall_message(msg_id)


@safe_run
def scan_group_list():
    global group_list
    group_list = get_group_list()
    if group_list is None:
        return


processing_threads = []


class ProcessMessage(threading.Thread):
    def __init__(self, thread_id, name, raw_msg):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.raw_msg = raw_msg

    def run(self):
        try:
            process_message(self.raw_msg)
        except FunctionTimedOut:
            error_message("Func timeout when processing message,", str(self.raw_msg))


class ProcessEvent(threading.Thread):
    def __init__(self, thread_id, name, raw_msg):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.raw_msg = raw_msg

    def run(self):
        try:
            process_event(self.raw_msg)
        except FunctionTimedOut:
            error_message("Func timeout when processing message,", str(self.raw_msg))


class DumpTrash(threading.Thread):
    def __init__(self, thread_id, name):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name

    def run(self):
        def remove(_path):
            if not os.path.exists(_path):
                os.mkdir(_path)
            _ls = os.listdir(_path)
            for _file in _ls:
                _c_path = os.path.join(_path, _file)
                if os.path.isdir(_c_path):
                    pass
                else:
                    os.remove(_c_path)

        last_run = time.time()
        while True:
            for thread in processing_threads:
                if not thread.is_alive():
                    processing_threads.remove(thread)
            if time.time() - last_run > 60 * 15:
                general_message("Warning", "Thread occupies too much")
                last_run = time.time()
            if processing_threads:
                time.sleep(5)
                continue
            paths = ["./runtime-data/temp/"]
            for path in paths:
                try:
                    remove(path)
                except Exception as error:
                    error_message("Remove trash failed:", error)
            while not processing_threads:
                time.sleep(1)
            last_run = time.time()


# noinspection PyUnresolvedReferences
@safe_run
def deal_message():
    global processing_threads
    dump_trash_thread = DumpTrash(1, "dump_trash_thread")
    dump_trash_thread.setDaemon(True)
    dump_trash_thread.start()
    mc = get_message_count()
    fetch_message(mc)
    try:
        while True:
            mc = get_message_count()
            if mc > 0:
                msgs = fetch_message(mc)
                for raw_msg in msgs:
                    if "Message" in raw_msg["type"]:
                        if check_in_wait(raw_msg):
                            continue
                        current_thread = ProcessMessage(len(processing_threads), "message_processor_thread", raw_msg)
                        current_thread.setDaemon(True)
                        current_thread.start()
                        processing_threads.append(current_thread)
                    elif "Event" in raw_msg["type"]:
                        current_thread = ProcessEvent(len(processing_threads), "event_processor_thread", raw_msg)
                        current_thread.setDaemon(True)
                        current_thread.start()
                        processing_threads.append(current_thread)
                    else:
                        general_message("Fail", "Unsupported message type", raw_msg["type"])
            time.sleep(0.1)
    except KeyboardInterrupt:
        log_message("KeyboardInterrupt in: deal message")


@safe_run
def deal_post_status(post_status):
    general_message("Event", "Post Status")
    try:
        post_status = json.loads(base64.b64decode(post_status))
        if post_status["status"] == "restart":
            reply_msg = "重启成功，服务已重启"
            reply_target = post_status["reply_target"]
            reply_quote = post_status["reply_message_id"]
            send_group_message1(reply_target, reply_msg, quote=reply_quote)
        if post_status["status"] == "update":
            reply_msg = "，服务已重启。当前 git version: " + get_git_version()
            if post_status["git_version"] == get_git_version():
                reply_msg = "没有更新任何内容" + reply_msg
            else:
                reply_msg = "更新成功" + reply_msg
            reply_target = post_status["reply_target"]
            reply_quote = post_status["reply_message_id"]
            send_group_message1(reply_target, reply_msg, quote=reply_quote)
    except Exception as error:
        error_message(error, "on deal_post_status")


@safe_run
def init_mirai_servers():
    init_group_server()


@safe_run
def start_mirai_servers():
    thread_dm = threading.Thread(target=deal_message)
    thread_dm.setDaemon(True)
    thread_dm.start()
    log_message("Deal message thread started")
    thread = threading.Thread(target=run_routine_task)
    thread.setDaemon(True)
    thread.start()
    log_message("Routine task thread started")
    log_message("All servers started")
    try:
        while True:
            if not thread_dm.is_alive():
                error_message("Deal message thread died")
                break
            time.sleep(10)
    except KeyboardInterrupt:
        log_message("KeyboardInterrupt Exit")
        exit()


if __name__ == '__main__':
    init_group_server()
    deal_message()
