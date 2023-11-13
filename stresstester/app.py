import asyncio
import logging
import time
from typing import Optional, Callable, Iterable
import subprocess
import traceback
import threading
import zipfile
from configparser import ConfigParser

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
# from ttkthemes import ThemedTk

from .base import Trail, TrailResult
from .furmark import Furmark
from .prime95 import Prime95
from .hwinfo64 import HwInfo64
from .logviewer import LogViewer
from .lshw import LSHW
from .batteryinfoview import BatteryInfo
from .utils import *


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
    def __init__(
            self,
            config_path: Optional[str] = None
    ):
        # init task loop
        self._loop = asyncio.get_event_loop()
        self._task_queue = []
        self._task_running = True
        self._pending_trails: dict[str, Trail] = {}
        self._running_trails: dict[str, Trail] = {}
        self._trail_results: dict[str, TrailResult] = {}

        # window
        self.input_window: Optional[tk.Toplevel] = None
        self.stress_window: Optional[tk.Toplevel] = None

        # tkinter won't init without a root window, so
        self.window = tk.Tk()
        self.window.withdraw()

        self._datetime_now_str = datetime_now_str()

        self.path = os.path.dirname(__file__)

        self._config = ConfigParser()
        self._config_path = config_path or os.path.join(os.getcwd(), "../config.ini")
        if os.path.exists(self._config_path):
            self._config.read(self._config_path)
            self._model = self._config.get("global", "model", fallback="未知型号")
        else:
            raise FileNotFoundError(f"Config file {self._config_path} not found")

        self._inst_name = tk.StringVar(value=self._config.get("main_window", "inst_name", fallback=""))
        self._stress = tk.BooleanVar(value=is_str_truthful(self._config.get("main_window", "stress", fallback="True")))
        self._stress_cpu = tk.BooleanVar(
            value=is_str_truthful(self._config.get("main_window", "stress_cpu", fallback="True")))
        self._stress_gpu = tk.BooleanVar(
            value=is_str_truthful(self._config.get("main_window", "stress_gpu", fallback="True")))
        self._stress_minutes = tk.IntVar(value=self._config.getint("main_window", "stress_minutes", fallback=10))
        self._cooldown = tk.BooleanVar(
            value=is_str_truthful(self._config.get("main_window", "cooldown", fallback="True")))
        self._cooldown_minutes = tk.IntVar(value=self._config.getint("main_window", "cooldown_minutes", fallback=5))

        self.setup_input_window()
        self.setup_main_window()

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
        self._progress["maximum"] = seconds
        for i in range(seconds):
            self._progress["value"] = i + 1
            _text_min = str((seconds - i) // 60) + self._config["main_window"].get("label_min", "分")
            _text_sec = str((seconds - i) % 60) + self._config["main_window"].get("label_sec", "秒")
            self._start_btn.configure(
                text=_text_min + _text_sec if (seconds - i) // 60 > 0 else _text_sec,
            )

            await asyncio.sleep(1)

    def submit_trail(
            self,
            t: Trail,
            resolve: Optional[Callable[[TrailResult], None]] = None,
            reject: Optional[Callable[[Exception], None]] = None,
            *args, **kwargs
    ):
        if normalize_trail_name(t) in self._pending_trails or \
                normalize_trail_name(t) in self._running_trails:
            logging.error(f"{normalize_trail_name(t)} 正在运行")
            return

        self._pending_trails[normalize_trail_name(t)] = t

        async def trail_runner():
            # move trail from pending to running
            self._running_trails[normalize_trail_name(t)] = self._pending_trails.pop(normalize_trail_name(t))

            # run trail
            try:
                res = await self._running_trails[normalize_trail_name(t)].run(*args, **kwargs)
                # move trail from running to finished
                self._running_trails.pop(normalize_trail_name(t))
                if resolve is not None:
                    resolve(res)
                self._trail_results[normalize_trail_name(t)] = res

            except Exception as e:
                logging.error(f"ERR [{normalize_trail_name(t)}] 出错")
                # print stacktrace
                logging.error(e, exc_info=True)
                # move trail from running to finished
                self._running_trails.pop(normalize_trail_name(t))
                if reject is not None:
                    reject(e)

        self.submit_task(trail_runner())

    def quit(self) -> None:
        print("Received quit signal")
        # unregister log handler
        logging.getLogger().removeHandler(self._handler)
        try:
            # do not accept new tasks
            self._task_running = False
            # terminate all running trails
            for _, t in self._running_trails.items():
                print(f"Terminating {normalize_trail_name(t)}")
                self._loop.create_task(t.terminate())
            asyncio.gather(*self._task_queue)
            print("Hit Ctrl+C to exit")
        except Exception as e:
            print(e)
        finally:
            # stop the mainloop
            self._loop.stop()
            if self.input_window is not None:
                self.input_window.destroy()
            if self.window is not None:
                self.window.destroy()

        # clean up
        time.sleep(5)
        import psutil
        proc = psutil.Process(os.getpid())
        # terminate all child processes
        for child in proc.children(recursive=True):
            child.terminate()
        os._exit(0)

    def create_zip(self) -> str:
        _name = "[{name}]{model}@{date}.zip".format(
            name=replace_unsafe_filename_chars(self._inst_name.get()),
            model=replace_unsafe_filename_chars(self._model),
            date=self._datetime_now_str
        )

        path = os.path.join(os.getcwd(), _name)
        zf = zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)
        for k, v in self._trail_results.items():
            for f in v.files:
                zf.write(f, os.path.join(k, os.path.basename(f)))
        if hasattr(self, "_log_path"):
            zf.write(self._log_path, os.path.basename(self._log_path))
        # generate meta file
        _meta = self.generate_meta()
        zf.write(_meta, os.path.basename(_meta))
        zf.close()

        return path

    def generate_meta(self) -> str:
        _name = f"meta@{self._datetime_now_str}.ini"
        path = os.path.join(self.path, _name)
        cf = ConfigParser()
        cf.set("DEFAULT", "name", self._inst_name.get())
        cf.set("DEFAULT", "model", self._model)
        cf.set("DEFAULT", "date", self._datetime_now_str)
        cf.set("DEFAULT", "stress", str(self._stress.get()))
        cf.set("DEFAULT", "stress_cpu", str(self._stress_cpu.get()))
        cf.set("DEFAULT", "stress_gpu", str(self._stress_gpu.get()))
        cf.set("DEFAULT", "stress_minutes", str(self._stress_minutes.get()))
        cf.set("DEFAULT", "cooldown", str(self._cooldown.get()))
        cf.set("DEFAULT", "cooldown_minutes", str(self._cooldown_minutes.get()))

        for k, v in self._trail_results.items():
            cf.add_section(k)
            if v.string:
                cf.set(k, "string", v.string.replace('%', '%%'))  # has to be escaped
            cf.set(k, "files", ",".join(k + '/' + os.path.basename(f) for f in v.files))
            cf.set(k, "start_time", str(v.start_timestamp))
            cf.set(k, "end_time", str(v.complete_timestamp))

        with open(path, "w") as f:
            cf.write(f)

        return path

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

        # trigger diag
        self.run_diag()

    def setup_main_window(self):
        _config = self._config["main_window"]
        self.window.title(_config.get("title", "电脑小队系统测试工具"))
        self.window.protocol("WM_DELETE_WINDOW", self.quit)
        self.window.iconbitmap(os.path.join(self.path, _config.get("icon", "icon.ico")))

        # create a multi-line text box for logging
        self._log = scrolledtext.ScrolledText(self.window, width=60, height=10)
        self._log.configure(state="disabled", foreground="black")
        self._log.pack(side="bottom", fill="both", expand=True)

        # Configure the logging module to use the custom handler
        self._log_path = os.path.join(os.path.dirname(__file__), f"log@{self._datetime_now_str}.txt")
        logging.basicConfig(filename=self._log_path,
                            level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self._handler = TextHandler(self._log)
        logging.basicConfig(level=logging.INFO)
        logging.getLogger().addHandler(self._handler)

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
        _stress_check = ttk.Checkbutton(_l, text=_config.get("label_stress", "烤机"), variable=self._stress)
        _stress_check.grid(column=0, row=0, sticky="w")

        # create two checkboxes for CPU and GPU stress, disabled when stress is not checked
        _stress_gpu_check = ttk.Checkbutton(_l, text="GPU", variable=self._stress_gpu)
        _stress_gpu_check.grid(column=2, row=2, sticky="w")

        _stress_cpu_check = ttk.Checkbutton(_l, text="CPU", variable=self._stress_cpu)
        _stress_cpu_check.grid(column=0, row=2, sticky="w")

        # add var track
        self._stress.trace("w",
                           lambda *args: _stress_gpu_check.configure(
                               state="normal" if self._stress.get() else "disabled"))
        self._stress.trace("w",
                           lambda *args: _stress_cpu_check.configure(
                               state="normal" if self._stress.get() else "disabled"))

        # create a label and a spinbox for stress minutes
        _stress_minutes_spinbox = ttk.Spinbox(_l, from_=1, to=60, width=5, textvariable=self._stress_minutes)
        _stress_minutes_spinbox.grid(column=2, row=0, sticky="w")

        _stress_minutes_label = ttk.Label(_l, text=_config.get("label_min", "分钟"))
        _stress_minutes_label.grid(column=4, row=0, sticky="w")

        _r = ttk.Frame(self.window)
        _r.pack(side="right", fill="both", expand=True)
        _r.columnconfigure(1, minsize=10)
        _r.columnconfigure(3, minsize=10)
        _r.rowconfigure(1, minsize=10)

        _cooldown_check = ttk.Checkbutton(_r, text=_config.get("label_cooldown", "冷却"), variable=self._cooldown)
        _cooldown_check.grid(column=0, row=0, sticky="w")

        _cooldown_minutes_spinbox = ttk.Spinbox(_r, from_=1, to=60, width=5, textvariable=self._cooldown_minutes)
        _cooldown_minutes_spinbox.grid(column=2, row=0, sticky="w")

        _cooldown_minutes_label = ttk.Label(_r, text=_config.get("label_min", "分钟"))
        _cooldown_minutes_label.grid(column=4, row=0, sticky="w")

        self._start_btn = ttk.Button(_r, text=_config.get("label_testing", "检测中"), command=self.run_trails,
                                     state="disabled")
        self._start_btn.grid(column=0, row=2, sticky="w", columnspan=5)

    def setup_input_window(self):
        _config = self._config["input_window"]
        self.input_window = tk.Toplevel(
            self.window,
            padx=10,
            pady=10,
        )
        self.input_window.title(_config.get("title", "电脑小队系统测试工具"))
        self.input_window.iconbitmap(os.path.join(self.path, _config.get("icon", "icon.ico")))
        self.input_window.protocol("WM_DELETE_WINDOW", self.quit)
        self.input_window.rowconfigure(1, minsize=10)
        self.input_window.rowconfigure(3, minsize=10)
        self.input_window.columnconfigure(1, minsize=10)
        self.input_window.columnconfigure(3, minsize=10)
        self.input_window.columnconfigure(5, minsize=10)

        _text = ttk.Label(self.input_window, text=_config.get("prompt", "请输入电脑名称"))
        _text.configure(state="disabled", foreground="black")
        _text.grid(column=0, row=0, sticky="w", columnspan=6)

        _label = ttk.Label(self.input_window, text=_config.get("label", "名称"))
        _label.grid(column=0, row=2, sticky="w")

        _input = ttk.Entry(self.input_window, width=25, textvariable=self._inst_name)
        _input.grid(column=4, row=2, sticky="w")

        _btn = ttk.Button(self.input_window, text=_config.get("button", "确认"), command=self._on_input_confirm)
        _btn.grid(column=6, row=2, sticky="w")

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
        _config = self._config["on_hwinfo64_finished"]
        # set test btn to normal
        self._start_btn.configure(state="normal", text=self._config["main_window"].get("label_start", "开始"))

        if not result.files:
            messagebox.showinfo(
                _config.get("title", "错误"),
                _config.get("error", "HWInfo64未生成报告，请重试")
            )
            return

        res = messagebox.askokcancel(
            _config.get("title", "提示"),
            _config.get("prompt", "HWInfo64测试完成，是否查看测试结果？")
        )
        if res:
            self.submit_trail(
                LogViewer(),
                reject=self._on_error,
                resolve=lambda *args: self._on_trails_finished(),
                files=(pick_latest_file(result.files),)
            )
        else:
            self._on_trails_finished()

    def _on_trails_finished(self):
        # set test btn to normal
        self._start_btn.configure(state="normal")

        _config = self._config["on_trails_finished"]
        _p = self.create_zip()
        messagebox.showinfo(
            _config.get("title", "提示"),
            _config.get("prompt", f"测试完成，报告已保存到：") + '\n' + _p
        )

        self.open_file(_p)

    def run(self) -> None:
        bg_thread = threading.Thread(target=self.run_loop)
        bg_thread.start()

        # enter mainloop
        if self.window is not None:
            self.window.mainloop()

    def on_lshw_finished(self, result: TrailResult):
        if result.value and '主板' in result.value and result.value['主板']:
            self._model = result.value['主板'][0]
        logging.info("[>>>] 配置 | HWINFO [<<<]")
        logging.info(result.string)

        # enable start button
        self._start_btn.configure(state="normal")
        self._start_btn.configure(text=self._config["main_window"].get("label_start", "开始测试"))
        self._start_btn.focus()

    def on_batteryinfo_finished(self, result: TrailResult):
        if not result.files or not result.string.strip():  # skip if no result
            return
        logging.info("[>>>] 电池 | BATTERY [<<<]")
        logging.info(result.string)

    def _get_stress_sec(self):
        return self._stress_minutes.get() * 60 if self._stress.get() else 0

    def _get_cooldown_sec(self):
        return self._cooldown_minutes.get() * 60 if self._cooldown.get() else 0

    def run_diag(self):
        self.submit_trail(
            BatteryInfo(),
            resolve=self.on_batteryinfo_finished,
            reject=self._on_error,
        )
        self.submit_trail(
            LSHW(),
            resolve=self.on_lshw_finished,
            reject=self._on_error,
        )

    def run_trails(self):
        _config = self._config["main_window"]
        if self._get_stress_sec() + self._get_cooldown_sec() == 0 \
                or (self._stress.get() and not (self._stress_cpu.get() or self._stress_gpu.get())):
            messagebox.showerror(
                _config.get("title", "错误"),
                _config.get("error", "请至少选择一项测试项目")
            )
            return

        # disable start btn
        self._start_btn.configure(state="disabled")

        # update progress bar
        self.submit_task(self.update_progress(
            self._get_stress_sec() + self._get_cooldown_sec() + 10,
        ))

        # run stress test
        self.submit_trail(
            HwInfo64(),
            resolve=self._on_hwinfo64_finished,
            reject=self._on_error,
            timeout=self._get_stress_sec() + self._get_cooldown_sec(),
            **(self._config["hwinfo64"] if "hwinfo64" in self._config else {})
        )

        if self._stress.get():
            if self._stress_cpu.get():
                self.submit_trail(
                    Prime95(),
                    resolve=self._on_success,
                    reject=self._on_error,
                    timeout=self._get_stress_sec(),
                    **(self._config["prime95"] if "prime95" in self._config else {})
                )
            if self._stress_gpu.get():
                self.submit_trail(
                    Furmark(),
                    resolve=self._on_success,
                    reject=self._on_error,
                    timeout=self._get_stress_sec(),
                    **(self._config["furmark"] if "furmark" in self._config else {})
                )
