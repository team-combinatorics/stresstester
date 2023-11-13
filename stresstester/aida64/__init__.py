import os
from stresstester.base import Trail, TrailResult
from typing import Literal
import psutil


class AIDA64(Trail):
    def __init__(self):
        super().__init__(
            path=os.path.dirname(__file__),
            files=(),
        )

    def _terminate_sync(self):
        try:
            # terminate all child processes
            parent = psutil.Process(self._process.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            self._process.terminate()
        except psutil.NoSuchProcess as e:
            print(f"Trail {self._process.pid} may have already terminated")
            print(e)

    async def terminate(self):
        try:
            self._terminate_sync()
        except Exception as e:
            print(f"Failed to terminate {self._process.pid}")
            print(e)

    async def run(self,
                  tests: tuple[Literal["CPU", "FPU", "Cache", "RAM", "Disk", "GPU"]] = ("FPU",),
                  timeout: int = 30,
                  ):
        return await self.exec(
            "aida64.exe /SST {sst_target} /SSTDUR {sst_dur}",
            timeout=timeout,
            sst_target=",".join(tests),
            sst_dur=max(1, (timeout + 1) // 60),
        )
