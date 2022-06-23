from .generate_license_plate import LicensePlateGenerator
import random
import hashlib
import os
import threading


def str_md5(target):
    m = hashlib.md5()
    m.update(target.encode('utf-8'))
    return m.hexdigest()


used_file_path = "./config/used_plate.txt.rd"


used_file_lock = threading.Lock()


def generate_license_plate_image(plate_number, save_path, vertical=True):
    used_file_lock.acquire()
    with open(used_file_path, 'a') as f:
        f.write(str_md5(plate_number) + "\n")
    used_file_lock.release()
    return LicensePlateGenerator.generate_certain_license_plate_images('single_blue', plate_number, save_path, vertical)


def random_plate_number(check_used=True):
    used_plate_number = []
    if check_used:
        used_file_lock.acquire()
        if os.path.exists(used_file_path):
            with open(used_file_path, 'r') as f:
                used_plate_number = f.read().splitlines()
        else:
            with open(used_file_path, 'w') as f:
                f.write("")
        used_file_lock.release()
    nonexistent_prefix = [chr(i) for i in range(75, 91)]
    nonexistent_prefix.remove('W')
    plate_number = "藏" + random.choice(nonexistent_prefix) + str(random.randint(1, 99999)).zfill(5)
    cd = 100
    while plate_number in used_plate_number:
        nonexistent_prefix = [chr(i) for i in range(75, 91)]
        plate_number = "藏" + random.choice(nonexistent_prefix) + str(random.randint(1, 99999)).zfill(5)
        cd -= 1
        if cd == 0:
            return None
    return plate_number


def clear_history():
    with open(used_file_path, 'w') as f:
        f.write("")


if __name__ == '__main__':
    print(random_plate_number())
