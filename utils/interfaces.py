import numpy as np
import cv2
from PIL import Image

class LetterImage:
    def __init__(self, original, contours, modified, rotation=0, scale=1):
        if modified is None:
            modified = original
        self.original = original
        self.rotation = rotation
        self.scale = scale
        self.contours = contours
        self.modified = modified
        self.first_time_source = None
        self.first_time_iteration = None

    def convert_to_red(self):
        r1, g1, b1 = 0, 0, 0  # Original value
        r2, g2, b2 = 255, 0, 0  # Value that we want to replace it with
        data = self.modified
        red, green, blue = data[:, :, 0], data[:, :, 1], data[:, :, 2]
        mask = True
        data[:, :, :3][mask] = [r2, g2, b2]
        self.modified = data

    def resize_img(self,iteration,old_zoom_cycle):
        scaling = 1.1
        if self.first_time_source is None:
            self.first_time_source = self.modified
            self.first_time_cycle = old_zoom_cycle
        ih, iw, temp = self.first_time_source.shape
        #iteration = current zoom, first_time_cycle =old zoom
        alpha = iteration - self.first_time_cycle
        abs_alpha = abs(alpha)
        print(alpha)
        if alpha > 0:
            size = (int(iw * (scaling**abs_alpha)), int(ih * (scaling**abs_alpha)))
            self.modified = cv2.resize(self.first_time_source, size,interpolation=cv2.INTER_LINEAR)
        elif alpha < 0:
            size = (int(iw / (scaling**abs_alpha)), int(ih / (scaling**abs_alpha)))
            self.modified = cv2.resize(self.first_time_source, size, interpolation=cv2.INTER_AREA)
        else:
            self.modified = self.first_time_source

        print(self.modified.shape)

class TextImage:
    def __init__(self, original, segmented):
        self.original = original
        self.segmented = segmented

    def get_size(self):
        ih, iw, ch = self.original.shape
        return ih, iw

    def get(self):
        return self.original

class SnakesParams:
    def __init__(self, iterations, expand, fill):
        self.iterations = iterations
        self.expand = expand
        self.fill = fill
