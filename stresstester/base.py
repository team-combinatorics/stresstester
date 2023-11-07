import asyncio
import subprocess
import logging
import time
import os
import glob
from typing import Optional, Union, List, Iterable, Any
from dataclasses import dataclass

import psutil

@dataclass
class TrailResult:
    start_timestamp: float  # timestamp when the trail was started
    complete_timestamp: float  # timestamp when the trail was completed
    files: Iterable[str] = ()  # results as a list of files
    string: Optional[str] = None  # result as a string
    value: Optional[Any] = None   # result as any python object


class Trail:
    def __init__(self, path, files: tuple[str, ...] = ()):
        # by default, the path is the directory of the file
        self.path = path
        self.files = files
        self._stdout = None
        self._process: Optional[asyncio.subprocess.Process] = None
    
    def __repr__(self):
        return f"<Trail path={self.path!r}>"
    
    def __str__(self):
        return self.path

    def out_to_value(self, out: str):
        """Parse the output of the trail to a python object."""
        return None

    async def exec(
        self, cmd: str, timeout: Optional[float] = None, 
        *args, **kwargs
    ):
        """Run the trail."""
        self._process = await asyncio.create_subprocess_shell(
            cmd.format(path=self.path, *args, **kwargs),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.path,
        )

        logging.info(f"{cmd.format(path=self.path, *args, **kwargs)} (cwd={self.path}, timeout={timeout}, pid={self._process.pid})")

        _time_start = time.time()
        
        # run the process
        try:
            self._stdout, self._stderr = await asyncio.wait_for(self._process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            # some trails may not terminate by themselves, should be normal
            await self.terminate()
            logging.warning(f"Trail {self.path} terminated after {timeout} seconds")
            self._stdout, self._stderr = b'', b''

        # get the output
        out_str = self._stdout.decode('gbk') + self._stderr.decode('gbk')
        
        # parse the output
        value = self.out_to_value(self._stdout.decode('gbk'))

        # check if files were generated
        files = []
        for f in self.files:
            fullpath = os.path.join(self.path, f)
            _to_add = glob.glob(fullpath)
            if _to_add:
                files.extend(_to_add)
            else:
                logging.warning(f"File {fullpath} was not generated")

        # # convert files to utf-8
        # for f in files:
        #     self.gbk_file_to_utf8(f)
        
        return TrailResult(
            start_timestamp=_time_start,
            complete_timestamp=time.time(),
            files=files,
            string=out_str,
            value=value,
        )

    async def terminate(self):
        """Terminate the trail."""
        if not self._process:
            return
        # terminate all child processes
        try:
            parent = psutil.Process(self._process.pid)
            for child in parent.children():
                child.terminate()
            self._process.terminate()
            await self._process.wait()
        except psutil.NoSuchProcess as e:
            print(f"Trail {self.path} may have already terminated")
            print(e)
    
    async def run(
        self, *args, **kwargs
    ) -> TrailResult:
        raise NotImplementedError("Trail.run is not implemented")


    def run_sync(
        self, *args, **kwargs
    ) -> TrailResult:
        """Try not to this method directly, use Trail.run instead."""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
        # start a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # run the trail
        result = loop.run_until_complete(self.run(*args, **kwargs))
        # close the event loop
        loop.close()
        return result