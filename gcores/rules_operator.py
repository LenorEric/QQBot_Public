import threading
import os
import json
import copy
from gcores.logger import *
from gcores.wrappers import *

__all__ = ["reload_rules", "get_rules", "set_rules", "save_rules", "ensure_rule_index"]

rules_file = "config/rules.json.rd"
rules_lock = threading.Lock()

rules = {}


@safe_run
def save_rules():
    if rules is None:
        return
    rules_lock.acquire()
    with open(rules_file, 'w', encoding="utf-8") as rule_file:
        rule_file.write(json.dumps(rules, indent=4, ensure_ascii=False))
    rules_lock.release()


@safe_run
def reload_rules(save=True):
    global rules
    rules_lock.acquire()
    if os.path.exists(rules_file):
        with open(rules_file, "r", encoding="utf-8") as file:
            rules_ = file.read()
            rules_ = json.loads(rules_)
    else:
        general_message("Warning", "Rules file not found, creating new rules.")
        if not os.path.exists(os.path.dirname(rules_file)):
            os.mkdir(os.path.dirname(rules_file))
        with open(rules_file, "w", encoding="utf-8") as file:
            rules_ = {}
            json.dump(rules, file, ensure_ascii=False)
    rules_lock.release()
    rules = rules_
    if save:
        save_rules()
    return rules_


# noinspection PyRedeclaration
rules = reload_rules()


@safe_run
def ensure_rule_index(*args, save=False):
    global rules
    if len(args) == 0:
        general_message("Fail", "No index given")
        return
    elif type(args[0]) == list:
        args = args[0]
    rules_lock.acquire()
    it = rules
    for index in args:
        if it is None:
            it = {}
        try:
            it = it[str(index)]
        except:
            it[str(index)] = {}
            it = it[str(index)]
    rules_lock.release()
    if save:
        save_rules()


@safe_run
def get_rules(*args, default=None, save_default=None, ensure=True, safe=False):
    if default is not None and save_default is None:
        save_default = [True, True]
    else:
        save_default = [False, False]
    if default is None:
        default = {}
    if ensure:
        ensure_rule_index(*args)
    rules_lock.acquire()
    it = rules
    for index in args:
        it = it[str(index)]
    rules_lock.release()
    if it == {} and args:
        it = default
        if save_default[0]:
            set_rules(default, *args, save=save_default[1])
    if safe:
        return copy.deepcopy(it)
    else:
        return it


@safe_run
def set_rules(value, *args, save=True, safe=False, ensure=True):
    if ensure:
        ensure_rule_index(*args)
    rules_lock.acquire()
    it = rules
    for index in args[:-1]:
        it = it[str(index)]
    it[str(args[-1])] = value
    rules_lock.release()
    if save:
        save_rules()
    it = it[args[-1]]
    if safe:
        return copy.deepcopy(it)
    else:
        return it
