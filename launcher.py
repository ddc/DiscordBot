#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

try:
    import pip
except ImportError:
    pip = None

import argparse
import os
import subprocess
import sys
import time
import tempfile
import requests
import urllib.request
from src.cogs.bot.utils import constants
from src.cogs.bot.utils import bot_utils as BotUtils
from src.cogs.gw2.utils import gw2_constants as Gw2Constants
from src.cogs.bot.utils.log import Log


def main():
    if constants.IS_WINDOWS:
        os.system("TITLE Discord Bot - Launcher")

    BotUtils.clear_screen()
    while True:
        print(f"{constants.INTRO}\n")
        print("1. Start Bot")
        print("2. Updates")
        print("0. Quit")
        choice = BotUtils.user_choice()
        if choice == "1":
            _run(auto_restart=True)
        elif choice == "2":
            _update_menu()
        elif choice == "0":
            break
        BotUtils.clear_screen()


def _update_menu():
    has_git = BotUtils.is_git_installed()
    BotUtils.clear_screen()
    while True:
        print(f"{constants.INTRO}\n")
        print("Update: (require admin privileges)")
        print("1. Update Bot")
        print("2. Update Requirements")
        print("0. Go back")
        choice = BotUtils.user_choice()
        if choice == "1":
            if not has_git:
                log.error("\nWARNING: Git not found. This means that it's either not "
                          "installed or not in the PATH environment variable.\n"
                          "Git is needed to update the Bot!\n")
            else:
                _update()
                if constants.INTERACTIVE_MODE:
                    BotUtils.wait_return()
        elif choice == "2":
            _update_requirements()
            if constants.INTERACTIVE_MODE:
                BotUtils.wait_return()
        elif choice == "0":
            break
        BotUtils.clear_screen()


def _update_requirements():
    interpreter = sys.executable
    if interpreter is None:
        raise RuntimeError("Python interpreter not found.")

    if pip is None:
        raise RuntimeError("Unable to update.\n"
                           "Pip module is missing.\n"
                           "Please make sure to install Python with pip module.")

    arguments = []
    f = open("requirements/requirements.txt")
    file_contents = f.readlines()
    for line in file_contents:
        foo = line.strip('\n')
        arguments.append(foo)

    BotUtils.clear_screen()
    for module in arguments:
        if module != "pip":
            print(f"\n\n==> Updating: {module}")
            command = interpreter, "-m", "pip", "install", "-U", module
            code = subprocess.call(command)
            if code != 0:
                BotUtils.clear_screen()
                return log.error(f"\nAn error occurred trying to update: {module}\n")

    log.info("PIP should be manually upgraded: python -m pip install --upgrade pip\n")
    log.info("\nAll requirements are up tp date.\n")


def _parse_cli_arguments():
    parser = argparse.ArgumentParser(description="Discord Bot's launcher")
    parser.add_argument("--start", "-s",
                        help="Starts the bot",
                        action="store_true")
    parser.add_argument("--update",
                        help="Update (git)",
                        action="store_true")
    return parser.parse_args()


def _update():
    has_git = BotUtils.is_git_installed()
    if has_git:
        bot_remote_git_url = constants.BOT_REMOTE_GIT_URL
        src_dir = tempfile.mkdtemp()
        dst_dir = dirname
        subprocess.call(("git", "clone", "--depth=50", "--branch=master", bot_remote_git_url, src_dir))
        BotUtils.recursive_overwrite(src_dir, dst_dir)
        log.info("\nBot was updated successfully.\n")
    else:
        log.error("\nWARNING: Unable to update.\n"
                  "Git installation was not found.\n"
                  "If you want to update, please install Git.\n"
                  f"{constants.GIT_URL}\n")


def _run(auto_restart):
    interpreter = sys.executable
    if interpreter is None:  # This should never happen
        raise RuntimeError("Python interpreter not found.")

    code = 0
    output = ""
    e = ""
    cmd = [interpreter, "bot.py"]
    while True:
        try:
            process = subprocess.run(cmd, check=True, universal_newlines=True)
            output = process.stdout
            code = process.returncode
        except Exception as e:
            code = 0
            break

        if code == 0:
            break
        elif code == 26:
            print(f"Restarting in {constants.TIME_BEFORE_START} secs...")
            time.sleep(constants.TIME_BEFORE_START)
            continue
        else:
            if not auto_restart:
                break

    log.error(f"Bot has been terminated.[Exit code:{code} {output} {e}]")
    if constants.INTERACTIVE_MODE:
        BotUtils.wait_return()


def _check_new_version():
    version_url_file = constants.VERSION_URL_FILE
    req = requests.get(version_url_file)
    client_version = constants.VERSION
    if req.status_code == 200:
        remote_version = req.text
        if remote_version[-2:] == "\\n" or remote_version[-2:] == "\n":
            remote_version = remote_version[:-2]  # getting rid of \n at the end of line

        if float(remote_version) > float(client_version):
            return True
        else:
            return False
    else:
        log.error("ERROR: VERSION file was not found.\n")


def _check_config_files():
    if not os.path.exists("logs"):
        os.makedirs("logs")

    if not os.path.exists(constants.SETTINGS_FILENAME):
        src_url = constants.SETTINGS_URL_FILE
        dst = constants.SETTINGS_FILENAME
        try:
            urllib.request.urlretrieve(src_url, dst)
        except urllib.request.HTTPError as e:
            log.error("ERROR: Could not download settings file.\n"
                      f"{e}.\n{src_url}\n"
                      "Exiting...")
            exit(1)
            return

    if not os.path.exists(Gw2Constants.GW2_SETTINGS_FILENAME):
        src_url = Gw2Constants.GW2_SETTINGS_URL_FILE
        dst = Gw2Constants.GW2_SETTINGS_FILENAME
        try:
            urllib.request.urlretrieve(src_url, dst)
        except urllib.request.HTTPError as e:
            log.error("ERROR: Could not download GW2 settings file.\n"
                      f"{e}.\n{src_url}\n"
                      "Exiting...")
            exit(1)
            return


if __name__ == '__main__':
    log = Log(constants.LOGS_DIR, constants.DEBUG).setup_logging()
    args = _parse_cli_arguments()
    _check_config_files()
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)

    os.chdir(dirname)
    if not constants.PYTHON_OK:
        log.error("Python 3.6 or higher is required. Please install the required version.\n"
                  "Press enter to continue...")
        if constants.INTERACTIVE_MODE:
            BotUtils.wait_return()
        exit(1)

    if pip is None:
        log.error("Bot cannot work without the pip module.\n"
                  "Please make sure to install Python with pip module.")
        if constants.INTERACTIVE_MODE:
            BotUtils.wait_return()
        exit(1)

    if args.update:
        print(sys.argv[1])
        _update()

    if constants.INTERACTIVE_MODE:
        if _check_new_version():
            _update()
        main()
    elif args.start:
        print(f"Launching in {constants.TIME_BEFORE_START} secs... ({sys.argv[1]})")
        time.sleep(constants.TIME_BEFORE_START)
        _run(auto_restart=True)
