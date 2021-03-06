from skimage.transform import resize, rotate
import cv2
import sys
import numpy as np
from utils.interfaces import LetterImage
from utils.image_helpers import get_letter_contours

def rotate_letter(letter_image: LetterImage, angle) -> LetterImage:
    new_rotation = letter_image.rotation + angle
    letter_image.rotation = new_rotation
    return apply_modifiers(letter_image)

def resize_letter(letter_image: LetterImage, scale) -> LetterImage:
    new_scale_factor = letter_image.scale + scale
    letter_image.scale = new_scale_factor
    return apply_modifiers(letter_image)

    

def apply_modifiers(letter_image: LetterImage):    
    original = letter_image.original

    scale = letter_image.scale
    resized_shape = (int(original.shape[0] * scale),
                     int(original.shape[1] * scale))
    rotation = letter_image.rotation

    resized = resize(original, resized_shape, order=1, mode='reflect', cval=0, clip=True,
                    preserve_range=False, anti_aliasing=True, anti_aliasing_sigma=None)

    rotated = rotate(resized, rotation, resize=True, center=None,
                     order=1, mode='constant', cval=0, clip=True, preserve_range=False)

    modified_letter_image = get_letter_contours(rotated)

    modified_letter_image.rotation = rotation
    modified_letter_image.scale = scale
    modified_letter_image.original = original

    return modified_letter_image
