import VideoLapse

camIp = "172.24.151.51"

if not VideoLapse.find(60, camIp):
    print("Cam wasn't found in time")
    VideoLapse.end_procedure()
