import numpy as np
from tifffile import imsave
import random
import cv2
from matplotlib import pyplot as plt
from tkinter import OptionMenu, StringVar, LAST, Tk, messagebox, Button, Label, Frame, Canvas,Toplevel, Scrollbar, Menu
from tkinter.ttk import Button, Label, Scrollbar, Style
from PIL import Image, ImageTk
import ctypes
import sys
import os
from skimage.measure import find_contours
from utils.image_helpers import lay_over, get_snakes, segment_image, get_letter_contours
from components.scrollable_frame import ScrollableFrame
from components.output_canvas import OutputCanvas
from components.letter_fitness_control import LetterFitnessControl
from utils.interfaces import LetterImage, TextImage, SnakesParams
from utils.Deformater import deformat_img
from utils.letter_modifiers import rotate_letter, resize_letter
from utils.file_system import get_letter_image_from_file,get_letter_image_from_edit_canvas, get_image_from_file, select_image_file, save_image_to_file, save_contours_to_file
from utils.tkinter_adapters import get_viewable_image, toolbar_sized, generate_output_from_canvas, scroll_view

COLOR_GREY = '#393E41'
COLOR_DARKGREY = '#020202'
COLOR_DARKBLUE = '#011638'
COLOR_PASTEL = '#CDCDCD'
COLOR_WHITE = '#FCF7F8'

LETTERS_DIR = 'resources/letters'
CANVAS_WIDTH = 700
LETTER_SELECTION_SIZE = 75

class AnicentTextApp(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.attributes('-fullscreen', True)
        self.fullScreenState = True
        self.source_image = None
        self.source_image_copy = None
        self.selected_letter = None
        self.selected_letter_snake = None

        #editor-mode
        self.edit_win = None
        self.editor_mode = False
        self.edit_canvas = None
        self.edit_img = None
        self.edit_img_source = None
        self.edit_img_id = None
        self.background = None
        self.current_line = None
        self.first_x = None
        self.first_y = None
        self.second_x = None
        self.second_y = None
        self.interpolation = 0
        self.interpolations = []
        self.withSnake = True
        #editor-mode

        #zoom
        self.x = 0
        self.y = 0
        self.zoomcycle = 0
        self.scale = 1.0
        self.img = None
        #zoom

        self.snakes_params = SnakesParams(iterations=4, expand=False, fill=False)
        # GUI setup
        self.pack()
        self.create_widgets()
        # Controls
        self.bind_keyboard_events()
        
        if '-d' in sys.argv:
            self.debug = True
        else:
            self.debug = False

        for filename in sorted(os.listdir(LETTERS_DIR)):
            if filename.endswith(".tif"):
                path = LETTERS_DIR + '/' + filename
                charactar_image = get_letter_image_from_file(path)
                letter_image = get_letter_contours(charactar_image)
                #np.set_printoptions(threshold=sys.maxsize)
                self.add_selectable_letter_image(letter_image)

        if self.debug:
            print('DEBUG MODE IS ON')
            source_image = get_image_from_file('resources/test_text.tif')
            self.set_source_image(source_image)

    def on_mousewheel_callback(self, event):
        if not self.source_image or self.editor_mode:
             return
        old_scale = self.scale
        old_zoom_cycle = self.zoomcycle
        if event.delta > 0:
            if self.zoomcycle == 5:
                return
            else:
                self.zoomcycle += 1
                self.scale *= 1.05
        elif event.delta < 0:
            if self.zoomcycle == 0:
                return
            else:
                self.zoomcycle -= 1
                self.scale /= 1.05
        self.redraw(old_scale, old_zoom_cycle)

    def redraw(self, old_scale, old_zoom_cycle):
        height, width = self.source_image.original.shape[:2]
        self.output_image_view.delete('background')
        ih, iw = self.source_image_copy.get_size()
        cw, ch = iw * self.scale, ih * self.scale
        tmp = Image.fromarray(self.source_image_copy.get())
        size = (int(cw * self.scale), int(ch * self.scale))
        tmp = tmp.resize(size)
        self.set_source_image(np.asarray(tmp), False)
        # Moving + Scaling each of the letters
        height2, width2 = self.source_image.original.shape[:2]
        letters = self.output_image_view.find_withtag('letter')
        for letter in letters:
            #resize
            currLetterSource = self.output_image_view.letters_source[letter]

            currLetterSource.resize_img(self.zoomcycle, old_zoom_cycle)
            coords = self.output_image_view.coords(letter)

            # deleting old letter
            self.output_image_view.delete(letter)
            del self.output_image_view.letters[letter]
            del self.output_image_view.letters_source[letter]
            # check new coords

            left_top_coords = [(coords[0]*(self.scale/old_scale)*(self.scale/old_scale)),
                               (coords[1]*(self.scale/old_scale)*(self.scale/old_scale))]
            # adding new letter
            self.add_letter_image(currLetterSource, left_top_coords)




    def toggleFullScreen(self, event):
        self.fullScreenState = not self.fullScreenState
        self.master.attributes("-fullscreen", self.fullScreenState)

    def quitFullScreen(self, event):
        self.fullScreenState = False
        self.master.attributes("-fullscreen", self.fullScreenState)

    def create_widgets(self):
        # MENU:


        menubar = Menu(self.master)

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="open", command=self.pick_source_image)
        filemenu.add_separator()
        filemenu.add_command(label="save image as..",
                             command=self.generate_output)
        filemenu.add_separator()
        filemenu.add_command(label="save contours as..",
                             command=self.generate_contours_output)
        menubar.add_cascade(label="File", menu=filemenu)

        self.master.config(menu=menubar)

        side_menu = Frame(self.master)
        letter_fitness = LetterFitnessControl(side_menu)
        letter_fitness.pack(side='top', expand=True, fill='x')
        letter_selection_frame = self.get_letter_selection_frame(side_menu)
        letter_selection_frame.pack(
            expand=False, side="top", fill='both', anchor='e')
        side_menu.pack(side='right', fill='y', expand=True)

        main_section = Frame(self.master)
        
        output_frame = self.get_output_image_canvas(main_section)
        output_frame.pack(side='left', fill='both', expand=True, anchor='n')
        main_section.pack(side='left', fill='both', expand=True)

    def arrow_key_pressed(self, dir):
        if self.editor_mode:
            return
        if(self.selected_letter is not None):
            if dir == 'left':
                self.rotate_selected_letter('left')
            if dir == 'right':
                self.rotate_selected_letter('right')
            if dir == 'up':
                self.resize_selected_letter('up')
            if dir == 'down':
                self.resize_selected_letter('down')
        if(self.output_image_view.selected_letter is not None):
            if dir == 'left' :
                self.move_selected_placed_letter('left')
            if dir == 'right' :
                self.move_selected_placed_letter('right')
            if dir == 'up' :
                self.move_selected_placed_letter('up')
            if dir == 'down' :
                self.move_selected_placed_letter('down')

    def bind_keyboard_events(self):
        self.master.bind("<F11>", self.toggleFullScreen)
        # Delete or Backspace key pressed
        self.master.bind_all(
            "<BackSpace>", self.delete_selected_letter)
        self.master.bind_all("<Delete>", self.delete_selected_letter)
        self.master.bind_all(
            "<Left>", lambda event: self.arrow_key_pressed('left'))
        self.master.bind_all(
            "<Right>", lambda event: self.arrow_key_pressed('right'))
        self.master.bind_all(
            "<Up>", lambda event: self.arrow_key_pressed('up'))
        self.master.bind_all(
            "<Down>", lambda event: self.arrow_key_pressed('down'))
        self.master.bind_all(
            "+", lambda event: self.increment_iterations(1))
        self.master.bind_all(
            "-", lambda event: self.increment_iterations(-1))
        self.master.bind_all(
            "*", lambda event: self.toggle_fit_mode())
        self.master.bind_all(
            "r", lambda event: self.popup_editor())
        self.master.bind_all(
            "=", lambda event: self.toggle_fill())


    def pick_source_image(self):
        selected = select_image_file()
        if selected is None:
            return
        self.set_source_image(selected)

    def pick_selectable_letter_image(self):
        selected = select_image_file()
        if selected is None:
            return
        contoured_image = get_letter_contours(selected)
        self.add_selectable_letter_image(contoured_image)

    def set_source_image(self, source, first_time=True):
        segmented = segment_image(source)
        self.source_image = TextImage(source, segmented)

        # update the image panels
        image = get_viewable_image(source)
        # garbage collector, please don't collect me
        self.output_image_view.tkimage = image
        if first_time:
            # Clear current canvas display
            self.output_image_view.delete('all')


            self.output_image_view.letters = {}
            self.output_image_view.letters_source = {}
            self.source_image_copy = self.source_image

        # Insert the image to the canvas
        self.output_image_view.create_image(
            0, 0, image=image, anchor='nw', tag='background')

        # Scroll Size Setup
        height, width = self.source_image.original.shape[:2]
        size = (width, height)
        self.output_image_view.config(scrollregion="0 0 %s %s" % size)

    def add_selectable_letter_image(self, letter_image, withSnake=True):
        resized = toolbar_sized(
            letter_image.modified, LETTER_SELECTION_SIZE, LETTER_SELECTION_SIZE)
        resized = get_viewable_image(resized)

        self.letter_selection_frame.letters.append(resized)

        image_instance = Label(self.letter_selection_frame,
                               image=resized, background=COLOR_WHITE)
        image_instance.pack(fill='x')

        # Selection binding
        image_instance.bind(
            "<Button-1>", lambda event: self.select_letter_image(image_instance, letter_image, withSnake))

    def add_letter_image(self, source, top_left):
        # update the image panels
        image = get_viewable_image(source.modified)
        left, top = top_left
        # Insert the image to the canvas
        instance = self.output_image_view.create_image(
            left, top, image=image, anchor='nw', tags='letter')

        # garbage collector, please don't collect me
        self.output_image_view.letters[instance] = image
        self.output_image_view.letters_source[instance] = source
        return instance

    def unselect_letter(self):
        self.selected_letter = None
        self.selected_letter_snake = None
        for letter_image in self.letter_selection_frame.winfo_children():
            letter_image.configure(background=COLOR_WHITE)
        self.reset_cursor()

    def select_letter_image(self, image_instance, letter_image, withSnake = True):
        self.withSnake = withSnake
        if self.selected_letter is None or not self.selected_letter == letter_image:
            self.unselect_letter()
            self.selected_letter = letter_image
            # image_instance.configure(background=COLOR_GREY)
        else:
            self.unselect_letter()

    def get_bounds(self, coords, image):
        x, y = coords
        height, width = image.shape[:2]
        height += 0
        width += 0
        top = int(max(y - (height / 2), 0))
        bottom = int(min(y + (height / 2), self.source_image.original.shape[0]))
        left = int(max(x - (width / 2), 0))
        right = int(min(x + (width / 2), self.source_image.original.shape[1]))
        return left, top, right, bottom

    def left_click_callback(self, event):
        # validation
        if(self.source_image is None):
            return

        x = int(self.output_image_view.canvasx(event.x))
        y = int(self.output_image_view.canvasy(event.y))
        if(self.selected_letter is None):
            # Select a piece from the canvas
            clicked_letter = self.output_image_view.find_withtag('current')
            if 'letter' in self.output_image_view.gettags(clicked_letter):
                self.output_image_view.selected_letter = clicked_letter
            else:
                # clear selection
                self.output_image_view.selected_letter = None
        else:
            # Add letter to canvas
            self.place_letter()

            # Clear selected letter to add
            self.unselect_letter()

    def delete_selected_letter(self, event):
        if(self.editor_mode):
            return
        if(not self.output_image_view.selected_letter is None):
            selected_letter_id = self.output_image_view.find_withtag(self.output_image_view.selected_letter)[0]
            self.output_image_view.delete(
                self.output_image_view.selected_letter)
            del self.output_image_view.letters[selected_letter_id]
            del self.output_image_view.letters_source[selected_letter_id]
            self.output_image_view.selected_letter = None

    def move_selected_placed_letter(self, direction):
        speed = 1
        if direction == 'left':
            dx, dy = (-speed, 0)
        if direction == 'right':
            dx, dy = (speed, 0)
        if direction == 'up':
            dx, dy = (0, -speed)
        if direction == 'down':
            dx, dy = (0, speed)
        self.output_image_view.move(
            self.output_image_view.selected_letter, dx, dy)


    def reset_cursor(self):
        if(self.output_image_view.corsur_image is not None):
            self.output_image_view.delete(
                self.output_image_view.corsur_image)
            self.output_image_view.delete(
                self.output_image_view.corsur_bounds)
        self.output_image_view.corsur = None
        self.output_image_view.corsur_image = None
        self.output_image_view.corsur_bounds = None

    def handle_mouse_movement(self, event):
        x, y = self.output_image_view.canvasx(
            event.x), self.output_image_view.canvasy(event.y)
        self.output_image_view.corsur_position = (x, y)
        self.draw_snaked_letter()

    def draw_snaked_letter(self):
        if self.selected_letter is None or self.source_image is None or self.output_image_view.corsur_position is None:
            return
        x, y = self.output_image_view.corsur_position
        height, width = self.selected_letter.modified.shape[:2]
        center_y = y - (height / 2)
        center_x = x - (width / 2)

        # todo: rotated bounds
        bounds = self.get_bounds(
            (x, y), self.selected_letter.modified) 
        left, top, right, bottom = bounds

        # Update snake image

        search_bounds = TextImage(self.source_image.original[
            top:bottom, left:right], self.source_image.segmented[
            top:bottom, left:right])

        snaked_image = self.selected_letter
        if (self.withSnake):
            snaked_image = get_snakes(self.selected_letter, search_bounds, max_iterations=self.snakes_params.iterations,
                           expand=self.snakes_params.expand, fill=self.snakes_params.fill)
        corsur_image = get_viewable_image(
            snaked_image.modified)
        self.output_image_view.corsur_image = corsur_image
        self.selected_letter_snake = snaked_image

        if self.output_image_view.corsur is None:
            self.output_image_view.corsur = self.output_image_view.create_image(
                center_x, center_y, image=corsur_image, anchor='nw', tags='corsur')
            self.output_image_view.corsur_bounds = self.output_image_view.create_rectangle(
                *bounds)
        else:
            # Update corsur image and bounds position
            self.output_image_view.coords(
                self.output_image_view.corsur, center_x, center_y)
            self.output_image_view.coords(
                self.output_image_view.corsur_bounds, *bounds)
            # Update corsur image
            self.output_image_view.itemconfig(
                self.output_image_view.corsur, image=corsur_image)

    def get_output_image_canvas(self, frame):
        output_image_frame = Frame(frame)
        self.output_image_view = OutputCanvas(
            output_image_frame, highlightthickness=0)

        # Scrollbar
        input_scroll_x = Scrollbar(
            output_image_frame, orient='horizontal')
        input_scroll_x.pack(side='bottom', fill='x')
        input_scroll_x.config(command=self.output_image_view.xview)

        input_scroll_y = Scrollbar(
            output_image_frame, orient='vertical')
        input_scroll_y.pack(side='right', fill='y')
        input_scroll_y.config(command=self.output_image_view.yview)

        self.output_image_view.config(
            yscrollcommand=input_scroll_y.set, xscrollcommand=input_scroll_x.set)

        self.output_image_view.pack(
            expand=True, fill='both', side='left')

        # Selected letter
        self.output_image_view.selected_letter = None

        # Mouse Cursor
        self.output_image_view.corsur = None
        self.output_image_view.corsur_image = None
        self.output_image_view.corsur_bounds = None
        self.output_image_view.bind('<Motion>', self.handle_mouse_movement)

        # Left Mouse Click
        self.output_image_view.bind("<Button-1>", self.left_click_callback)

        # Mouse Scroll
        self.output_image_view.bind(
            "<MouseWheel>", self.on_mousewheel_callback)

        return output_image_frame

    def get_letter_selection_frame(self, frame):
        scrollable_frame = ScrollableFrame(frame,
            background=COLOR_WHITE)
        self.letter_selection_frame = scrollable_frame.frame
        self.letter_selection_frame.letters = []

        return scrollable_frame

    def place_letter(self):
        if self.selected_letter_snake is not None:
            snakes_image = self.selected_letter_snake
            coords = self.output_image_view.coords(self.output_image_view.corsur)
            self.add_letter_image(snakes_image, coords)

    def generate_contours_output(self):
        # generate_output_from_canvas(self.output_image_view, 'outputi.tif')
        if self.source_image is None:
            return

        # Put all the letters on the source image
        letters = self.output_image_view.find_withtag('letter')
        output = []
        for letter in letters:
            coords = self.output_image_view.coords(letter)
            top_left = [int(coords[0]), int(coords[1])]
            letter_contours = []
            for contours in self.output_image_view.letters_source[letter].contours:
                letter_contours.append(contours.tolist())
            letter_representation = {
                "coords": top_left,
                "contours": letter_contours,
            }
            output.append(letter_representation)
        save_contours_to_file(output)

    def generate_output(self):
        # generate_output_from_canvas(self.output_image_view, 'outputi.tif')
        if self.source_image is None:
            return
        original = self.source_image.original
        output = np.reshape(original,
                            (original.shape[0], original.shape[1], 4))

        # Put all the letters on the source image
        letters = self.output_image_view.find_withtag('letter')
        for letter in letters:
            coords = self.output_image_view.coords(letter)
            top_left = [int(coords[0]), int(coords[1])]
            letter_image = self.output_image_view.letters_source[letter].modified
            output = lay_over(output, letter_image, top_left)

        save_image_to_file(output)

    # LETTER MODIFIERS
    def rotate_selected_letter(self, dir):
        if dir == 'left':
            self.selected_letter = rotate_letter(self.selected_letter, 5)
        if dir == 'right':
            self.selected_letter = rotate_letter(self.selected_letter, -5)
        self.draw_snaked_letter()

    def resize_selected_letter(self, scale):
        if scale == 'up':
            self.selected_letter = resize_letter(self.selected_letter, 0.1)
        if scale == 'down':
            self.selected_letter = resize_letter(self.selected_letter, -0.1)
        self.draw_snaked_letter()
    
    # SNAKES MODIFIERS
    def increment_iterations(self, amount):
        if self.editor_mode:
            return
        self.snakes_params.iterations = max(
            1, self.snakes_params.iterations + amount)
        self.draw_snaked_letter()

    def toggle_fit_mode(self):
        if self.editor_mode:
            return
        self.snakes_params.expand = not self.snakes_params.expand
        self.draw_snaked_letter()

    def toggle_fill(self):
        if self.editor_mode:
            return
        self.snakes_params.fill = not self.snakes_params.fill
        self.draw_snaked_letter()

    def popup_editor(self):
        if self.editor_mode:
            messagebox.showwarning("Warning", "another editor is open")
            return
        if self.output_image_view.selected_letter is None:
            messagebox.showwarning("Warning", "Please select letter to de-format")
            return
        #create editor window
        self.editor_mode = True
        self.edit_win = Toplevel()

        # get letter to modify
        selected_letter = self.output_image_view.selected_letter
        selected_letter_id = self.output_image_view.find_withtag(selected_letter)[0]
        self.edit_img_source = self.output_image_view.letters_source[selected_letter_id].modified
        self.edit_img = get_viewable_image(self.edit_img_source)

        bounds = self.output_image_view.bbox(selected_letter)# returns a tuple like (x1, y1, x2, y2)
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        self.edit_canvas = Canvas(self.edit_win, width=width, height=height)
        # get background
        self.background = self.source_image.get()[bounds[1]:bounds[3], bounds[0]:bounds[2]]
        self.background = get_viewable_image(self.background)
        self.edit_canvas.create_image(0, 0, image=self.background,
                                                         anchor='nw', tags='background')
        # add letter
        self.edit_img_id = self.edit_canvas.create_image(
            0, 0, image=self.edit_img, anchor='nw', tags='letter')
        # add all attributes + labels + buttons
        self.edit_win.overrideredirect(True)
        self.edit_win.attributes("-topmost", True)
        self.edit_win.wm_title("Edit-Mode")
        close = Button(self.edit_win, text="Close", command= lambda : self.destroy_popup(False))
        save = Button(self.edit_win, text="Save", command=lambda: self.destroy_popup(True))
        deformat = Button(self.edit_win, text="Deformat", command=lambda: self.deformat())
        # Title
        label = Label(self.edit_win, text="Edit-Mode")
        label.grid(row=0, column=0)
        self.interpolation=0
        # Interpolation options
        Style().configure("green.TButton", padding=6, relief="flat",
                              background="green")
        Style().configure("red.TButton", padding=6, relief="flat",
                              background="red")
        nearest = Button(self.edit_win, text="nearest", command=lambda : self.change_interpolation(0), style="green.TButton")
        linear = Button(self.edit_win, text="b-linear", command=lambda : self.change_interpolation(1), style="red.TButton")
        cubic = Button(self.edit_win, text="cubic", command=lambda : self.change_interpolation(2), style="red.TButton")
        self.interpolations.append(nearest)
        self.interpolations.append(linear)
        self.interpolations.append(cubic)
        nearest.grid(row=1, column=0)
        linear.grid(row=1, column=1)
        cubic.grid(row=1, column=2)
        self.edit_canvas.grid(row=2, column=1)
        close.grid(row=3, column=0)
        deformat.grid(row=3, column=1)
        save.grid(row=3, column=2)
        self.edit_canvas.bind("<Button-1>", self.create_line)

    def change_interpolation(self, id):
        self.interpolation = id
        for i in self.interpolations:
            i.configure(style="red.TButton")
        self.interpolations[id].configure(style="green.TButton")

    def deformat(self):
        if self.current_line is None:
            messagebox.showwarning("Warning", "Please draw line in order to deformat")
            return
        (x1, y1, x2, y2) = (self.first_x,self.first_y,self.second_x,self.second_y)
        self.edit_img_source = deformat_img(self.edit_img_source, x2, y2, x1, y1, 2)
        self.edit_img = get_viewable_image(self.edit_img_source)
        self.edit_canvas.delete(self.edit_img_id)
        self.edit_img_id = self.edit_canvas.create_image(
            0, 0, image=self.edit_img, anchor='nw', tags='letter')
        self.first_x = None
        self.first_y = None
        self.edit_canvas.delete(self.current_line)

    def create_line(self, event):
        if self.first_x is None or (self.second_x is not None):
            self.first_x = event.x
            self.first_y = event.y
            self.second_x = None
            self.second_y = None
        else:
            if self.current_line is not None:
                self.edit_canvas.delete(self.current_line)
            self.second_x = event.x
            self.second_y = event.y
            self.current_line = self.edit_canvas.create_line(self.first_x, self.first_y,
                                                             self.second_x, self.second_y,
                                                             arrow=LAST, fill='green yellow')

    def destroy_popup(self, shouldSave):
        self.editor_mode = False
        if(shouldSave):
            x1,y1 = self.output_image_view.coords(self.output_image_view.selected_letter)
            self.delete_selected_letter("")
            imgray = cv2.cvtColor(self.edit_img_source, cv2.COLOR_BGR2GRAY)
            ret, thresh = cv2.threshold(imgray, 127, 255, 0)
            contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            letter_img = LetterImage(self.edit_img_source, contours,self.edit_img_source)
            self.add_letter_image(letter_img,(x1,y1))
            mask = self.edit_img_source[:,:,0]
            mask = mask>0

            #Save img
            filename = "edited_letter_"+ str(random.randint(0, 100000))
            path = LETTERS_DIR + '/' + filename + ".tif"
            imsave(path, self.edit_img_source)
            charactar_image = get_letter_image_from_file(path)
            letter_image = get_letter_contours(charactar_image)
            self.add_selectable_letter_image(letter_image)
            # np.set_printoptions(threshold=sys.maxsize)

            #

            #letter_img = LetterImage(mask, contours, self.edit_img_source)
            #self.add_selectable_letter_image(letter_img, False)

        self.edit_win.destroy()
        self.edit_win = None
        self.edit_canvas = None
        self.edit_img = None
        self.edit_img_source = None
        self.edit_img_id = None
        self.background = None
        self.current_line = None
        self.first_x = None
        self.first_y = None
        self.second_x = None
        self.second_y = None
        self.interpolation = 0
        self.interpolations = []

root = Tk()
s = Style()
s.theme_use('default')
app = AnicentTextApp(master=root)
app.mainloop()
