# BrewFlasher
![BrewFlasher Logo](images/BrewFlasher.png)

A standalone desktop application for flashing brewing-related firmware to your ESP8266, ESP32, ESP32-C3 or ESP32-S2.


###### Espanol

BrewFlasher es una aplicación de escritorio independiente que permite al usuario actualizar o flashear un firmware específico (y subir un software) a un ESP32, ESP32-S2 o un ESP8266. BrewFlasher ubicará automáticamente el firmware en Internet, lo descargará y lo flasheará a tu chip sin ningún otro esfuerzo. Simple, rápido y mágico. 

###### Deutsche

BrewFlasher ist eine eigenständige Desktopanwendung, welche es Nutzern erlaubt, spezifische Firmware auf einen ESP32, ESP32-S2 oder ESP8266 zu flashen (installieren). Es findet die benötigte Firmware aus dem Internet und flasht sie eigenständig auf deinen Chip. Einfach, schnell und magisch.

###### Svenska

BrewFlasher är en desktop applikation för att programmera mjukvara till projekt med fokus på bryggning.

###### Norsk

BrewFlasher er en programvare som gir brukeren mulighet til å flashe spesifikk firmware (laste opp programvaren til en ESP32, ESP32-S2 eller ESP8266 chip. Programmet vil automatisk finne firmware på internett, laste ned det, og flashe det til din chip med få valg. Enkelt, raskt og magisk.

## About

![Image of BrewFlasher GUI](images/gui.png)

BrewFlasher is a standalone desktop application that allows the user to flash specific firmware (upload software) to an 
ESP32, ESP32-S2, or ESP8266. It will automatically locate the firmware on the internet, download it, and flash it to 
your chip with minimal input required. Simple, fast, and magic.

This project was built as a natural complement to a handful of other projects I either support or collaborate on, where 
a user is expected to flash firmware to an ESP8266, ESP32, or ESP32-S2 controller. For many users, this step of the 
installation process is the most daunting - either because it requires the use of third-party tools that aren't 
mentioned in the project they want to use, requires the use of the command line, or - in some cases - isn't well 
explained at all. I solved this problem in my [Fermentrack](http://www.fermentrack.com/) project by building in a guided
"firmware flash" workflow - but this only helps when the user has installed Fermentrack. BrewFlasher was designed to 
take the best parts of the Fermentrack firmware flash workflow and integrate them into a standalone desktop application.


## Supported Firmware
BrewFlasher is designed to specifically support a handful of beer- and brewing-related projects for the ESP32, ESP32-S2,
or ESP8266. Those projects include:

- BrewPi-ESP (ESP32, ESP8266, and ESP32-S2)
- TiltBridge
- BrewBubbles
- Keg Cop
- Flite
- iSpindHub
- SBL4TILT
- GravityMon
- FermWatch
- BrewUNO

An up-to-date list of supported firmware can be found at the [BrewFlasher](https://www.brewflasher.com/about/supported_projects/) website.

If you have a beer- or brewing-related project you would like supported, raise an [issue](https://github.com/thorrak/brewflasher/issues) and we can discuss it. 

If you are looking to flash generic firmware, I recommend the [NodeMCU PyFlasher](https://github.com/marcelstoer/nodemcu-pyflasher) tool that BrewFlasher was based on. It works great for ESP8266 boards (and might work for some ESP32 boards as well)!


## Installation

### MacOS and Windows releases

Download the latest [release](https://github.com/thorrak/brewflasher/releases). BrewFlasher doesn't have to be installed; just double-click it and it'll start.

### Running from python source on Linux

You can run BrewFlasher on Linux as follows:

    git clone git@github.com:thorrak/brewflasher.git; cd brewflasher
    pip install -r requirements.txt # you may need to e.g. `apt install libgtk-3-dev` for wxPython
    python Main.py

The [esptool.py](https://docs.espressif.com/projects/esptool/en/latest/esp32/index.html) utility may require that your user can access e.g. `/dev/ttyUSB0`:

    sudo usermod -a -G dialout
    su - $USER # to pick-up the new group in the shell

## Manually toggling "Flash" Mode

[Deutsche / Español](http://www.brewflasher.com/manualflash/)

For certain chips (e.g. ESP32-S2) the USB-to-serial functionality is provided by the controller itself rather than a 
separate piece of hardware. For these chips, you may be required to manually set the controller into "flash" mode before 
BrewFlasher can install new firmware. Below is the process for doing this for the Lolin S2 mini -- other controllers
are likely similar (though the "0" button may be labeled something else, like "boot" or "flash")

1. Plug the Lolin S2 Mini into your computer
2. Hold down the "0" button on the right of the board
3. While continuing to hold the "0" button, press the "RST" button on the left of the board
4. Wait several seconds, then release the "0" button
5. Flash your controller with the desired firmware
6. Manually press the "RST" button on the left of the board to reset the controller once flashing is complete


## Background & Development
BrewFlasher is based *heavily* on the [NodeMCU PyFlasher](https://github.com/marcelstoer/nodemcu-pyflasher) project. In 
comparison to that project, BrewFlasher adds explicit ESP32 & ESP32-S2 support as well as a workflow to automate selecting and
downloading brewing-related firmware to flash. The firmware selection is taken from a curated list maintained 
behind-the-scenes on BrewFlasher.com.

### Special Thank You

A special THANK YOU goes out to the following people who assisted with translating BrewFlasher into other languages:

- **Deutsche**: TheySaidGetAnAlt on Reddit
- **Español**: iloverentmusical on Reddit
- **Svenska**: @mp-se
- **Norsk**: bardevjen on HomeBrewTalk

Interested in helping translate BrewFlasher, or have suggestions to improve one of the translations? Please reach out - either on HomeBrewTalk or by raising an issue/pull request here on GitHub!




## License
This package was based on the NodeMCU PyFlasher project which is licensed under [MIT](http://opensource.org/licenses/MIT) 
license, the code for which is © Marcel Stör

All subsequent additions are additionally licensed under the [MIT](http://opensource.org/licenses/MIT) license and are 
© John Beeler

As noted in the license, BrewFlasher is provided without warranty of any kind. As when flashing any microcontroller,
a possibility of damage exists. Be careful, as all use of BrewFlasher is at your own risk. 
