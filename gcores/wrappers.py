import threading
from functools import wraps
from gcores.logger import *

__all__ = ["safe_run", "lock_run"]


def safe_run(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            error_message(error, ", Error in:", func.__name__)
            return None

    return wrapper


wrapper_lock = threading.Lock()


def lock_run(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        wrapper_lock.acquire()
        ret = func(*args, **kwargs)
        wrapper_lock.release()
        return ret

    return wrapper
