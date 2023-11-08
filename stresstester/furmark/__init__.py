import os

from ..base import Trail

class Furmark(Trail):
    def __init__(self):
        super().__init__(
            path=os.path.dirname(__file__),
            files=('FurMark-Scores.txt',),
        )

    async def run(self,
        width: int = 1280,
        height: int = 720,
        timeout: int = 30,
        run_mode: int = 1,
    ):
        return await self.exec(
            "FurMark.exe /width={width} /height={height} /nogui /nomenubar /noscore /run_mode={run_mode} "
            + "/log_score /disable_catalyst_warning /msaa=0 /max_time={gpu_time}",
            timeout=timeout,
            width=width,
            height=height,
            gpu_time=(timeout - 8) * 1000,
            run_mode=run_mode,
        )