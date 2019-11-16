#!/bin/bash
set +e

PYTHON3="/usr/bin/python3"
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

sudo $PYTHON3 -m pip install -U pip
sudo $PYTHON3 -m pip install -U discord.py[voice]
sudo $PYTHON3 -m pip install -U requests
sudo $PYTHON3 -m pip install -U asyncpg
sudo $PYTHON3 -m pip install -U beautifulsoup4
sudo $PYTHON3 -m pip install -U imgurpython
sudo $PYTHON3 -m pip install -U GitPython
#sudo pip-review --local --interactive
#sudo pip-review --local --auto
