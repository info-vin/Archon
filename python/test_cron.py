from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger

tz = ZoneInfo("Asia/Taipei")
trigger = CronTrigger(day_of_week='tue,fri,sat,sun', hour=10, minute=30, timezone=tz)

now = datetime.now(tz)
midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

print("Midnight:", midnight)
next_time = trigger.get_next_fire_time(None, midnight)
print("Next Fire Time from Midnight:", next_time)
