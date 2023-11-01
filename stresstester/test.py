import tkinter as tk
from tkinter import messagebox, ttk

# 创建主窗口
window = tk.Tk()
window.title("应用程序")

# 第一个窗口
frame1 = tk.Frame(window)
frame1.pack(pady=20)

name_label = tk.Label(frame1, text="请输入姓名:", font=("Arial", 14))
name_label.grid(row=0, column=0)

name_entry = tk.Entry(frame1, font=("Arial", 14))
name_entry.grid(row=0, column=1)

def open_window2():
    window.withdraw()
    window2.deiconify()

confirm_button = tk.Button(frame1, text="确认", font=("Arial", 12), command=open_window2)
confirm_button.grid(row=0, column=2, padx=10)

# 第二个窗口
window2 = tk.Toplevel(window)
window2.title("窗口2")
window2.withdraw()

frame2 = tk.Frame(window2)
frame2.pack(padx=20, pady=20)

left_frame = tk.Frame(frame2)
left_frame.pack(side="left")

copy_checkbutton = tk.Checkbutton(left_frame, text="拷机", font=("Arial", 12))
copy_checkbutton.pack(pady=10)

copy_label = tk.Label(left_frame, text="分钟", font=("Arial", 12))
copy_label.pack()

copy_entry = tk.Entry(left_frame, font=("Arial", 12))
copy_entry.pack()

cpu_checkbutton = tk.Checkbutton(left_frame, text="CPU", font=("Arial", 12))
cpu_checkbutton.pack()

gpu_checkbutton = tk.Checkbutton(left_frame, text="GPU", font=("Arial", 12))
gpu_checkbutton.pack()

right_frame = tk.Frame(frame2)
right_frame.pack(side="right")

cool_checkbutton = tk.Checkbutton(right_frame, text="冷却", font=("Arial", 12))
cool_checkbutton.pack(pady=10)

cool_label = tk.Label(right_frame, text="分钟", font=("Arial", 12))
cool_label.pack()

cool_entry = tk.Entry(right_frame, font=("Arial", 12))
cool_entry.pack()

progressbar = ttk.Progressbar(window2, length=200)
progressbar.pack(pady=20)

def open_window3():
    window2.withdraw()
    window3.deiconify()

progressbar_button = tk.Button(window2, text="确认", font=("Arial", 12), command=open_window3)
progressbar_button.pack()

# 第三个窗口
window3 = tk.Toplevel(window)
window3.title("窗口3")
window3.withdraw()

frame3 = tk.Frame(window3)
frame3.pack(padx=20, pady=20)

confirm_label = tk.Label(frame3, text="要查看测试结果吗？", font=("Arial", 14))
confirm_label.pack()

# create a messagebox with confirm and cancel button

def confirm():
    messagebox.askquestion(title="确认", message="确认要查看测试结果吗？")

confirm_button = tk.Button(frame3, text="确认", font=("Arial", 12), command=confirm)
confirm_button.pack(pady=10)

window.mainloop()