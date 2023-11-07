import os
from stresstester.base import Trail


class BatteryInfo(Trail):
    def __init__(self):
        super().__init__(
            path=os.path.dirname(__file__),
            files=('battery.csv',),
        )

    async def run(self):
        return await self.exec(
            "batteryinfoview.exe /scomma battery.csv"
        )