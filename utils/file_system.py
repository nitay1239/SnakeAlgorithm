import numpy as np
from skimage.io import imread, show, imshow, imsave
from tkinter import filedialog
import json

image_file_types = (
    ("TIFF Files", '*.tif'),
    ("PNG Files", '*.png'),
    ("JPEG Files", '*.jpeg;*.jpg;*.jpe'),
    ("GIF Files", '*.gif'),
    ("all files", "*.*"))

def get_letter_image_from_file(file_name):
    image = get_image_from_file(file_name)
    mask = np.zeros(
        (image.shape[0], image.shape[1]), dtype=np.bool)
    mask[np.where((image == [0, 0, 0, 255]).all(axis=-1))] = 1
    return mask

def get_letter_image_from_edit_canvas(image):
    mask = np.zeros(
        (image.shape[0], image.shape[1]), dtype=np.bool)
    mask[np.where((image == [0, 0, 0, 255]).all(axis=-1))] = 1
    return mask


def get_image_from_file(file_name):
    return imread(file_name)


def select_image_file():
    path = filedialog.askopenfilename(
        filetypes=image_file_types, initialdir="input")
    if len(path) > 0:
        input_image = imread(path)
        return input_image


def save_image_to_file(image):
    path = filedialog.asksaveasfilename(filetypes=image_file_types,
                                        defaultextension='.tif',
                                        initialdir="output",)
    imsave(path, image)


def save_contours_to_file(contours):
    path = filedialog.asksaveasfilename(filetypes=[("JSON Files", '*.json')],
                                        defaultextension='.json',
                                        initialdir="output",)
    with open(path, 'w') as outfile:
        json.dump(contours, outfile)
