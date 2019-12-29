@echo off
chcp 65001
echo.
pushd %~dp0

::Attempts to start py launcher without relying on PATH
%SYSTEMROOT%\py.exe --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO attempt
%SYSTEMROOT%\py.exe -3 -m pip install -U pip
%SYSTEMROOT%\py.exe -3 -m pip install -U discord.py[voice]
%SYSTEMROOT%\py.exe -3 -m pip install -U requests
%SYSTEMROOT%\py.exe -3 -m pip install -U asyncpg
%SYSTEMROOT%\py.exe -3 -m pip install -U beautifulsoup4
%SYSTEMROOT%\py.exe -3 -m pip install -U imgurpython
%SYSTEMROOT%\py.exe -3 -m pip install -U GitPython
%SYSTEMROOT%\py.exe -3 -m pip install -U gTTS
PAUSE
GOTO end

::Attempts to start py launcher by relying on PATH
:attempt
py.exe --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO attempt2
py.exe -3 -m pip install -U pip
py.exe -3 -m pip install -U discord.py[voice]
py.exe -3 -m pip install -U requests
py.exe -3 -m pip install -U asyncpg
py.exe -3 -m pip install -U beautifulsoup4
py.exe -3 -m pip install -U imgurpython
py.exe -3 -m pip install -U GitPython
py.exe -3 -m pip install -U gTTS
PAUSE
GOTO end

::Attempts to start whatever python.exe there is
:attempt2
python.exe --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO lastattempt
python.exe -m pip install -U pip
python.exe -m pip install -U discord.py[voice]
python.exe -m pip install -U requests
python.exe -m pip install -U asyncpg
python.exe -m pip install -U beautifulsoup4
python.exe -m pip install -U imgurpython
python.exe -m pip install -U GitPython
python.exe -m pip install -U gTTS
PAUSE
GOTO end

::As a last resort, attempts to start pip
:lastattempt
pip --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO message
pip install -U pip
pip install -U discord.py[voice]
pip install -U requests
pip install -U asyncpg
pip install -U beautifulsoup4
pip install -U imgurpython
pip install -U GitPython
pip install -U gTTS
PAUSE
GOTO end

:message
clear
echo Couldn't find a valid Python ^>3.7 installation. Python needs to be installed and available in the PATH environment
echo variable.
echo Download Python at: https://www.python.org/downloads/releases
PAUSE

:end
