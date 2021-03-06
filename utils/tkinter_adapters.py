from PIL import Image, ImageTk
from skimage.transform import resize
import platform

def get_viewable_image(source):
    image = Image.fromarray(source)
    image = ImageTk.PhotoImage(image)
    return image

def toolbar_sized(source, width=75, height=75):
    resized = source.copy()
    resize(resized, (width, height), order=1, mode='reflect', cval=0, clip=True,
           preserve_range=False, anti_aliasing=True, anti_aliasing_sigma=None)
    return resized

def generate_output_from_canvas(canvas, fileName):
    canvas.postscript(file=fileName + '.eps')
    img = Image.open(fileName + '.eps')
    img.save(fileName + '.png', 'png')

def scroll_view(view, event):
    if event.state: # left - right
        view.xview_scroll(get_delta(event), "units")
    else: # up - down
        view.yview_scroll(get_delta(event), "units")

def get_delta(event):
    if platform.system() == 'Windows':
        return -1 * event.delta / 120
    if platform.system() == 'Linux':
        if event.num == 4:
            return -1
        elif event.num == 5:
            return 1
    return -1 * event.delta

