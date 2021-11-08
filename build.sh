#!/usr/bin/env bash
#rm -fr build dist
#VERSION=1.2
#NAME=BrewFlasher

pyinstaller --log-level=INFO \
            --noconfirm \
            --target-arch x86_64 \
            build-on-mac.spec

#https://github.com/sindresorhus/create-dmg
#create-dmg dist/$NAME-$VERSION.app
#mv "$NAME-$VERSION 0.0.0.dmg" dist/$NAME-$VERSION.dmg
