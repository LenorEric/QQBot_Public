import difflib
import os
import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from xpinyin import Pinyin

__all__ = ["string_similar", "advanced_string_similar", "kmp_using_ass"]


def mlp(suffix):
    return os.path.join(os.path.dirname(__file__), suffix)


def get_pinyin(string):
    return Pinyin().get_pinyin(string, "")


def string_similar(s1, s2):
    return difflib.SequenceMatcher(None, s1, s2).quick_ratio()


font_ch = ImageFont.truetype(mlp("./unifont.ttf"), 80, 0)


def generate_char_image(char):
    """ 生成字符图片
    :param char: 字符
    :return:
    """
    img = Image.new("RGB", (80 * len(char), 140), (255, 255, 255))
    ImageDraw.Draw(img).text((0, 32), char, (0, 0, 0), font=font_ch)
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def img_similar(img1, img2):
    """
    :param img1:
    :param img2:
    :return:
    """

    def cmp_hash(hash1, hash2, shape=(10, 10)):
        n = 0
        # hash长度不同则返回-1代表传参出错
        if len(hash1) != len(hash2):
            return -1
        # 遍历判断
        for i in range(len(hash1)):
            # 相等则n计数+1，n最终为相似度
            if hash1[i] == hash2[i]:
                n = n + 1
        return n / (shape[0] * shape[1])

    # 感知哈希算法(pHash)
    def p_hash(img, shape=(10, 10)):
        # 缩放32*32
        img = cv2.resize(img, (32, 32))  # , interpolation=cv2.INTER_CUBIC

        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 将灰度图转为浮点型，再进行dct变换
        dct = cv2.dct(np.float32(gray))
        # opencv实现的掩码操作
        dct_roi = dct[0:10, 0:10]
        hash_list = []
        average = np.mean(dct_roi)
        for i in range(dct_roi.shape[0]):
            for j in range(dct_roi.shape[1]):
                if dct_roi[i, j] > average:
                    hash_list.append(1)
                else:
                    hash_list.append(0)
        return hash_list

    hash1 = p_hash(img1)
    hash2 = p_hash(img2)
    return cmp_hash(hash1, hash2)


def advanced_string_similar(s1, s2):
    """

    :param s1:
    :param s2:
    :return: True / False
    """
    a2z = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for s_1, s_2 in zip(s1, s2):
        if s_1 in a2z and s_2 in a2z:
            if s_1 != s_2:
                return False
        s1_py = get_pinyin(s_1)
        s2_py = get_pinyin(s_2)
        img1 = generate_char_image(s_1)
        img2 = generate_char_image(s_2)
        if img_similar(img1, img2) < 0.8 and string_similar(s1_py, s2_py) < 0.9:
            return False
    return True


def kmp_using_ass(mom_string, son_string):
    # 传入一个母串和一个子串
    # 返回子串匹配上的第一个位置，若没有匹配上返回-1
    test = ''
    if type(mom_string) != type(test) or type(son_string) != type(test):
        return -1
    if len(son_string) == 0:
        return 0
    if len(mom_string) == 0:
        return -1
    # 求next数组
    next_ = [-1] * len(son_string)
    if len(son_string) > 1:  # 这里加if是怕列表越界
        next_[1] = 0
        i, j = 1, 0
        while i < len(son_string) - 1:  # 这里一定要-1，不然会像例子中出现next[8]会越界的
            if j == -1 or advanced_string_similar(son_string[i], son_string[j]):
                i += 1
                j += 1
                next_[i] = j
            else:
                j = next_[j]
    # kmp框架
    m = s = 0  # 母指针和子指针初始化为0
    while s < len(son_string) and m < len(mom_string):
        # 匹配成功,或者遍历完母串匹配失败退出
        if s == -1 or advanced_string_similar(mom_string[m], son_string[s]):
            m += 1
            s += 1
        else:
            s = next_[s]
    if s == len(son_string):  # 匹配成功
        return m - s
    # 匹配失败
    return -1


if __name__ == '__main__':
    print(kmp_using_ass("翔哥是大卷王", "劵王"))
