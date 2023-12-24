#!/usr/bin/env bash
#rm -fr build dist
#VERSION=1.7.0
#NAME=BrewFlasher

source ./venv/bin/activate
python3 compile_languages.py locales
# NOTE - pyobjc must be installed or you cannot launch the app from the bundle (only the console app will work)
# See: https://github.com/pyinstaller/pyinstaller/issues/7841
pip install pyobjc
# NOTE -- YOU NEED TO RUN THE BELOW COMMAND MANUALLY!
./venv/bin/pyinstaller --log-level=INFO --noconfirm build-on-mac-m1.spec

#https://github.com/sindresorhus/create-dmg
#create-dmg dist/$NAME-$VERSION.app
#mv "$NAME-$VERSION 0.0.0.dmg" dist/$NAME-$VERSION.dmg
