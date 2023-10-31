import logging
import time
from ..stresstester.base import Trail, TrailResult
from datetime import datetime
import os
import asyncio
import subprocess
import glob
import pyautogui
import psutil

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
            logging.info("Pressing F5 | vbs")
            subprocess.check_call(f'CScript.exe "{os.path.join(self.path, "hotkey.vbs")}"', timeout=1)
        except Exception as e:
            logging.warning(f"Failed to press hotkey: {e}")
            logging.info("Pressing F5 | pyautogui")
            pyautogui.press('f5')

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
        logging.info(f"HWiNFO64.exe started with pid {self._process_sync.pid}")
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
        if not hasattr(self, "_process_sync"):
            return
        # terminate all child processes
        parent = psutil.Process(self._process_sync.pid)
        for child in parent.children(): 
            child.terminate()
        self._process_sync.terminate()

    async def terminate(self):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._terminate_sync)

    async def run(self, timeout: int = 30):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._exec_sync, timeout)

        files = glob.glob(os.path.join(self.path, '*.csv'))

        # convert files to utf-8
        for f in files:
            self.gbk_file_to_utf8(f)

        return TrailResult(
            start_timestamp=time.time(),
            complete_timestamp=time.time(),
            files=files,
            string='',
            value=None,
        )

