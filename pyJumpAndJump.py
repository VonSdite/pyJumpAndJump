# -*- coding: utf-8 -*-
# __Author__: Sdite
# __Email__ : a122691411@gmail.com

import os
import time
import pickle
import queue
from PIL import Image, ImageDraw
from math import sqrt

# 测试手机红米4a 分辨率720*1280

# 保存截图的文件夹
SCREEN_SHOT_PATH = 'screenshot/'
if not os.path.isdir(SCREEN_SHOT_PATH):
    os.mkdir(SCREEN_SHOT_PATH)

# 小人最下方的线到小人底盘中心的偏移值
# 可能需要修正， 待观察
DEVIATION = 13

# 分数板的最低位置
SCORE_MAX_UNDERLINE = 192

# 每次跳跃的角度的tan值
TAN = 0.58278145695364238410596026490066
# tan = (742-566)/(526-224)

# 小人的宽度
LITTLE_MAN_WIDTH = 52

# 按压的位置，为开始游戏的位置
PRESS_X1, PRESS_Y1, PRESS_X2, PRESS_Y2 = (300, 1010, 400, 1010)

PRESS_X_OFFSET = 2.15879      # 按压时间系数, 需要更改，可以自己慢慢微调

# 调用安卓adb截图并获取截图
def pull_screenshot(mission):
    # 截图保存在sd卡中的命名
    img_path = '/sdcard/{}.png'.format(mission)

    # adb截图
    os.system('adb shell screencap -p {}'.format(img_path))

    # adb拉取截图到'screenshot'目录
    os.system('adb pull {} {}'.format(img_path, SCREEN_SHOT_PATH))


# 寻找小人的底盘中心点
def find_little_man_center(im):
    width, height = im.size

    center_x_sum = 0
    center_x_count = 0
    center_y_max = 0
    center_x = 0
    center_y = 0

    # 通过观察，小人最下方底盘是一条直线
    # 由此来找出小人底盘的中心
    # 从分数板下方高度开始遍历，减掉部分循环，提高效率
    for y in range(SCORE_MAX_UNDERLINE, height):
        for x in range(width):
            pixel = im.getpixel((x, y))
            # 根据底边像素值得到的区间
            if (50 < pixel[0] < 59) and (55 < pixel[1] < 63) and (94 < pixel[2] < 102):
                center_x_sum += x
                center_x_count += 1
                center_y_max = y

    if center_x_count == 0 or center_x_sum == 0:
        return 0, 0

    # 求出小人的中心
    center_x = center_x_sum // center_x_count
    center_y = center_y_max - DEVIATION

    # 将小人中心标记出来
    im.putpixel((center_x, center_y), (255, 0, 0))

    return center_x, center_y


# 寻找要跳到的中心位置
def find_target(im, center_x, center_y):
    width, height = im.size

    # 要跳到的中心点在 小人底盘上方和分数板下方
    # 先找出要跳到的中心点的x坐标
    target_x_sum = 0
    target_x_count = 0
    target_x = 0
    target_y = 0

    for y in range(SCORE_MAX_UNDERLINE, center_y):
        tmp = im.getpixel((0, y))  # 作为参考值
        for x in range(width):
            # 距离小人底盘中心小于小人宽度的跳过
            if abs(x - center_x) < LITTLE_MAN_WIDTH:
                continue

            pixel = im.getpixel((x, y))
            if abs(pixel[0] - tmp[0]) + abs(pixel[1] - tmp[1]) + abs(pixel[2] - tmp[2]) > 10:
                target_x_sum += x
                target_x_count += 1

        if target_x_sum != 0 and target_x_count != 0:
            target_x = target_x_sum // target_x_count
            break

    if target_x_sum == 0 and target_x_count == 0:
        return 0, 0

    target_y = int(center_y - TAN * abs(target_x - center_x))

    # 将要跳到的目标点标记出来
    im.putpixel((target_x, target_y), (255, 0, 0))

    return target_x, target_y


# 绘制小人跳的路径
def draw_line(im, center_x, center_y, target_x, target_y, mission):
    draw = ImageDraw.Draw(im)
    draw.line((center_x, center_y) + (target_x, target_y), fill=2, width=3)
    del draw
    im.save('{}{}.png'.format(SCREEN_SHOT_PATH, mission))


# 跳！
def jump(distance):
    if distance == 0:
        # 为0表示游戏没开始，就点击一下开始
        cmd = 'adb shell input tap {} {}'.format(PRESS_X1, PRESS_Y1)
    else:
        press_time = distance * PRESS_X_OFFSET
        press_time = max(press_time, 200)  # 设置 200 ms 是最小的按压时间
        press_time = int(press_time)
        # print(press_time)
        cmd = 'adb shell input swipe {} {} {} {} {}'.format(PRESS_X1, PRESS_Y1, PRESS_X2,
                                                            PRESS_Y2, press_time)
        print('press: {}ms  distance: {}px'.format(press_time, distance))
    os.system(cmd)


def run():
    mission = 1
    while True:
        pull_screenshot(mission)  # 截图并拉取图片

        im = Image.open('{}{}.png'.format(SCREEN_SHOT_PATH, mission))  # 打开图片
        # 因为pycharm PIL库不自动补全，加这句就可以了
        assert isinstance(im, Image.Image)

        center_x, center_y = find_little_man_center(im)  # 获取小人底盘中心
        target_x, target_y = find_target(im, center_x, center_y)  # 获取要跳到的目标位置
        jump(sqrt((center_x - target_x) ** 2 + (center_y - target_y) ** 2))  # 跳

        draw_line(im, center_x, center_y, target_x, target_y, mission)  # 绘制要跳跃的路径

        mission += 1

        time.sleep(1)


if __name__ == '__main__':
    run()
