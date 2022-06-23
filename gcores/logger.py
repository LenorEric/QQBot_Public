import datetime
import threading
from functools import wraps

log_lock = threading.Lock()

__all__ = ["general_message", "trigger_message", "error_message", "log_message"]


def lock_for_print(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        log_lock.acquire()
        func(*args, **kwargs)
        log_lock.release()

    return wrapper


@lock_for_print
def general_message(event_type, *event, **kwargs):
    print("<", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ">", sep="", end="")
    print("[", event_type, "]: ", sep="", end="")
    print(*event, **kwargs)


@lock_for_print
def trigger_message(*event, **kwargs):
    print("<", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ">", sep="", end="")
    print("[Trigger]:", *event, **kwargs)


@lock_for_print
def error_message(*event, **kwargs):
    print("<", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ">", sep="", end="")
    print("[Error]:", *event, **kwargs)


@lock_for_print
def log_message(*event, **kwargs):
    print("<", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ">", sep="", end="")
    print("[Log]:", *event, **kwargs)
