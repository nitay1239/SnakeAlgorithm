from tkinter import Frame, Canvas, Scrollbar
from tkinter.ttk import Scrollbar
from utils.tkinter_adapters import scroll_view
class ScrollableFrame(Frame):
    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)
        scrollbar = Scrollbar(self, orient='vertical')
        scrollbar.pack(fill='y', side='right', expand=False)
        canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=canvas.yview)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.frame = Frame(canvas)
        frame_instance = canvas.create_window(0, 0, window=self.frame,anchor='nw')


        def _configure_frame(event):
            size = (self.frame.winfo_reqwidth(), self.frame.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if self.frame.winfo_reqwidth() != canvas.winfo_width():
                canvas.config(width=self.frame.winfo_reqwidth())
            if self.frame.winfo_reqheight() != canvas.winfo_height():
                canvas.config(height=self.frame.winfo_reqheight())

        def _configure_canvas(event):
            if self.frame.winfo_reqwidth() != canvas.winfo_width():
                canvas.itemconfigure(
                    frame_instance, width=canvas.winfo_width())
            if self.frame.winfo_reqheight() != canvas.winfo_height():
                canvas.config(height=self.frame.winfo_reqheight())


        # Mouse Scroll
        def _on_mousewheel_callback(event):
            scroll_view(canvas, event)

        def _bound_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel_callback)

        def _unbound_to_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        self.bind('<Enter>', _bound_to_mousewheel)
        self.bind('<Leave>', _unbound_to_mousewheel)
        canvas.bind('<Configure>', _configure_canvas)
        self.frame.bind('<Configure>', _configure_frame)
