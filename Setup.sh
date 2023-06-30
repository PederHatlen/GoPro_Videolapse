#! /bin/sh

serverIP="192.168.1.39:5500"

sudo apt update
sudo apt -y install python3.9 libpython3.9-dev python3-pip tmux

python3 -m pip install requests pyserial dropbox

rm -f /home/nrkbeta/VideoLapse.py
wget "${serverIP}/VideoLapse.py" -O /home/nrkbeta/VideoLapse.py

rm -f /lib/systemd/system/VideoLapse.service
sudo wget "${serverIP}/VideoLapse.service" -O /lib/systemd/system/VideoLapse.service
sudo chmod 644 /lib/systemd/system/VideoLapse.service

sudo systemctl daemon-reload
sudo systemctl enable VideoLapse.service

# sudo shutdown -r now