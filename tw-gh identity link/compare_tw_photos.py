import cv2
import os

# reference: https://my.oschina.net/u/4399904/blog/4237625


def calculate(image1, image2):
    hist1 = cv2.calcHist([image1], [0], None, [256], [0.0, 255.0])
    hist2 = cv2.calcHist([image2], [0], None, [256], [0.0, 255.0])
    degree = 0
    for i in range(len(hist1)):
        if hist1[i] != hist2[i]:
            degree = degree + \
                (1 - abs(hist1[i] - hist2[i]) / max(hist1[i], hist2[i]))
        else:
            degree = degree + 1
    degree = degree / len(hist1)
    return degree



def get_img_similarity(image1, image2, size = (256, 256)):
    try:
        image1_resized = cv2.resize(image1, size)
        image2_resized = cv2.resize(image2, size)
        sub_image1 = cv2.split(image1_resized)
        sub_image2 = cv2.split(image2_resized)
        sub_data = 0
        for im1, im2 in zip(sub_image1, sub_image2):
            sub_data += calculate(im1, im2)
        sub_data = sub_data / 3
    except:
        print(size)
        print(image1.shape)
        print(image2.shape)
        print(image1_resized.shape)
        print(image2_resized.shape)

        exit()
    return sub_data

