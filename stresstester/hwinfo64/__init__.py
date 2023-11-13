import logging
import time
import os
import asyncio
import subprocess
import glob
import pyautogui
import psutil

from ..base import Trail, TrailResult
from ..utils import pick_latest_file

class HwInfo64(Trail):
    def __init__(self):
        super().__init__(
            path=os.path.dirname(__file__),
            files=('*.csv',)
        )

    async def _before(self):
        """Register hotkey"""
        await self.exec(
            'reg add "HKCU\SOFTWARE\HWiNFO64\Sensors" /v AutoLoggingHotKey /t REG_DWORD /d 00000116 /f"'
        )

    async def _exec(self, timeout):
        """Run HWiNFO64.exe"""
        await asyncio.sleep(.5)
        self._res = await self.exec(
            "HWiNFO64.exe", timeout=timeout
        )

    def _press_f5(self):
        try:
            logging.info("Pressing F5 with pyautogui")
            pyautogui.press('f5')
            time.sleep(.5)
            assert glob.glob(os.path.join(self.path, '*.csv')), "Logs were not generated"
        except Exception as e:
            logging.warning(f"Failed to press hotkey: {e}")
            logging.info("Pressing F5 with vbs")
            subprocess.check_call(f'CScript.exe "{os.path.join(self.path, "hotkey.vbs")}"', timeout=1)

    def _after(self):
        """Press F5"""
        time.sleep(5)
        for _ in range(3):
            self._press_f5()
            time.sleep(1)
            if glob.glob(os.path.join(self.path, '*.csv')):
                break
        else:
            logging.warning("Logs were not generated")

    def _exec_sync(self, timeout):
        """Run HWiNFO64.exe"""
        logging.info(f"Registering hotkey")
        logging.info(
            subprocess.check_output(
                'reg add "HKCU\SOFTWARE\HWiNFO64\Sensors" /v AutoLoggingHotKey /t REG_DWORD /d 00000116 /f"'
            ).decode('gbk')
        )

        self._process_sync = subprocess.Popen(
            "HWiNFO64.exe",
            cwd=self.path,
            shell=True,
        )
        # start process, record its pid
        logging.info(f"HWiNFO64.exe (cwd={self.path}, timeout={timeout}, pid={self._process_sync.pid})")
        # press hotkey
        time.sleep(5)
        self._after()
        # sleep for timeout
        time.sleep(timeout)
        # stop logging
        self._press_f5()
        # kill process
        time.sleep(1)
        logging.warning(f"Terminating HWiNFO64.exe after {timeout} seconds")
        self._terminate_sync()

    def _terminate_sync(self):
        try:
            # terminate all child processes
            parent = psutil.Process(self._process_sync.pid)
            for child in parent.children():
                child.terminate()
            self._process_sync.terminate()
        except psutil.NoSuchProcess as e:
            print(f"Trail {self._process_sync.pid} may have already terminated")
            print(e)

    async def terminate(self):
        ## Don't execute in executor
        # loop = asyncio.get_running_loop()
        # fut = loop.run_in_executor(None, self._terminate_sync)
        # try:
        #     await asyncio.wait_for(fut, timeout=5)
        # except asyncio.TimeoutError:
        #     print(f"Failed to terminate {self._process_sync.pid} after 5 seconds")

        try:
            self._terminate_sync()
        except Exception as e:
            print(f"Failed to terminate {self._process_sync.pid}")
            print(e)

    async def run(self, timeout: int = 30):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._exec_sync, timeout)

        files = glob.glob(os.path.join(self.path, '*.csv'))

        return TrailResult(
            start_timestamp=time.time(),
            complete_timestamp=time.time(),
            files=(pick_latest_file(files),) if files else (),
            string='',
            value=None,
        )

