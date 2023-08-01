#! /bin/sh
serverIP="192.168.1.39:5500"

rm VideoLapse.py
wget "${serverIP}/VideoLapse.py"
python3 /home/nrkbeta/VideoLapse.py