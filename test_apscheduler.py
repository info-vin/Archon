import datetime
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
tz = ZoneInfo("Asia/Taipei")
trigger = CronTrigger(day_of_week='tue,fri,sat,sun', hour=10, minute=30, timezone=tz)

now = datetime.datetime.now(tz)
print(f"Trigger fields: hour={trigger.fields[5].expressions[0]}, minute={trigger.fields[6].expressions[0]}")
