# -*- coding: utf-8 -*-
"""

"""
import os

import imageio


def make_gif(path, gif_path, fps):
    images = []
    for root, dirs, files in os.walk(gif_path):
        for file in files:
            images.append(os.path.join(root, file))

    ids = [int(image.split('_')[-1].split('.')[0]) for image in images]

    images_ids = zip(ids, images)
    # x[0]按ids排序，x[1]按images排序，(x[0],x[1])表示先按ids再按images排序
    sorted_images_ids = sorted(images_ids, key=lambda x: x[0])
    result = zip(*sorted_images_ids)
    sorted_ids, sorted_images = [list(x) for x in result]

    gif_images = [imageio.v3.imread(image) for image in sorted_images]
    gif_name = gif_path.split(os.sep)[-1] + '.gif'
    imageio.mimsave(os.path.join(path, gif_name), gif_images, duration=1000*1/fps)


if __name__ == '__main__':
    path = r'H:\files\virtual\1'
    gif_path = r'H:\files\virtual\1\S11'
    make_gif(path, gif_path, 8)
