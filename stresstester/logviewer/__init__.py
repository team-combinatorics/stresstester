import os

from ..base import Trail

class LogViewer(Trail):
    def __init__(self):
        super().__init__(
            path=os.path.dirname(__file__),
            files=(),
        )

    async def run(self, files: tuple[str, ...] = ()):
        return await self.exec(
            "GenericLogViewer.exe {file} {config}",
            config='"' + os.path.join(self.path, 'default.cfg') + '"',
            # quote the file path
            file=' '.join([f'"{f}"' for f in files]),
        )