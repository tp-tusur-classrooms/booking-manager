from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

UNIVERSITY_TIMEZONE = ZoneInfo("Asia/Tomsk")


@dataclass(frozen=True, slots=True)
class Period:
    """Фактический полуоткрытый интервал; не привязан к виду занятости."""

    starts_at: datetime
    ends_at: datetime

    @classmethod
    def on_date(cls, day: date, start: time, end: time) -> "Period":
        return cls(
            datetime.combine(day, start, UNIVERSITY_TIMEZONE),
            datetime.combine(day, end, UNIVERSITY_TIMEZONE),
        )

    @classmethod
    def day(cls, day: date) -> "Period":
        return cls(
            datetime.combine(day, time.min, UNIVERSITY_TIMEZONE),
            datetime.combine(day + timedelta(days=1), time.min, UNIVERSITY_TIMEZONE),
        )
