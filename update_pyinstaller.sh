#!/usr/bin/env bash

# This script rebuilds the bootloaders so as to not have differing signatures from the system that is doing the main
# application build. This is required for notarization to work on MacOS (and may prevent security warnings on Windows)

# Note - this command (at least the "pip install" bit) needs to be done from within the virtualenv
git clone https://github.com/pyinstaller/pyinstaller.git
cd pyinstaller
git checkout v4.7
cd bootloader
python ./waf all
pip install ..

