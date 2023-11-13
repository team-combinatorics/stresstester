import os
from stresstester.base import Trail, TrailResult

class BatteryInfo(Trail):
    def __init__(self):
        super().__init__(
            path=os.path.dirname(__file__),
            files=('battery.csv',),
        )

    def csv_to_str(self, csv_path: str):
        _text = ''
        with open(csv_path, 'r', encoding='gbk') as f:
            for l in f.readlines():
                _l, _r = l.split(',', 1)
                # remove ',' in _r
                _r = _r.replace(',', '')
                _l, _r = _l.strip(), _r.strip()
                if not _r or _l == 'Description':
                    continue
                _text += f"{_l}:\t{_r}\n"
        return _text

    async def run(self) -> TrailResult:
        r = await self.exec(
            "BatteryInfoView.exe /scomma battery.csv"
        )
        _csv_path = os.path.join(self.path, 'battery.csv')
        return TrailResult(
            string=self.csv_to_str(_csv_path) if os.path.exists(_csv_path) else None,
            value=None,
            files=r.files,
            start_timestamp=r.start_timestamp,
            complete_timestamp=r.complete_timestamp,
        )