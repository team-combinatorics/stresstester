import os

from ..base import Trail

class Prime95(Trail):
    def __init__(self):
        super().__init__(
            path=os.path.dirname(__file__),
        )

    async def run(self,
        timeout: int = 30
    ):
        return await self.exec(
            "prime95.exe -t",
            timeout=timeout,
        )