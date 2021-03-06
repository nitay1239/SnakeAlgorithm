from tkinter import Tk, Button, Label, Frame, Canvas, Scrollbar
from tkinter.ttk import Button, Label, Scrollbar, Style
from utils.interfaces import LetterImage, TextImage, SnakesParams

class LetterFitnessControl(Frame):
    def __init__(self, parent, **kwargs):
        Frame.__init__(self, parent, **kwargs)
        label = Label(self, text='Letter Menu:')
        label.pack()