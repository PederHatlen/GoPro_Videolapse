from ..VideoLapse import event_times, event_times_local
from datetime import datetime, timezone

latitude = 62.0075084
longitude = 12.1801452

tz = datetime.now(timezone.utc).astimezone().tzinfo

online = event_times(latitude, longitude)
local = event_times_local(latitude, longitude)
datetime.strftime(online["last"]["time"], '%y/%m/%d %H:%M:%S')
print("Online:")
print(f"\tLast: {datetime.strftime(online['last']['time'], '%y/%m/%d %H:%M:%S')}, {online['last']['type']}")
print(f"\tNext: {datetime.strftime(online['next']['time'], '%y/%m/%d %H:%M:%S')}, {online['next']['type']}")

print("\nLocal:")
print(f"\tLast: {datetime.strftime(local['last']['time'], '%y/%m/%d %H:%M:%S')}, {local['last']['type']}")
print(f"\tNext: {datetime.strftime(local['next']['time'], '%y/%m/%d %H:%M:%S')}, {local['next']['type']}")