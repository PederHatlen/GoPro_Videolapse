from astral import sun, Observer
from datetime import datetime, timedelta, timezone


def main():
    lat = 62.0075084
    long = 12.1801452

    tz = timezone.utc
    obs = Observer(lat, long)

    now = datetime.now(timezone.utc)
    day = timedelta(days=1)

    events = [
        {"type":"set", "time":sun.sunset(obs, now - day, tz)},
        {"type":"rise", "time":sun.sunrise(obs, now, tz)},
        {"type":"noon", "time":sun.noon(obs, now, tz)},
        {"type":"set", "time":sun.sunset(obs, now, tz)},
        {"type":"rise", "time":sun.sunrise(obs, now + day, tz)}
    ]

    last = {}
    for e in events:
        if now < e["time"]: return {"last":last, "next":e}
        else: last = e

    return False

if __name__ == "__main__":
    print(main())