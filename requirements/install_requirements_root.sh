#!/bin/bash
set +e

sudo apt-get install -y ffmpeg
sudo apt-get install -y libssl-dev
sudo apt-get install -y libffi-dev
sudo apt-get install -y libsqlite3-dev

sudo python3 -m pip install -U pip
sudo python3 -m pip install -U discord.py[voice]
sudo python3 -m pip install -U requests
sudo python3 -m pip install -U asyncpg
sudo python3 -m pip install -U beautifulsoup4
sudo python3 -m pip install -U imgurpython
sudo python3 -m pip install -U GitPython
