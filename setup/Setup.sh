#! /bin/sh

sudo apt update
sudo apt -y install python3 libpython3-dev python3-pip tmux

curl -fsSL https://tailscale.com/install.sh | sh

python3 -m pip install requests pyserial dropbox astral pi-ina219

rm -f /home/nrkbeta/VideoLapse.py
wget "https://raw.github.com/PederHatlen/GoPro_Videolapse/main/VideoLapse.py" -O /home/nrkbeta/VideoLapse.py

rm -f /lib/systemd/system/VideoLapse.service
sudo wget "https://raw.github.com/PederHatlen/GoPro_Videolapse/main/setup/VideoLapse.service" -O /lib/systemd/system/VideoLapse.service
sudo chmod 644 /lib/systemd/system/VideoLapse.service

sudo systemctl daemon-reload
sudo systemctl enable VideoLapse.service

read -p "Dropbox refresh token: " dropbox_refresh_token
read -p "Dropbox auth key: " dropbox_auth_key

sudo echo "export DROPBOX_REFRESH_TOKEN=" >> "/etc/profile"
sudo echo "export DROPBOX_AUTH_KEY=" >> "/etc/profile"

sudo tailscale up

sudo shutdown -r now