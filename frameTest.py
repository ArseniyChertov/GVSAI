from tkinter import *

root = Tk()
root.geometry("480x600")
frame = LabelFrame(root, text="This Is My Frame...", padx=5, pady=5)
frame.place(x=100, y=00)

b = Button(frame, text="Don't Click Here!")
b.pack()




root.mainloop()