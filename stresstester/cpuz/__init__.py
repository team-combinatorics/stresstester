import os

from ..base import Trail, TrailResult

class CPUZ(Trail):
    def __init__(self):
        super().__init__(
            path=os.path.dirname(__file__),
            files=('*.txt',),
        )

    def txt_to_scores(self, txt_path: str):
        _text = ''

        with open(txt_path, 'r', encoding='gbk') as f:
            # read the last line
            _text = f.readlines()[-1]
            _l, _r = _text.split(',', 1)
            _l = float(_l.strip().replace('"', ''))
            _r = float(_r.strip().replace('"', ''))
            return _l, _r

    async def run(
        self, *args, **kwargs
    ) -> TrailResult:
        r = await self.exec(
            "cpuz.exe -bench"
        )
        if len(r.files) < 1:
            raise ValueError(f"Got {len(r.files)} files, expected at least 1")

        _single, _multi = self.txt_to_scores(r.files[0])
        _str = f"Single:\t{_single}\nMulti:\t{_multi}\n"
        _value = {
            'single': _single,
            'multi': _multi,
        }
        return TrailResult(
            string=_str,
            value=_value,
            files=r.files,
            start_timestamp=r.start_timestamp,
            complete_timestamp=r.complete_timestamp,
        )