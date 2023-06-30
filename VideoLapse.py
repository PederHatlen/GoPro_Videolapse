'''
Kode for å styre et GoPro Hero 11 Kamera for å ta en video på soloppgang, solnedgang og x tidspunkt.

'''

import requests, time, serial, dropbox
from datetime import datetime, timedelta

# from goprocam import GoProCamera

# Defs
fileFormatOut = ".mp4"

camIP = "172.24.151.51"

latitude = 62.0075084
longitude = 12.1801452


def find(timeout, ip):
    expireTime = datetime.now() + timedelta(seconds=timeout)
    while datetime.now() < expireTime:
        try:
            requests.get(f"http://{ip}:8080/gopro/camera/keep_alive", timeout=1)
            print(f"Found {ip}")
            return True
        except requests.exceptions.ConnectTimeout:
            print(f"Camera {ip} was not found")
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
                print(f"Uploading chunk {chunks}, {round((cursor.offset/c_length)*100, 2)}%")
    
    clipName = clipLink.split("/")[-1]
    localname = (name if name != '' else clipName)

    commit = dropbox.files.CommitInfo(path=f"/videos/{localname}")
    dbx.files_upload_session_finish(b'', cursor, commit)

    print("Upload completed!")

def get_last_clip(camIP):
    mediaList = requests.get(f"http://{camIP}:8080/gopro/media/list").json()["media"]
    if mediaList == []: return False

    return mediaList[0]["fs"][-1]["n"]

def delete_clip(camIP, clipName):
    r = requests.get(f"http://{camIP}:8080/gopro/media/delete/file?path=100GOPRO/{clipName}")
    return r.status_code

def event_times():
    neededEvents = ["Rise", "ElevationMax", "Set"]
    last = {}

    yr_APIData = requests.get(f"https://www.yr.no/api/v0/locations/{latitude},{longitude}/celestialevents").json()

    for event in yr_APIData["events"]:
        if event["body"] != "Sun" or event["type"] not in neededEvents: continue

        eventTime = datetime.fromisoformat(event["time"])
        if datetime.now(eventTime.tzinfo) < eventTime:
            return {"last":last, "next":{"time":eventTime, "type":event["type"]}}
        else:
            last = {"time":eventTime, "type":event["type"]}

    return False

def end_procedure(secondsUntillWakeup):
    # Connecting to esp32
    ser = serial.Serial("/dev/tty.usbmodem101", 9600)

    ser.write(b"Hello i believe you exist maybe?")

    print(ser.readline())

    ser.write(bin(secondsUntillWakeup))

# def capture_sdk(ip, clipLength):
#     gpCam = GoProCamera.GoPro(camera="HERO11", ip_address=ip)
#     gpCam.video_settings("4k","50")
#     clipLink = gpCam.shoot_video(clipLength)

#     if clipLink == f"http://{ip}/videos/DCIM//": return False

#     return clipLink

# def capture(ip, cliplength):
#     mediaRaw_pre = requests.get(f"http://{ip}:8080/gopro/media/list").json()["media"]

#     requests.get(f"http://{ip}:8080/gopro/camera/shutter/start")     # Start recording
#     time.sleep(cliplength)                                           # Wait cliptime to stop
#     requests.get(f"http://{ip}:8080/gopro/camera/shutter/stop")      # Stop recording

#     time.sleep(2)

#     mediaRaw_post = requests.get(f"http://{ip}:8080/gopro/media/list").json()["media"]

#     # medialist after - medialist before, to get the clip made in between/get the new clip, and ensure only 1 exist
#     diff = list(set([d["n"] for d in mediaRaw_post]) - set([d["n"] for d in mediaRaw_pre]))

#     if len(diff) != 1:
#         print(f"Clip was not recorded properly: found {len(diff)} clips, expected 1")
#         return False

#     # Get difference of media lists, and get the filename
#     return diff[0]

# def upload(clippath, name):
#     dbx = dropbox.dropbox_client.Dropbox(oauth2_refresh_token=db_refresh, app_key=db_key, app_secret=db_secret)
#     with open(f"{clippath}{name}", 'rb') as f:
#         print(dbx.files_upload(f.read(), f"/{clippath}{name}"))
#     print("Clip uploaded")


def main():
    events = {}
    now = datetime.now()

    # split into if the camera is availeable or not
    if not find(90, camIP):
        print("cam was not found :(")
        events = event_times()
    else:
        # Sleep untill clip is done recording
        time.sleep(90 - (now - datetime.now()).total_seconds())

        # Finding the event after it has pased for better distingtion
        events = event_times()

        clipName = get_last_clip(camIP)
        clipLink = f"http://{camIP}:8080/videos/DCIM/100GOPRO/{clipName}"

        try:
            stream_dropbox(clipLink, f"{datetime.strftime(datetime.now(), '%y-%m-%d_%H-%M-%S')}_Sun{events['last']['type']}.mp4")
            delete_clip(camIP, clipName)
        except Exception as E:
            print("something went wrong while uploading/deleting", E)
    
    secondsUntillWakeup = (events["next"]["time"] - datetime.now(events["next"]["time"].tzinfo)).total_seconds() - (60/2)
    end_procedure(secondsUntillWakeup)
    
    # print(f"{event.lower()} happening in {(timeOfEvent - datetime.now(eventTime.tzinfo)).total_seconds()} seconds")

    # Find if gopro is connected (find function)
    # Capturing clip and uploading to server
    

    # if timeOfEvent != "" and find(timeOfEvent - (padding/2), cameraIP):
    #     time.sleep((timeOfEvent - padding - datetime.now(eventTime.tzinfo)).total_seconds())
    #     print(f"Starting capture of {event}")

    #     clipLink = capture_sdk(cameraIP, clipDuration)

    #     if clipLink != False:
    #         stream_dropbox(clipLink)
    #         print(f"Captured and uploaded {clipLink}")
    
    # Calculating time untill next wakeup
    # And send seconds untill wakeup to the esp32 controller, controlling the system power
    # secondsUntillWakeup = (events[1] - timedelta(seconds=(padding)) - datetime.now(eventTime.tzinfo)).total_seconds()
    # end_procedure(secondsUntillWakeup)

if __name__ == "__main__":
    try:
        main()
    except Exception as E:
        print("Error occured: ", E)
    
    # If error, wait 1 minute and try again
    end_procedure(60)