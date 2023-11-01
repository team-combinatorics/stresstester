import asyncio
import random
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
from typing import Optional, Callable
import subprocess
import sys
import traceback
import threading

from ttkthemes import ThemedTk

from .base import Trail, TrailResult
from ..furmark import Furmark
from ..prime95 import Prime95
from ..hwinfo64 import HwInfo64

class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

class StressTesterApp:
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._task_queue = []
        self._task_running = True
        self._pending_trails: dict[str, Trail] = {}
        self._running_trails: dict[str, Trail] = {}
        self._trail_results: dict[str, TrailResult] = {}

        self.input_window: Optional[tk.Toplevel] = None
        self.stress_window: Optional[tk.Toplevel] = None

        # tkinter won't init without a root window, so
        self.window = ThemedTk(theme="arc")
        self.window.withdraw()

        # Input values
        self._inst_name = tk.StringVar(value="")
        self._stress = tk.BooleanVar(value=True)
        self._stress_cpu = tk.BooleanVar(value=True)
        self._stress_gpu = tk.BooleanVar(value=True)
        self._stress_minutes = tk.IntVar(value=20)
        self._cooldown = tk.BooleanVar(value=True)
        self._cooldown_minutes = tk.IntVar(value=10)

        self.setup()

    @staticmethod
    def normalize_trail_name(t: Trail):
        return t.__class__.__name__.lower()

    def submit_task(self, task):
        self._task_queue.append(
            self._loop.create_task(task)
        )

    def run_loop(self, interval: float = 0.05):
        async def run():
            while self._task_running:
                await asyncio.gather(*self._task_queue)
                await asyncio.sleep(interval)
        self._loop.create_task(run())
        self._loop.run_forever()

    async def update_progress(self, seconds: int):
        if self._progress is None:
            return
        for i in range(seconds):
            self._progress["value"] = int((i+1) / seconds * 100)
            await asyncio.sleep(1)

    def submit_trail(
            self, 
            t: Trail, 
            resolve: Optional[Callable[[TrailResult], None]] = None,
            reject: Optional[Callable[[Exception], None]] = None,
            *args, **kwargs
        ):
        if self.normalize_trail_name(t) in self._pending_trails or \
            self.normalize_trail_name(t) in self._running_trails:
            logging.error(f"{self.normalize_trail_name(t)} 正在运行")
            return

        self._pending_trails[self.normalize_trail_name(t)] = t

        async def trail_runner():
            # move trail from pending to running
            self._running_trails[self.normalize_trail_name(t)] = self._pending_trails.pop(self.normalize_trail_name(t))
            
            # run trail
            try:
                res = await self._running_trails[self.normalize_trail_name(t)].run(*args, **kwargs)
                # move trail from running to finished
                self._running_trails.pop(self.normalize_trail_name(t))
                if resolve is not None:
                    resolve(res)
                self._trail_results[self.normalize_trail_name(t)] = res

            except Exception as e:
                logging.error(f"{self.normalize_trail_name(t)} 出错: ")
                # print stacktrace
                logging.error(e, exc_info=True)
                # move trail from running to finished
                self._running_trails.pop(self.normalize_trail_name(t))
                if reject is not None:
                    reject(e)

        self.submit_task(trail_runner())

    def quit(self) -> None:
        print("Received quit signal")
        logging.warning("Received quit signal")
        # do not accept new tasks
        self._task_running = False
        # terminate all running trails
        for _, t in self._running_trails.items():
            logging.warning(f"Terminating {self.normalize_trail_name(t)}")
            print(f"Terminating {self.normalize_trail_name(t)}")
            self._loop.create_task(t.terminate())

        asyncio.gather(*self._task_queue)

        # stop the mainloop
        self._loop.stop()

        if self.input_window is not None:
            self.input_window.destroy()
        if self.window is not None:
            self.window.destroy()


    def open_file(self, path: str):
        # open the location of a file with windows explorer
        subprocess.Popen(f'explorer /select,"{path}"')

    def _on_input_confirm(self):
        # check if the input is valid
        if not self._inst_name.get():
            messagebox.showerror("错误", "名称不能为空")
            return
        
        # close the input window
        if self.input_window is not None:
            self.input_window.destroy()
        # show the main window
        self.window.deiconify()


    def setup_main_window(self):
        self.window.title("电脑小队系统测试工具")
        self.window.protocol("WM_DELETE_WINDOW", self.quit)

        # create a multi-line text box for logging
        self._log = scrolledtext.ScrolledText(self.window, width=50, height=10)
        self._log.configure(state="disabled", foreground="black")
        self._log.pack(side="bottom", fill="both", expand=True)

        # Configure the logging module to use the custom handler
        logging.basicConfig(filename='test.log',
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s')   
        handler = TextHandler(self._log)
        logging.basicConfig(level=logging.INFO)
        logging.getLogger().addHandler(handler)

        # create a progress bar
        self._progress = ttk.Progressbar(self.window, orient="horizontal", length=100, mode="determinate")
        self._progress.pack(side="bottom", fill="x", expand=True, ipady=10)

        # create a 2-column layout for rest of the space
        _l = ttk.Frame(self.window)
        _l.pack(side="left", fill="both", expand=True)
        _l.columnconfigure(1, minsize=10)
        _l.columnconfigure(3, minsize=10)
        _l.rowconfigure(1, minsize=10)

        # create a checkbox for stress test
        _stress_check = ttk.Checkbutton(_l, text="烤机", variable=self._stress)
        _stress_check.grid(column=0, row=0, sticky="w")

        # create two checkboxes for CPU and GPU stress, disabled when stress is not checked
        _stress_gpu_check = ttk.Checkbutton(_l, text="GPU", variable=self._stress_gpu)
        _stress_gpu_check.grid(column=2, row=2, sticky="w")

        _stress_cpu_check = ttk.Checkbutton(_l, text="CPU", variable=self._stress_cpu)
        _stress_cpu_check.grid(column=0, row=2, sticky="w")

        # create a label and a spinbox for stress minutes
        _stress_minutes_spinbox = ttk.Spinbox(_l, from_=1, to=60, width=5, textvariable=self._stress_minutes)
        _stress_minutes_spinbox.grid(column=2, row=0, sticky="w")

        _stress_minutes_label = ttk.Label(_l, text="分钟")
        _stress_minutes_label.grid(column=4, row=0, sticky="w")

        _r = ttk.Frame(self.window)
        _r.pack(side="right", fill="both", expand=True)
        _r.columnconfigure(1, minsize=10)
        _r.columnconfigure(3, minsize=10)
        _r.rowconfigure(1, minsize=10)

        _cooldown_check = ttk.Checkbutton(_r, text="冷却", variable=self._cooldown)
        _cooldown_check.grid(column=0, row=0, sticky="w")

        _cooldown_minutes_spinbox = ttk.Spinbox(_r, from_=1, to=60, width=5, textvariable=self._cooldown_minutes)
        _cooldown_minutes_spinbox.grid(column=2, row=0, sticky="w")

        _cooldown_minutes_label = ttk.Label(_r, text="分钟")
        _cooldown_minutes_label.grid(column=4, row=0, sticky="w")

        _start_btn = ttk.Button(_r, text="开始", command=self.run_trails)
        _start_btn.grid(column=0, row=2, sticky="w", columnspan=5)


    def setup_input_window(self):
        self.input_window = tk.Toplevel(
            self.window,
            padx=10, 
            pady=10,
        )
        self.input_window.title("电脑小队系统测试工具")
        self.input_window.protocol("WM_DELETE_WINDOW", self.quit)
        self.input_window.rowconfigure(1, minsize=10)
        self.input_window.rowconfigure(3, minsize=10)
        self.input_window.columnconfigure(1, minsize=10)
        self.input_window.columnconfigure(3, minsize=10)
        self.input_window.columnconfigure(5, minsize=10)

        _text = ttk.Label(self.input_window, text="请在下方输入电脑名称，然后点击确认")
        _text.configure(state="disabled", foreground="black")
        _text.grid(column=0, row=0, sticky="w", columnspan=6)

        _label = ttk.Label(self.input_window, text="名称")
        _label.grid(column=0, row=2, sticky="w")

        _input = ttk.Entry(self.input_window, width=25, textvariable=self._inst_name)
        _input.grid(column=4, row=2, sticky="w")

        _btn = ttk.Button(self.input_window, text="确认", command=self._on_input_confirm)
        _btn.grid(column=6, row=2, sticky="w")


    def setup(self):
        self.setup_input_window()
        self.setup_main_window()

    def _on_success(self, result: TrailResult):
        pass

    def _on_error(self, e: Exception):
        # make the progress bar red
        if self._progress is not None:
            self._progress["style"] = "red.Horizontal.TProgressbar"
        
        # use a messagebox to show error
        text = f"错误: {e} \n{traceback.format_exc()}"
        messagebox.showerror("错误", text)

        # calls exit
        self.quit()

    def _on_hwinfo64_finished(self, result: TrailResult):
        # open the log file
        print(self._trail_results)

    def run(self) -> None:
        bg_thread = threading.Thread(target=self.run_loop)
        bg_thread.start()

        # enter mainloop
        if self.window is not None:
            self.window.mainloop()

    def run_trails(self):
        # update progress bar
        self.submit_task(self.update_progress(
            (self._stress_minutes.get() + self._cooldown_minutes.get())*60
        ))
        # run stress test
        self.submit_trail(
            HwInfo64(),
            resolve=self._on_success,
            reject=self._on_error,
            timeout=(self._stress_minutes.get() + self._cooldown_minutes.get()) * 60,
        )
        self.submit_trail(
            Furmark(),
            resolve=self._on_success,
            reject=self._on_error,
            timeout=self._stress_minutes.get() * 60,
        )
        self.submit_trail(
            Prime95(),
            resolve=self._on_success,
            reject=self._on_error,
            timeout=self._stress_minutes.get() * 60,
        )

if __name__ == '__main__':
    app = StressTesterApp()
    app.run()