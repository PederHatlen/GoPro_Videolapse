'''
Kode for å styre et GoPro Hero 11 Kamera for å ta en video på soloppgang, solnedgang og midt på dagen.


'''
import os
import re
import requests, time, serial, dropbox
from astral import sun, Observer
from datetime import datetime, timedelta, timezone
from ina219 import INA219

# Defs
# Location
latitude = 62.0075084
longitude = 12.1801452

# Sending events to a logging machine
do_debug_logging = True
logger_address = "109.74.200.4:1338" # for testing

# Addresses for devices
GoProIP = "172.24.151.51"
microController_serial = "/dev/ttyS0"

# Dropbox
dropbox_refresh_token = os.environ["DROPBOX_REFRESH_TOKEN"]
dropbox_auth_key = os.environ["DROPBOX_AUTH_KEY"]

clip_length = 30 # Seconds, Needs to be changed in gopro labs as well

tz = datetime.now(timezone.utc).astimezone().tzinfo # Timezone used for dates

# Voltage checking
SHUNT_OHMS = 0.1
MAX_EXPECTED_AMPS = 0.2

ina = INA219(SHUNT_OHMS, MAX_EXPECTED_AMPS)
ina.configure(ina.RANGE_16V)

voltage = ina.voltage() # Voltage is gathered by a Adafruit INA219 Voltage sensor, using the pi-ina219 library
temperature = int(open('/sys/class/thermal/thermal_zone0/temp').read())/1000 # Getting Temperature (raspberry is environment temperature right after boot)

# Sending to the logger computer 
def log_print(data):
    print(data)
    if do_debug_logging:
        try: requests.post(f"http://{logger_address}/add", json={"from":"RPI", "text":data})
        except: print("Could not send to log")

def send_status(volt, temp, next_event, current_event_name):
    # Sending next event as a unix timestamp
    try: requests.post(f"http://{logger_address}/status", json={"volt":volt, "temp":temp, "current_event_name":current_event_name, "next_event":next_event.isoformat()})
    except: log_print("Could not send status")

# Find the gopro cammera by sending requests
def find(timeout, GoProIP):
    expireTime = datetime.now(tz) + timedelta(seconds=timeout)
    while datetime.now(tz) < expireTime:
        try:
            requests.get(f"http://{GoProIP}:8080/gopro/camera/keep_alive", timeout=1)
            log_print(f"Found {GoProIP}")
            return True
        except:
            print(f"Camera {GoProIP} was not found")
        time.sleep(1)
    print("Could not find gopro in time")
    return False

# Get the token needed to upload to dropbox, refresh token and authorization key needed
def get_dropbox_accesskey(dropbox_refresh_token, dropbox_auth_key):
    payload = f'refresh_token={dropbox_refresh_token}&grant_type=refresh_token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f'Basic {dropbox_auth_key}'}
    r = requests.post("https://api.dropboxapi.com/oauth2/token", headers=headers, data=payload)
    return r.json()["access_token"]

# Stream file from gopro to dropbox (dropbox upload sessions, becouse files may be over 150Mb)
def stream_dropbox(clipLink, name=""):
    try:
        # Get the accesskey and making a connection to dropbox, start session and start upload
        dbx = dropbox.dropbox_client.Dropbox(get_dropbox_accesskey(dropbox_refresh_token, dropbox_auth_key))
        upload_session_start_result = dbx.files_upload_session_start(b'')
        cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id, offset=0)

        # Uploading chunk by chunk from datastream
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

        # Finish uploading
        commit = dropbox.files.CommitInfo(path=f"/videos/{localname}")
        dbx.files_upload_session_finish(b'', cursor, commit)

        log_print("Upload completed!")
    except KeyboardInterrupt:
        log_print("Keyboard interupt, Skipping upload...")

# Get the last recorded file from gopro
def get_last_clip(GoProIP):
    log_print(f"Trying to access: http://{GoProIP}:8080/gopro/media/list")
    # log_print(requests.get("http://172.24.151.51:8080/gopro/media/list").text)
    time.sleep(20)
    mediaList = requests.get(f"http://{GoProIP}:8080/gopro/media/list").json()["media"]
    if mediaList == []: return False

    return mediaList[0]["fs"][-1]["n"]

# Delete a clip from gopro
def delete_clip(GoProIP, clipName):
    r = requests.get(f"http://{GoProIP}:8080/gopro/media/delete/file?path=100GOPRO/{clipName}")
    return r.status_code

def delete_all_clips(GoProIP):
    mediaList = requests.get(f"http://{GoProIP}:8080/gopro/media/list").json()["media"][0]['fs']
    for obj in mediaList:
        delete_clip(GoProIP, obj["n"])
        log_print("Deleted %s" % obj["n"])
    return True

# Get event times from the YR api, works great, when internet is connected, but differs a bit from local calculation
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

# Local only calculation of sun, quite fast, but not as accurate as YR
def event_times_local(lat, long):
    now = datetime.now(tz)
    day = timedelta(days=1)
    obs = Observer(lat, long)

    # Getting sun events for all events around a day (sunset yesterday, everything today and sunrise tomorrow)
    events = [
        {"type":"Set", "time":sun.sunset(obs, now - day, tz)},
        {"type":"Rise", "time":sun.sunrise(obs, now, tz)},
        {"type":"Noon", "time":sun.noon(obs, now, tz)},
        {"type":"Set", "time":sun.sunset(obs, now, tz)},
        {"type":"Rise", "time":sun.sunrise(obs, now + day, tz)}
    ]

    # Filtering the events with only the last and the next events
    last = {}
    for e in events:
        if now < e["time"]: return {"last":last, "next":e}
        else: last = e

    return False

# Spoofing the eventtimes, now + 5 minutes
def event_times_fake(lat, long):
    now = datetime.now(tz)
    return {"last":{"type":"Test_Last", "time":now-timedelta(minutes=5)}, "next":{"type":"Test_Next", "time":now+timedelta(minutes=5)}}

# This might need som rewriting/changing
def esp32_shutdown(eventTime, current_event_name):
    voltage = None
    if type(eventTime) == int:
        secondsUntillWakeup = eventTime
    else:
        # next event time - time now - half clip time = seconds untill next clip should start
       secondsUntillWakeup = abs(round(eventTime - datetime.now(tz)).total_seconds() - (clip_length/2))
    log_print(f"Seconds untill next wakeup: {secondsUntillWakeup}")

    # Connecting to esp32
    ser = serial.Serial(microController_serial, 9600)

    ser.write(b"Hello i believe you exist maybe?")

    # while voltage == None:
    #     data = ser.readline().decode('utf-8').strip()
    #     if data:
    #         log_print(f"Received data from serial port: {data}")
    #         match = re.search("(?<=Voltage:)(.*?)(?=\s*;)", data)
    #         if match:
    #             voltage = match.group(0)
    #             log_print(f"Voltage: {voltage}")
    #             break
    #     else:
    #         log_print("did not get voltage from controller")
    #     time.sleep(0.5)

    send_status(voltage, temperature, eventTime, current_event_name)

    log_print("Sending sleep command to stamp")
    ser.write(f"Sleep for {secondsUntillWakeup} seconds\n".encode('ascii'))

    # Shutdown raspberrypi properly
    #call("sudo shutdown -h now", shell=True)
    

# Main function, combines everything
def main():
    events = {}

    ser = serial.Serial(microController_serial, 9600)

    ser.write(b"Booted")

    # split into if the camera is availeable or not
    if not find(30, GoProIP):
        # If camera is not available
        log_print("cam was not found :(")
        events = event_times(latitude, longitude)
        if events["last"]["time"] > (datetime.now(tz)-timedelta(minutes=10)): esp32_shutdown(datetime.now(tz) + timedelta(minutes=1), events["last"]["name"])
    else:
        # If camera is availeable
        # Sleep untill clip is done recording
        try:
            sleeptime = (clip_length)
            if sleeptime < 0: sleeptime = 0
            log_print(f"Sleeping for {sleeptime} seconds")
            time.sleep(sleeptime)
        except KeyboardInterrupt:
            log_print("KeyboardInterrupt, skipping...")

        log_print("Done sleeping")

        # Finding the event after it has pased for better distingtion
        events = event_times(latitude, longitude)

        clipName = get_last_clip(GoProIP)
        clipLink = f"http://{GoProIP}:8080/videos/DCIM/100GOPRO/{clipName}"

        log_print(f"Last clip was {clipName}")

        now = datetime.now(tz)

        try:
            log_print("Trying to upload to dropbox")
            stream_dropbox(clipLink, f"{clipName}_{datetime.strftime(events['last']['time'], '%y-%m-%d_%H-%M-%S')}_Sun{events['last']['type']}.mp4")
            delete_clip(GoProIP, clipName)
            #delete_all_clips(GoProIP)
            uploadTime = (datetime.now(tz)-now).total_seconds()
            log_print(f"Uploading took {uploadTime//60} minutes and {(uploadTime%60)} seconds")
        except Exception as E:
            log_print("something went wrong while uploading/deleting %s" % E)

    events = event_times(latitude, longitude)

    esp32_shutdown(events["next"]["time"], events["last"]["name"])
    

if __name__ == "__main__":
    try:
        main()
    except Exception as E:
        log_print(f"Error occured: {E}")
    
    # If error, wait 1 minute and try again
    while True:
        time.sleep(5)
        try:
            esp32_shutdown(datetime.now(tz) + timedelta(minutes=1), "error")
        except Exception as E:
            log_print(f"Error: {E}")
