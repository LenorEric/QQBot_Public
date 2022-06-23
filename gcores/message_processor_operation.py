import os
import sys
import re
import unicodedata
from functools import wraps
import cores.test_similarity.text_similarity as ts
from web_api import *
from gcores.logger import *
from gcores.rules_operator import *
from gcores.message_cache import *
from gcores.wrappers import *

__all__ = ["send_auto_message1", "send_auto_image1", "send_auto_mixed", "check_list", "check_message",
           "group_message_only", "find_keyword", "send_group_message", "punctuation_mend", "extract_text", "extract_at",
           "extract_image", "match_target", "rel_path_to_url", "img_database", "permission_zb", "permission_op",
           "exact_permission", "permission_admin", "permission", "extract_quote", "private_message_only",
           "restricted_scope", "get_scopes"]


@wraps(send_group_message1)
@safe_run
def send_group_message_wrapper(group_id, message, quote=None):
    def msg_process():
        group_info = get_message_cache(group_id)
        if message.strip() == "":
            return
        elif not group_info:
            group_info = [message, 4, [get_rules("bot_qq", default=3401562258)]]
        else:
            group_info = [message, 4, [get_rules("bot_qq", default=3401562258)]]
        set_message_cache(group_id, group_info)

    msg_process()
    return send_group_message1(group_id, message, quote=quote)


send_group_message = send_group_message_wrapper


@wraps(send_group_mixed)
@safe_run
def send_group_mixed_wrapper(group_id, message_chain, quote=None):
    def msg_process():
        fake_raw_msg = {"messageChain": message_chain}
        message = extract_text(fake_raw_msg)
        group_info = get_message_cache(group_id)
        if message.strip() == "":
            return
        elif not group_info:
            group_info = [message, 4, [get_rules("bot_qq", default=3401562258)]]
        else:
            group_info = [message, 4, [get_rules("bot_qq", default=3401562258)]]
        set_message_cache(group_id, group_info)

    msg_process()
    return send_group_mixed(group_id, message_chain, quote=quote)


send_group_mixed_wpd = send_group_mixed_wrapper


def send_auto_message1(raw_msg, message, quote=None, reply=None):
    if raw_msg["type"] == "GroupMessage":
        if reply is None:
            reply = True
        if reply:
            if quote is None:
                quote = raw_msg["messageChain"][0]["id"]
            send_group_message(raw_msg["sender"]["group"]["id"], message, quote=quote)
        else:
            send_group_message(raw_msg["sender"]["group"]["id"], message)
    elif raw_msg["type"] == "FriendMessage":
        if reply is None:
            reply = False
        if reply:
            if quote is None:
                quote = raw_msg["messageChain"][0]["id"]
            send_friend_message1(raw_msg["sender"]["id"], message, quote=quote)
        else:
            send_friend_message1(raw_msg["sender"]["id"], message)
    elif raw_msg["type"] == "TempMessage":
        if reply is None:
            reply = False
        if reply:
            if quote is None:
                quote = raw_msg["messageChain"][0]["id"]
            send_temp_message1(raw_msg["sender"]["id"], raw_msg["sender"]["group"]["id"], message, quote=quote)
        else:
            send_temp_message1(raw_msg["sender"]["id"], raw_msg["sender"]["group"]["id"], message)


def send_auto_image1(raw_msg, image_url, quote=None, do_reply=None):
    if raw_msg["type"] == "GroupMessage":
        if do_reply is None:
            do_reply = True
        if do_reply:
            if quote is None:
                quote = raw_msg["messageChain"][0]["id"]
            send_group_image1(raw_msg["sender"]["group"]["id"], image_url, quote=quote)
        else:
            send_group_image1(raw_msg["sender"]["group"]["id"], image_url)
    elif raw_msg["type"] == "FriendMessage":
        if do_reply is None:
            do_reply = False
        if do_reply:
            if quote is None:
                quote = raw_msg["messageChain"][0]["id"]
            send_friend_image1(raw_msg["sender"]["id"], image_url, quote=quote)
        else:
            send_friend_image1(raw_msg["sender"]["id"], image_url)
    elif raw_msg["type"] == "TempMessage":
        if do_reply is None:
            do_reply = False
        if do_reply:
            if quote is None:
                quote = raw_msg["messageChain"][0]["id"]
            send_temp_image1(raw_msg["sender"]["id"], raw_msg["sender"]["group"]["id"], image_url, quote=quote)
        else:
            send_temp_image1(raw_msg["sender"]["id"], raw_msg["sender"]["group"]["id"], image_url)


def send_auto_mixed(raw_msg, message_chain, quote=None, reply=None):
    if raw_msg["type"] == "GroupMessage":
        if reply is None:
            reply = True
        if reply:
            if quote is None:
                quote = raw_msg["messageChain"][0]["id"]
            send_group_mixed_wpd(raw_msg["sender"]["group"]["id"], message_chain,
                                 quote=quote)
        else:
            send_group_mixed_wpd(raw_msg["sender"]["group"]["id"], message_chain)
    elif raw_msg["type"] == "FriendMessage":
        if reply is None:
            reply = False
        if reply:
            if quote is None:
                quote = raw_msg["messageChain"][0]["id"]
            send_friend_mixed(raw_msg["sender"]["id"], message_chain, quote=quote)
        else:
            send_friend_mixed(raw_msg["sender"]["id"], message_chain)
    elif raw_msg["type"] == "TempMessage":
        if reply is None:
            reply = False
        if reply:
            if quote is None:
                quote = raw_msg["messageChain"][0]["id"]
            send_temp_mixed(raw_msg["sender"]["id"], raw_msg["sender"]["group"]["id"], message_chain,
                            quote=quote)
        else:
            send_temp_mixed(raw_msg["sender"]["id"], raw_msg["sender"]["group"]["id"], message_chain)


action_while_list = []
action_black_list = []
action_mode = 0  # 0: none, 1: white, 2: black

img_database = {"AtAll": "data/img/at_all.jpg"}

"""Load command prompt"""
get_rules("cmd_prompt", default="e*")


@safe_run
def check_list(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if check_list_(args[0]):
            return func(*args, **kwargs)
        else:
            return 0

    def check_list_(msg):
        if action_mode == 0:
            return True
        sender_id = 0
        if msg["type"] == "FriendMessage":
            sender_id = msg["sender"]["id"]
        elif msg["type"] == "GroupMessage":
            sender_id = msg["sender"]["group"]["id"]
        if action_mode == 1:
            if sender_id in action_while_list:
                return True
            else:
                return False
        elif action_mode == 2:
            if sender_id in action_black_list:
                return False
            else:
                return True

    return wrapper


@safe_run
def check_message(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if "Message" in args[0]["type"]:
                return func(*args, **kwargs)
            else:
                return None
        except Exception as error:
            return error

    return wrapper


@safe_run
def group_message_only(silent=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if "GroupMessage" == args[0]["type"]:
                    return func(*args, **kwargs)
                else:
                    if not silent:
                        send_auto_message1(args[0], "本功能仅限群聊使用")
                    return None
            except Exception as error:
                return error

        return wrapper

    return decorator


@safe_run
def private_message_only(silent=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if args[0]["type"] in ["FriendMessage", "TempMessage", "StrangerMessage"]:
                    return func(*args, **kwargs)
                else:
                    if not silent:
                        send_auto_message1(args[0], "本功能仅限私聊使用")
                    return None
            except Exception as error:
                return error

        return wrapper

    return decorator


@safe_run
def permission_op(func):
    # noinspection PyTypeChecker
    @wraps(func)
    def wrapper(raw_msg):
        try:
            ensure_rule_index("permission", "op", )
            if raw_msg["sender"]["id"] in get_rules("permission", "op", default=[]):
                return func(raw_msg)
            else:
                if raw_msg["sender"]["id"] in get_rules("permission", "zb", default=[]):
                    send_auto_message1(raw_msg, "什么铸币")
                else:
                    send_auto_message1(raw_msg, "你没有权限进行此操作")
        except Exception as error:
            error_message(error)
        return None

    return wrapper


@safe_run
def permission_admin(func):
    # noinspection PyTypeChecker
    @wraps(func)
    def wrapper(raw_msg):
        try:
            if raw_msg["sender"]["id"] in get_rules("permission", "admin", default=[]) + get_rules("permission", "op",
                                                                                                   default=[]):
                return func(raw_msg)
            else:
                ensure_rule_index("permission", "zb")
                if raw_msg["sender"]["id"] in get_rules("permission", "zb", default=[]):
                    send_auto_message1(raw_msg, "什么铸币")
                else:
                    send_auto_message1(raw_msg, "你没有权限进行此操作")
        except Exception as error:
            error_message(error)
        return None

    return wrapper


@safe_run
def permission_zb(func):
    # noinspection PyTypeChecker
    @wraps(func)
    def wrapper(raw_msg):
        try:
            if raw_msg["sender"]["id"] in get_rules("permission", "zb", default=[]):
                return func(raw_msg)
            else:
                return None
        except Exception as error:
            return error_message(error)

    return wrapper


@safe_run
def permission(*perm, silent=False):
    def decorator(func):
        # noinspection PyTypeChecker,PyUnresolvedReferences
        @wraps(func)
        def wrapper(raw_msg):
            try:
                if type(perm[0]) == list:
                    pmt_list = perm[0]
                else:
                    pmt_list = perm
                perm_list = get_rules("permission", "op", safe=True, default=[]) + get_rules("permission", "admin",
                                                                                             safe=True, default=[])
                for pmt in pmt_list:
                    perm_list += get_rules("permission", pmt, default=[], safe=True)
                if raw_msg["sender"]["id"] in perm_list:
                    return func(raw_msg)
                else:
                    if raw_msg["sender"]["id"] in get_rules("permission", "zb", default=[]):
                        if not silent:
                            send_auto_message1(raw_msg, "什么铸币")
                    else:
                        if not silent:
                            send_auto_message1(raw_msg, "你没有权限进行此操作")
            except Exception as error:
                error_message(error)
            return None

        return wrapper

    return decorator


@safe_run
def exact_permission(*perm, deop=False, silent=False):
    def decorator(func):
        # noinspection PyTypeChecker,PyUnresolvedReferences
        @wraps(func)
        @safe_run
        def wrapper(raw_msg):
            try:
                if type(perm[0]) == list:
                    pmt_list = perm[0]
                else:
                    pmt_list = perm
                if deop:
                    perm_list = []
                else:
                    perm_list = get_rules("permission", "op", default=[], safe=True)
                for pmt in pmt_list:
                    perm_list += get_rules("permission", pmt, default=[], safe=True)
                if raw_msg["sender"]["id"] in perm_list:
                    return func(raw_msg)
                else:
                    ensure_rule_index("permission", "zb")
                    if raw_msg["sender"]["id"] in get_rules("permission", "zb", default=[]):
                        if not silent:
                            send_auto_message1(raw_msg, "什么铸币")
                    else:
                        if not silent:
                            send_auto_message1(raw_msg, "你没有权限进行此操作")
            except Exception as error:
                return error_message(error)

        return wrapper

    return decorator


@safe_run
def restricted_scope(qq_id_list=None, group_id_list=None, silent=False):
    def decorator(func):
        # noinspection PyTypeChecker,PyUnresolvedReferences
        @wraps(func)
        @safe_run
        def wrapper(raw_msg):
            try:
                if qq_id_list is not None and raw_msg["sender"]["id"] not in qq_id_list:
                    if not silent:
                        send_auto_message1(raw_msg, "此功能不对你开放")
                    return None
                elif group_id_list is not None and raw_msg["type"] not in ["FriendMessage", "StrangerMessage"] and \
                        raw_msg["sender"]["group"]["id"] not in group_id_list:
                    if not silent:
                        send_auto_message1(raw_msg, "此功能不对本群开放")
                    return None
                else:
                    return func(raw_msg)
            except Exception as error:
                return error_message(error)

        return wrapper

    return decorator


@safe_run
def punctuation_mend(string):
    # 输入字符串或者txt文件路径
    table = {ord(f): ord(t) for f, t in zip(
        u'，、。！？【】（）％＃＠＆１２３４５６７８９０“”‘’',
        u',,.!?[]()%#@&1234567890""\'\'')}  # 其他自定义需要修改的符号可以加到这里
    res = unicodedata.normalize('NFKC', string)
    res = res.translate(table)
    re.sub(r'(?<=[.,])(?=\S)', r' ', res)
    res = res.replace(" ", "")
    return res.lower().strip()


@safe_run
def extract_text(raw_msg):
    text = ""
    for msg in raw_msg["messageChain"]:
        if msg["type"] == "Plain":
            text += msg["text"]
    return text


@safe_run
def extract_at(raw_msg):
    """
    获取@的人的id
    :param raw_msg:
    :return: at_list
    """
    at_list = []
    for msg in raw_msg["messageChain"]:
        if msg["type"] == "At":
            at_list.append(msg["target"])
    return at_list


@safe_run
def extract_quote(raw_msg):
    """
    获取引用的消息id
    :param raw_msg:
    :return: quote_list
    """
    quote_list = []
    for msg in raw_msg["messageChain"]:
        if msg["type"] == "Quote":
            quote_list.append(msg["id"])
    return quote_list


@safe_run
def extract_image(raw_msg):
    image_list = []
    for msg in raw_msg["messageChain"]:
        if msg["type"] == "Image":
            image_list.append(msg["url"])
    return image_list


@safe_run
def match_target(raw_msg, target, threshold):
    sim = ts.string_similar(punctuation_mend(extract_text(raw_msg)), punctuation_mend(target))
    if sim >= threshold:
        return True
    else:
        return False


@safe_run
def find_keyword(raw_msg, keyword, except_keyword_list=None, max_cmp_len=0):
    def find_keyword_sub(raw_msg_, keyword_, except_keyword_list_=None, max_cmp_len_=0):
        if except_keyword_list_ is None:
            except_keyword_list_ = []
        text = punctuation_mend(extract_text(raw_msg_))
        if text == "":
            return False
        keyword_ = punctuation_mend(keyword_)
        if max_cmp_len_ == -1:
            max_cmp_len_ = len(keyword_)
        if 0 < max_cmp_len_ < len(text):
            return False
        for except_keyword in except_keyword_list_:
            if except_keyword in text:
                return False
        if keyword_ in text:
            return True
        return False

    if type(keyword) == list:
        for keyword0 in keyword:
            if find_keyword_sub(raw_msg, keyword0, except_keyword_list, max_cmp_len):
                return True
        return False
    elif type(keyword) == str:
        return find_keyword_sub(raw_msg, keyword, except_keyword_list_=None, max_cmp_len_=0)


@safe_run
def rel_path_to_url(path):
    return "file:///" + os.path.join(sys.path[0], path)


def get_scopes(*scope):
    if type(scope[0]) == list:
        scope = scope[0]
    ret = set()
    for s in scope:
        scopes = get_rules("scope", s, default=[])
        for sc in scopes:
            ret.add(sc)
    return tuple(ret)
