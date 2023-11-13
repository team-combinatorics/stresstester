import os

from ..base import Trail

class LSHW(Trail):
    def __init__(self):
        super().__init__(
            path=os.path.dirname(__file__),
            files=('hwinfo.ini','PnPDevice.ini'),
        )

    def out_to_value(self, s: str):
        """
        Parses the output of 硬件检测引擎.exe and returns a dict.
        """
        # remove content after last \n
        s = s[:s.rfind('\n')]
        lines = s.splitlines()
        r = {}
        k, v = 'ERR', 'ERR'
        for l in lines:
            if not l.strip():
                continue
            if ':' in l:
                k, v = l.split(':', 1)
                r[k.strip()] = [v.strip()]
            else:
                r[k].append(l.strip())
        return r
    
    async def run(self):
        for _to_check in ("lshw.exe", "data", "lshw.dll"):
            if not os.path.exists(os.path.join(self.path, _to_check)):
                raise FileNotFoundError(f"{os.path.join(self.path, _to_check)} not found")

        return await self.exec("lshw.exe")
    