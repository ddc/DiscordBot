#!/bin/bash
set +e

PYTHON3=$(whereis python3 | awk '{ print $2 }')
PKG_CONFIG_PATH=/opt/vc/lib/pkgconfig:/usr/lib/arm-linux-gnueabihf/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig:/usr/local/lib/pkgconfig:/usr/local/pgsql/lib/pkgconfig:$PKG_CONFIG_PATH:
export PKG_CONFIG_PATH

sudo apt-get update
sudo apt-get install -y libsqlite3-dev
sudo apt-get install -y libperl-dev
sudo apt-get install -y python3-pip
sudo apt-get install -y python3-dev
sudo apt-get install -y python3-pip
sudo apt-get install -y python3-setuptools
sudo apt-get install -y python3-distutils
#sudo apt-get install -y libgtk2.0-dev
#sudo apt-get install -y libssl-dev
#sudo apt-get install -y libffi-dev
#sudo apt-get install -y ffmpeg

sudo "$PYTHON3" -m pip install -r ../requirements.txt
#sudo pip-review --local --interactive
#sudo pip-review --local --auto
