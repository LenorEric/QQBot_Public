import cv2
import numpy as np
import scipy.signal

__all__ = ['threshold_process']


def white2transparent(img):
    height, width, channel = img.shape
    for h in range(height):
        for w in range(width):
            if img[h, w, 0] == 255:
                img[h, w, 3] = 0
    return img


def gray2transparent(img, lower, threshold1, upper, threshold2, tp_bg=False):
    def trans(x):
        if x < threshold1:
            return int(k1 * x + b1)
        else:
            return int(k2 * x + b2)

    k1 = upper / (threshold1 - lower)
    b1 = - k1 * lower
    k2 = (255 - upper) / (threshold2 - threshold1)
    b2 = 255 - k2 * threshold2
    height, width, channel = img.shape
    for h in range(height):
        for w in range(width):
            if img[h, w, 0] == 255:
                if tp_bg:
                    img[h, w] = [255, 255, 255, 0]
            else:
                if tp_bg:
                    img[h, w] = [0, 0, 0, 255 - trans(img[h, w, 0])]
                else:
                    t = trans(img[h, w, 0])
                    img[h, w] = [t, t, t, 255]
    return img


def find_near(array, start, end):
    begin = array[start]
    up = start
    state = begin > end
    while up < len(array) and (array[up] > end) == state:
        up += 1
    return up


def threshold_process(img_path, save_path, fix=0.65, preview=True, tp_bg=None):
    if tp_bg is None:
        tp_bg = not preview
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if preview or img.shape[0] < 300:
        w = 300 * img.shape[1] // img.shape[0]
        img = cv2.resize(img, (w, 300))
    elif max(img.shape) > 1080:
        w = 1000 * img.shape[1] // img.shape[0]
        img = cv2.resize(img, (w, 1080))
    img_data = img.reshape(-1)
    gray_num = np.bincount(img_data, minlength=256)
    indexes = []
    distance_h = 256
    distance_l = 0
    while len(indexes) != 2:
        indexes, _ = scipy.signal.find_peaks(gray_num, distance=(distance_h + distance_l) // 2)
        if len(indexes) < 2:
            distance_h = (distance_h + distance_l) // 2
        elif len(indexes) > 2:
            distance_l = (distance_h + distance_l) // 2
    threshold2 = int((indexes[0] + indexes[1]) * fix)
    img[img > threshold2] = 255
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    threshold1 = find_near(gray_num, indexes[0], gray_num[indexes[0]] * 0.5 + threshold2 * 0.5)
    img = gray2transparent(img, np.min(img), threshold1, 10, threshold2, tp_bg=tp_bg)
    cv2.imwrite(save_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 5])
    return save_path


def threshold_process_old(img_path, save_path, fix=0.65, preview=True):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if preview:
        w = 300 * img.shape[1] // img.shape[0]
        img = cv2.resize(img, (w, 300))
    img_data = img.reshape(-1)
    gray_num = np.bincount(img_data, minlength=256)
    indexes = []
    distance_h = 256
    distance_l = 0
    while len(indexes) != 2:
        indexes, _ = scipy.signal.find_peaks(gray_num, distance=(distance_h + distance_l) // 2)
        if len(indexes) < 2:
            distance_h = (distance_h + distance_l) // 2
        elif len(indexes) > 2:
            distance_l = (distance_h + distance_l) // 2
    threshold = (indexes[0] + indexes[1]) * fix
    if threshold > 255:
        threshold = 255
    ret, img = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    blur_size = min(img.shape) // 250
    if blur_size % 2 == 0:
        blur_size += 1
    img = cv2.GaussianBlur(img, (blur_size, blur_size), 0.3 * (((blur_size - 1) * 0.5) - 1) + 0.8)
    if not preview:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        img = white2transparent(img)
    cv2.imwrite(save_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 8])
    return save_path


if __name__ == '__main__':
    pass
