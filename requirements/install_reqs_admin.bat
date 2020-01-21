@echo off
chcp 65001
echo.
pushd %~dp0

::Attempts to start py launcher without relying on PATH
%SYSTEMROOT%\py.exe --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO attempt
%SYSTEMROOT%\py.exe -3 -m pip install -r ../requirements.txt
PAUSE
GOTO end

::Attempts to start py launcher by relying on PATH
:attempt
py.exe --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO attempt2
py.exe -3 -m pip install -r ../requirements.txt
PAUSE
GOTO end

::Attempts to start whatever python.exe there is
:attempt2
python.exe --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO lastattempt
python.exe -m pip install -r ../requirements.txt
PAUSE
GOTO end

::As a last resort, attempts to start pip
:lastattempt
pip --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO message
pip install -r ../requirements.txt
PAUSE
GOTO end

:message
clear
echo Couldn't find a valid Python ^>3.7 installation. Python needs to be installed and available in the PATH environment
echo variable.
echo Download Python at: https://www.python.org/downloads/releases
PAUSE

:end
