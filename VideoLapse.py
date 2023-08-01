'''
Kode for å styre et GoPro Hero 11 Kamera for å ta en video på soloppgang, solnedgang og x tidspunkt.

'''

import requests, time, serial, dropbox
from astral import sun, Observer
from datetime import datetime, timedelta, timezone
from subprocess import call

# Defs
fileFormatOut = ".mp4"

clip_length = 30

camIP = "172.24.151.51"
microController_serial = "/dev/ttyS0"

latitude = 62.0075084
longitude = 12.1801452

tz = datetime.now(timezone.utc).astimezone().tzinfo

# Sending to the logger computer 
def log_print(data):
    print(data)
    if do_debug_logging:
        try: requests.post(f"http://{logger_address}/add", json={"from":"RPI", "data":data})
        except: print("Could not send to log")

def find(timeout, camIP):
    expireTime = datetime.now(tz) + timedelta(seconds=timeout)
    while datetime.now(tz) < expireTime:
        try:
            requests.get(f"http://{camIP}:8080/gopro/camera/keep_alive", timeout=1)
            log_print(f"Found {camIP}")
            return True
        except:
            print(f"Camera {camIP} was not found")
        time.sleep(1)
    print("Could not find gopro in time")
    return False

def get_dropbox_accesskey():
    payload = 'refresh_token=[refresh_token]&grant_type=refresh_token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic [Authentification]'}
    r = requests.post("https://api.dropboxapi.com/oauth2/token", headers=headers, data=payload)
    return r.json()["access_token"]

def stream_dropbox(clipLink, name=""):
    dbx = dropbox.dropbox_client.Dropbox(get_dropbox_accesskey())
    upload_session_start_result = dbx.files_upload_session_start(b'')
    cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id, offset=0)

    with requests.get(clipLink, stream=True) as r:
        print(r.headers)
        c_length = int(r.headers['Content-Length'])
        chunks = 0
        for chunk in r.iter_content(chunk_size=4*1024*1024):
            if chunk: 
                dbx.files_upload_session_append_v2(chunk, cursor)
                cursor.offset += len(chunk)
                chunks += 1
                log_print(f"Uploading chunk {chunks}, {round((cursor.offset/c_length)*100, 2)}%")
    
    clipName = clipLink.split("/")[-1]
    localname = (name if name != '' else clipName)

    commit = dropbox.files.CommitInfo(path=f"/videos/{localname}")
    dbx.files_upload_session_finish(b'', cursor, commit)

    log_print("Upload completed!")

def get_last_clip(camIP):
    mediaList = requests.get(f"http://{camIP}:8080/gopro/media/list").json()["media"]
    if mediaList == []: return False

    return mediaList[0]["fs"][-1]["n"]

def delete_clip(camIP, clipName):
    r = requests.get(f"http://{camIP}:8080/gopro/media/delete/file?path=100GOPRO/{clipName}")
    return r.status_code

def event_times(lat, long):
    neededEvents = ["Rise", "ElevationMax", "Set"]
    last = {}

    yr_APIData = requests.get(f"https://www.yr.no/api/v0/locations/{lat},{long}/celestialevents").json()

    for event in yr_APIData["events"]:
        if event["body"] != "Sun" or event["type"] not in neededEvents: continue

        eventTime = datetime.fromisoformat(event["time"]).replace(tzinfo=tz)
        if datetime.now(tz) < eventTime:
            return {"last":last, "next":{"time":eventTime, "type":event["type"]}}
        else:
            last = {"time":eventTime, "type":event["type"]}

    return False

def event_times_local(lat, long):
    now = datetime.now(tz)
    day = timedelta(days=1)
    obs = Observer(lat, long)

    events = [
        {"type":"Set", "time":sun.sunset(obs, now - day, tz)},
        {"type":"Rise", "time":sun.sunrise(obs, now, tz)},
        {"type":"Noon", "time":sun.noon(obs, now, tz)},
        {"type":"Set", "time":sun.sunset(obs, now, tz)},
        {"type":"Rise", "time":sun.sunrise(obs, now + day, tz)}
    ]

    last = {}
    for e in events:
        if now < e["time"]: return {"last":last, "next":e}
        else: last = e

    return False

def event_times_fake(lat, long):
    now = datetime.now(tz)
    return {"last":{"type":"Test", "time":now-timedelta(seconds=80)}, "next":{"type":"Test", "time":now+timedelta(seconds=80)}}

def esp32_shutdown(secondsUntillWakeup):
    # Connecting to esp32
    ser = serial.Serial(microController_serial, 9600)

    ser.write(b"Hello i believe you exist maybe?")
    print(ser.readline())

    ser.write(str(secondsUntillWakeup).encode('ascii'))

    call("sudo shutdown -h now", shell=True)
    

def main():
    global events

    ser = serial.Serial(microController_serial, 9600)

    ser.write(b"Booted")

    # split into if the camera is availeable or not
        log_print("cam was not found :(")
        events = event_times_local(latitude, longitude)
        if events["last"]["time"] > (datetime.now(tz)-timedelta(minutes=10)):
            esp32_shutdown(10)
    else:
        # Sleep untill clip is done recording
        try:
            sleeptime = (clip_length - 20)
            if sleeptime < 0: sleeptime = 0
            log_print(f"Sleeping for {sleeptime} seconds")
            time.sleep(sleeptime)
        except KeyboardInterrupt:
            log_print("KeyboardInterrupt, skipping...")

        log_print("Done sleeping")

        # Finding the event after it has pased for better distingtion
        events = event_times_local(latitude, longitude)

        clipName = get_last_clip(camIP)
        clipLink = f"http://{camIP}:8080/videos/DCIM/100GOPRO/{clipName}"

        log_print(f"Last clip was {clipName}")

        now = datetime.now(tz)

        try:
            log_print("Trying to upload to dropbox")
            stream_dropbox(clipLink, f"{datetime.strftime(now, '%y-%m-%d_%H-%M-%S')}_Sun{events['last']['type']}.mp4")
            delete_clip(camIP, clipName)
            uploadTime = (datetime.now(tz)-now).total_seconds()
            log_print(f"Uploading took {uploadTime//60} minutes and {round(uploadTime%60)} seconds")
        except Exception as E:
            log_print("something went wrong while uploading/deleting", E)
    secondsUntillWakeup = (events["next"]["time"] - datetime.now(tz)).total_seconds() - (clip_length/2)
    log_print(f"Seconds untill next wakeup: {secondsUntillWakeup}")

    esp32_shutdown(round(secondsUntillWakeup))
    


if __name__ == "__main__":
    try:
        main()
    except Exception as E:
        log_print(f"Error occured: {E}")
    
    # If error, wait 1 minute and try again
    while True:
        time.sleep(5)
        try:
            esp32_shutdown(10)
        except Exception as E:
            log_print(f"Error: {E}")