import tkinter
from tkinter import ttk

root = tkinter.Tk()
root.title('Tab Widget Test')
root.geometry("500x500")

my_notebook = tkinter.ttk.Notebook(root)
#my_notebook.pack()
my_notebook.place(x=0, y=0)

def hide():
    my_notebook.hide(1)

def show():
    my_notebook.add(my_frame2, text="Red Tab")

def select():
    my_notebook.select(1)

my_frame1 = tkinter.Frame(my_notebook, width=500, height=500, bg='blue')
my_frame2 = tkinter.Frame(my_notebook, width=500, height=500, bg='red')

#my_frame1.pack(fill="both", expand=1)
#my_frame2.pack(fill="both", expand=1)

my_notebook.add(my_frame1, text="Blue Tab")
my_notebook.add(my_frame2, text="Red Tab")

# Hide A Tab
my_button = tkinter.Button(my_frame1, text="Hide Tab 2", command=hide)
my_button.place(x=100,y=100)

# Show A Tab
my_button2 = tkinter.Button(my_frame1, text="Show Tab 2", command=show)
my_button2.place(x=100,y=120)

# Navigate To A Tab
my_button3 = tkinter.Button(my_frame1, text="Navigate Tab 2", command=select)
my_button3.place(x=100,y=140)

root.mainloop()
