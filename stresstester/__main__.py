import asyncio
import random
import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional, Callable

from .base import Trail, TrailResult
from ..furmark import Furmark

class StressTesterWindow(tk.Tk):
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._task_queue = []
        self._task_running = True

        self._pending_trails: dict[str, Trail] = {}
        self._running_trails: dict[str, Trail] = {}
        self._trail_results: dict[str, TrailResult] = {}

        self.setup()

    @staticmethod
    def normalize_trail_name(t: Trail):
        return t.__class__.__name__.lower()

    def submit_task(self, task):
        self._task_queue.append(
            self._loop.create_task(task)
        )

    async def run_loop(self, interval: float = 0.05):
        while self._task_running:
            await asyncio.gather(*self._task_queue)
            await asyncio.sleep(interval)

    def submit_trail(
            self, 
            t: Trail, 
            resolve: Optional[Callable[[TrailResult], None]] = None,
            reject: Optional[Callable[[Exception], None]] = None
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
                res = await self._running_trails[self.normalize_trail_name(t)].run()
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


    def run(self) -> None:
        self._loop.create_task(self.run_loop())
        self._loop.run_forever()
        # enter mainloop
        self.mainloop()


    def quit(self) -> None:
        
        # do not accept new tasks
        self._task_running = False
        # terminate all running trails
        _terminate_tasks = []
        for _, t in self._running_trails.items():
            _terminate_tasks.append(t.terminate())
        self._loop.run_until_complete(asyncio.gather(*_terminate_tasks))
        # stop the loop
        self._loop.stop()

        return super().quit()

    def _on_button_click(self):
        self.submit_trail(Furmark())


    def setup(self):
        self.title("电脑小队系统测试工具")
        self._frame = ttk.Frame(self, padding="3 3 12 12")
        self._frame.grid(column=0, row=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # create a progress bar
        self._progress = ttk.Progressbar(self._frame, orient="horizontal", length=200, mode="determinate")
        self._progress.pack(side="bottom", fill="x", expand=True)

        # create a listbox
        self._listbox = tk.Listbox(self._frame, width=50, height=20)

        # create a input 
        self._input = ttk.Entry(self._frame, width=50, textvariable=tk.IntVar())
        # get value 
        self._input.get()

        # create a button
        self._button = ttk.Button(self._frame, text="开始测试", command=self._on_button_click)


# class AsyncTk(tk.Tk):
#     "Basic Tk with an asyncio-compatible event loop"
#     def __init__(self):
#         super().__init__()
#         self.running = True
#         self.runners = [self.tk_loop()]
#         self.button_presses = []

#     async def tk_loop(self):
#         "asyncio 'compatible' tk event loop?"
#         # Is there a better way to trigger loop exit than using a state vrbl?
#         while self.running:
#             self.update()
#             await asyncio.sleep(0.05) # obviously, sleep time could be parameterized
#             if len(self.button_presses) > 0:
#                 await self.button_presses.pop(0)
#                 self.mainloop()

    

#     def stop(self):
#         self.running = False

#     async def run(self):
#         await asyncio.gather(*self.runners)

#     def add_button_coro(self, coro):
#         task = asyncio.create_task(coro)
#         self.button_presses.append(task)


# class App(AsyncTk):
#     "User's app"
#     def __init__(self):
#         super().__init__()
#         self.create_interface()
#         self.runners.append(self.counter())

#     def create_interface(self):
#         b1 = Button(master=self, text='Random Float',
#                     command=lambda: print("your wish, as they say...", random.random()))
#         b1.pack()
#         b2 = Button(master=self, text='Quit', command=self.stop)
#         b2.pack()
#         b3 = Button(master=self, text='Foo', command=lambda: self.add_button_coro(self.foo()))
#         b3.pack()

#     async def counter(self):
#         "sample async worker... (with apologies to Lawrence Welk)"
#         i = 1
#         while self.running:
#             print("and a", i)
#             await asyncio.sleep(1)
#             i += 1

#     async def foo(self):
#         print(f"IO task foo has started")
#         await asyncio.sleep(1)
#         print(f"IO task foo has finished")

# async def main():
#     app = App()
#     await app.run()

if __name__ == '__main__':
    app = StressTesterWindow()
    app.run()