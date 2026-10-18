from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class ExportPeriod:
    key: str
    today: date
    start: date | None

    @classmethod
    def create(cls, key: str, today: date):
        if key not in {'3', '6', '12', 'total'}:
            raise ValueError('Período inválido')
        if key == 'total':
            return cls(key, today, None)
        index = today.year * 12 + today.month - int(key)
        return cls(key, today, date(index // 12, index % 12 + 1, 1))

    @property
    def label(self):
        return 'Todo o histórico' if self.start is None else f'{self.start:%d/%m/%Y} a {self.today:%d/%m/%Y}'


@dataclass
class ExportResult:
    path: Path
    filename: str
    timings: dict[str, float]
    counts: dict[str, int]
    file_sizes: dict[str, int]
