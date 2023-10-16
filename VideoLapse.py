'''
Kode for å styre et GoPro Hero 11 Kamera for å ta en video på soloppgang, solnedgang og midt på dagen.


'''
import os
import requests, time, serial, dropbox, json
from astral import sun, Observer
from datetime import datetime, timedelta, timezone
from ina219 import INA219

gps_serial = "/dev/serial/by-id/usb-SimTech__Incorporated_SimTech__Incorporated_0123456789ABCDEF-if05-port0"
s = serial.Serial("%s" % gps_serial, baudrate=115200, timeout=3)
s.write(b"AT\r\n")
s.write(b"AT+CGPS=1\r\n")
s.close()


# Defs
# Location
STATIC_LATITUDE = 62.0075084
STATIC_LONGITUDE = 12.1801452


# Sending events to a logging machine
do_debug_logging = True
logger_address = "dev.nrkalpha.com:2448" # for testing

# Addresses for devices
GoProIP = "172.24.151.51"
microController_serial = "/dev/ttyS0"

# Dropbox
dropbox_refresh_token = os.environ["DROPBOX_REFRESH_TOKEN"]
dropbox_auth_key = os.environ["DROPBOX_AUTH_KEY"]

clip_length = 30 # Seconds, Needs to be changed in gopro labs as well

tz = datetime.now(timezone.utc).astimezone().tzinfo # Timezone used for dates

temperature = int(open('/sys/class/thermal/thermal_zone0/temp').read())/1000 # Getting Temperature (raspberry is environment temperature right after boot)

# Sending to the logger computer 
def log_print(data):
    print(data)
    if do_debug_logging:
        try: requests.post(f"http://{logger_address}/log", json={"from":"RPI", "text":data})
        except: print("Could not send to log")

def send_status(volt, temp, next_event, current_event_name):
    # Sending next event as a unix timestamp
    try: requests.post(f"http://{logger_address}/status", json={"volt":volt, "temp":temp, "current_event_name":current_event_name, "next_event":next_event.isoformat()})
    except: log_print("Could not send status")

def convert_to_decimal(coord, direction):
    # Split the input string into degrees and minutes
    degree_length = 2 if direction in ['N', 'S'] else 3
    degrees = float(coord[:degree_length])
    minutes = float(coord[degree_length:])
    # Convert to decimal format
    decimal = degrees + (minutes / 60)
    # Check the direction for south and west coordinates, which should be negative
    if direction in ['S', 'W']:
        decimal = -decimal 
    return decimal

def write_gps_position():
    gps_serial = "/dev/serial/by-id/usb-SimTech__Incorporated_SimTech__Incorporated_0123456789ABCDEF-if05-port0"
    s = serial.Serial("%s" % gps_serial, baudrate=115200, timeout=3)
    gps_location_found = False
    tries = 0
    max_tries = 20
    while tries < max_tries:
        s.write(b"AT+CGPSINFO\r\n")
        for line in s.readlines():
            #print(line)
            if line.startswith("+CGPSINFO".encode()):
                log_print("Found CGPSINFO line: {line}")
            if line.startswith("+CGPSINFO".encode()) and ',,,,,,'.encode() not in line:
                #print(line)
                data_str = line.replace(b'+CGPSINFO: ', b'').decode('utf-8').strip().split(',')
                lat = convert_to_decimal(data_str[0], data_str[1])
                lng = convert_to_decimal(data_str[2], data_str[3])
                with open('gps_position.json', 'w') as fp:
                    data = {"lat": lat, "lng": lng, "dt": time.time()}
                    fp.write(json.dumps(data))
                    log_print("Wrote new GPS location data!!! {lat} {lng}")
                gps_location_found = True
                break
        tries += 1

def get_gps_position():
    if not os.path.exists('gps_position.json'):
        with open('gps_position.json', 'w') as fp:
            data = {"lat": STATIC_LATITUDE, "lng": STATIC_LONGITUDE, "dt": time.time()}
            fp.write(json.dumps(data))
            log_print("Wrote initial GPS location data based on static data from VideoLapse.py {STATIC_LATITUDE} {STATIC_LONGITUDE}")
    with open('gps_position.json') as fp:
        data = json.load(fp)
        time_since_last_update = round(time.time()-data["dt"])
        log_print(f'Fetched GPS info from file. Lat: {data["lat"]} Lng: {data["lng"]} Updated {time_since_last_update} seconds ago')
        return (data["lat"], data["lng"])

latitude, longitude = get_gps_position()


def get_voltage(SHUNT_OHMS = 0.1, MAX_EXPECTED_AMPS = 0.2):
    # Voltage is gathered by a Adafruit INA219 Voltage sensor, using the pi-ina219 library
    try:
        ina = INA219(SHUNT_OHMS, MAX_EXPECTED_AMPS)
        ina.configure(ina.RANGE_16V)
        return ina.voltage()
    except Exception as E:
        log_print(f"Error ocured while trying to get voltage: {E} \nSending voltage = 0 instead")
        return '0'

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
    # time.sleep(20)
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

    # on rise +1
    # on set -1

    log_print(f"Fetching data from YR for location {lat} {long}")
    yr_APIData = requests.get(f"https://www.yr.no/api/v0/locations/{lat},{long}/celestialevents").json()
    log_print("Got data from YR for location {lat} {long}")
    for event in yr_APIData["events"]:
        if event["body"] != "Sun" or event["type"] not in neededEvents: continue

        eventTime = datetime.fromisoformat(event["time"]).replace(tzinfo=tz)

        # Workaround because recording triggered too early/late
        if event["type"] == "Rise":
            eventTime = eventTime + timedelta(hours=1)
        if event["type"] == "Set":
            eventTime = eventTime - timedelta(hours=1)
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
        {"type":"Set", "time":sun.sunset(obs, now - day, tz)-timedelta(hours=1)},
        {"type":"Rise", "time":sun.sunrise(obs, now, tz)+timedelta(hours=1)},
        {"type":"Noon", "time":sun.noon(obs, now, tz)},
        {"type":"Set", "time":sun.sunset(obs, now, tz)-timedelta(hours=1)},
        {"type":"Rise", "time":sun.sunrise(obs, now + day, tz)+timedelta(hours=1)}
    ]

    # Filtering the events with only the last and the next events
    last = {}
    for e in events:
        # Adding an hour to current time if fired before real event-time
        if (now + timedelta(hours=1)) < e["time"]: return {"last":last, "next":e}
        else: last = e

    return False

# Spoofing the eventtimes, now + 5 minutes
def event_times_fake(lat, long):
    now = datetime.now(tz)
    return {"last":{"type":"Test_Last", "time":now-timedelta(minutes=5)}, "next":{"type":"Test_Next", "time":now+timedelta(minutes=5)}}

# This might need som rewriting/changing
def esp32_shutdown(eventTime, current_event_name):
    # Connecting to esp32
    ser = serial.Serial(microController_serial, 9600)

    ser.write(b"Hello i believe you exist maybe?")

    send_status(get_voltage(), temperature, eventTime, current_event_name)

    # next event time - time now - half clip time = seconds untill next clip should start
    secondsUntillWakeup = abs(round((eventTime - datetime.now(tz)).total_seconds()) - (clip_length/2))
    log_print(f"Seconds untill next wakeup: {secondsUntillWakeup}")

    log_print("Sending sleep command to stamp")
    ser.write(f"Sleep for {secondsUntillWakeup} seconds\n".encode('ascii'))


# Main function, combines everything
def main():
    events = {}

    ser = serial.Serial(microController_serial, 9600)

    ser.write(b"Booted")

    # split into if the camera is availeable or not
    if not find(clip_length, GoProIP):
        # If camera is not available
        log_print("cam was not found :(")
        events = event_times_local(latitude, longitude)
        if events["last"]["time"] > (datetime.now(tz)-timedelta(minutes=10)): esp32_shutdown(datetime.now(tz) + timedelta(minutes=1), events["last"]["type"])
    else:
        # If camera is availeable
        # Sleep untill clip is done recording
        try:
            log_print(f"Waiting for {clip_length//2} seconds before trying to access videos on GoPro")
            time.sleep(clip_length/2)
        except KeyboardInterrupt:
            log_print("KeyboardInterrupt, skipping...")

        log_print("Done waiting")

        # Finding the event after it has pased for better distingtion
        events = event_times_local(latitude, longitude)

        clipName = get_last_clip(GoProIP)
        clipLink = f"http://{GoProIP}:8080/videos/DCIM/100GOPRO/{clipName}"

        if not clipName:
            log_print("Did not find any clips")
            esp32_shutdown(events["next"]["time"], events["last"]["type"])
            return

        log_print(f"Last clip was {clipName}")

        now = datetime.now(tz)

        try:
            log_print("Trying to upload to dropbox")
            stream_dropbox(clipLink, f"{clipName}_{datetime.strftime(events['last']['time'], '%y-%m-%d_%H-%M-%S')}_Sun{events['last']['type']}.mp4")
            delete_clip(GoProIP, clipName)
            #delete_all_clips(GoProIP)
            uploadTime = (datetime.now(tz)-now).total_seconds()
            log_print(f"Uploading took {uploadTime//60} minutes and {round(uploadTime%60)} seconds (total seconds was: {uploadTime})")
            write_gps_position()
        except Exception as E:
            log_print("something went wrong while uploading/deleting %s" % E)
    esp32_shutdown(events["next"]["time"], events["last"]["type"])
    

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
