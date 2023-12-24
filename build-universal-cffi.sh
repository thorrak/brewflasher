#!/usr/bin/env bash

#source ./venv/bin/activate

git clone https://github.com/python-cffi/cffi.git
cd cffi
git fetch
git reset --hard
git checkout v1.16.0

python3 -m pip install build pytest

# The proper SDKROOT can be found by running `xcrun --sdk macosx --show-sdk-path` -- right now, it's 14.0
MACOSX_DEPLOYMENT_TARGET='11.0' SDKROOT=macosx14.0 python3 -m build -w .
cd ..

python3 -m pip install cffi/dist/cffi-*universal2.whl --force-reinstall

# python3 -m pytest .
