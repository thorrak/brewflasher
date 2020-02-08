#!/usr/bin/env bash
#rm -fr build dist
VERSION=1.0
NAME=BrewFlasher

pyinstaller --log-level=DEBUG \
            --noconfirm \
            build-on-mac.spec

#https://github.com/sindresorhus/create-dmg
#create-dmg dist/$NAME-$VERSION.app
#mv "$NAME-$VERSION 0.0.0.dmg" dist/$NAME-$VERSION.dmg
