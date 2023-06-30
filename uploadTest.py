import VideoLapse, time

clipLink = VideoLapse.capture_sdk("172.24.128.51", 10)

VideoLapse.stream_dropbox(clipLink, f"{time.strftime('%Y-%m-%d_%H-%M-%S')}_test.mp4")