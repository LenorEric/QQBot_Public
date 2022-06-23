import threading

__all__ = ["get_message_cache", "set_message_cache"]

msg_cache = {}
msg_cache_lock = threading.Lock()
""" {group_id: ["last_message_text", count], ...} """


def get_message_cache(target):
    msg_cache_lock.acquire()
    group_info = msg_cache.get(target, [])
    msg_cache_lock.release()
    return group_info


def set_message_cache(target, msg_info):
    msg_cache_lock.acquire()
    msg_cache[target] = msg_info
    msg_cache_lock.release()
