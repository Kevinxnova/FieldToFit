"""Owner-approved publication times, always interpreted in Beijing time."""
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Asia/Shanghai')
COLLECT_AT = time(7, 45)
CUTOFF_AT = time(8, 30)
PUBLISH_AT = time(9)
CHECK_AT = time(9, 5)


def local_time(value):
    return value.astimezone(TZ).time()


def cutoff_for(day):
    return datetime.combine(date.fromisoformat(day), CUTOFF_AT, TZ)
