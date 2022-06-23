import os
import sys


def force_cover_local_code():
    os.system("git fetch --all")
    os.system("git reset --hard origin/main")
    os.system("git merge origin/main")


if __name__ == '__main__':
    force_cover_local_code()
    argv_add = [os.path.join(os.path.dirname(sys.argv[0]), "main.py")] + sys.argv[1:]
    os.execl(sys.executable, sys.executable, *argv_add)
