from skimage.filters import gaussian, threshold_otsu
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from matplotlib import path

from skimage.color import rgb2gray, gray2rgb
from skimage.filters import gaussian
from skimage.segmentation import active_contour
from skimage.feature import canny
from skimage.measure import find_contours
from skimage.transform import resize, rotate
from skimage.draw import polygon
from utils.interfaces import LetterImage, TextImage

def segment_image(source):
    segmented = rgb2gray(source)
    segmented = gaussian(segmented, 1)
    return segmented

def get_letter_contours(letter_mask) -> LetterImage:
    contours = find_contours(letter_mask, 0.3)
    filtered_contours = list(filter(lambda x: len(x) > 100, contours))
    sorted_contours = sorted(filtered_contours, key=lambda x: len(x))
    letter_image = np.zeros(
        (letter_mask.shape[0], letter_mask.shape[1], 4), dtype=np.uint8)
    letter_image = drawContours(
        letter_image, sorted_contours, [255, 0, 0, 255])
    return LetterImage(letter_mask, sorted_contours, letter_image)


def get_snakes(letter_image: LetterImage, text_image: TextImage, alpha=0.010, beta=20, gamma=0.0005, w_edge=1, max_iterations=4, expand=False, fill=False) -> LetterImage:
    if expand:
        w_line = 1
    else:
        w_line = -1

    mask = np.zeros(
        (text_image.segmented.shape[0], text_image.segmented.shape[1]), dtype=np.bool)
    snakes = []
    for letter_contour in letter_image.contours:
        init = letter_contour.copy()
        snake = active_contour(text_image.segmented, init, alpha=alpha, beta=beta, gamma=gamma,
                            w_edge=w_edge, w_line=w_line, max_iterations=max_iterations, coordinates='rc')
        snakes.append(snake)

    for snake in snakes:
        rr, cc = polygon(snake[ :, 0], snake[ :, 1], mask.shape)
        mask[rr, cc] = ~mask[rr, cc]

    # color = get_dominant_color_in_mask(text_image.original, mask)
    color = [104, 71, 41, 255]
    blank = np.zeros(
        (text_image.original.shape[0]+50, text_image.original.shape[1]+50, 4), dtype=np.uint8)
    if fill:
        blank[np.where(mask)] = [0,0,0,255]
    blank = drawContours(blank, snakes, [52, 35, 20, 255])
    return LetterImage(letter_image.original, snakes, blank)


def get_dominant_color_in_mask(image, mask):
    bounds = image
    avg_color_per_row = np.average(bounds, axis=0)
    avg_color = np.average(avg_color_per_row, axis=0)
    return avg_color

def drawContours(img, contours, color):
    for contour in contours:
        contour = contour.astype(int)
        img[contour[:, 0], contour[:, 1]] = color
    return img


def drawShapes(letter_image) -> LetterImage:
    modified = letter_image.modified
    mask = np.zeros(
        (modified.shape[0], modified.shape[1]), dtype=np.bool)
    color = [104, 71, 41, 255]

    for snake in letter_image.contours:
        rr, cc = polygon(snake[:, 0], snake[:, 1], mask.shape)
        mask[rr, cc] = ~mask[rr, cc]

    blank = np.zeros(
        (modified.shape[0], modified.shape[1], 4), dtype=np.uint8)
    blank[np.where(mask)] = color
    return LetterImage()


def lay_over(background_image, forground_image, top_left):
    x, y = top_left
    background_height, background_width, _ = background_image.shape
    forground_height, forground_width, forground_depth = forground_image.shape

    template = np.zeros((background_height, background_width, forground_depth))
    template[y: y + forground_height, x: x +
             forground_width, :] = forground_image

    mask = (template[:, :, 3])
    tmp_back = background_image.copy()
    tmp_back[np.where(mask)] = template[np.where(mask)]
    return tmp_back
