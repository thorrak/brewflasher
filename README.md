# BrewFlasher
![BrewFlasher Logo](images/BrewFlasher.png)

A standalone desktop application for flashing brewing-related firmware to your ESP8266 or ESP32.


![Image of NodeMCU PyFlasher GUI](images/gui.png)

## About
BrewFlasher is a standalone desktop application that allows the user to flash specific firmware (upload software) to an 
ESP32 or ESP8266. It will automatically locate the firmare on the internet, download it, and flash it to your chip with 
minimal input required. Simple, fast, and magic.

This project was built as a natural complement to a handful of other projects I either support or collaborate on, where 
a user is expected to flash firmware to an ESP8266 or ESP32 controller. For many users, this step of the installation 
process is the most daunting - either because it requires the use of third-party tools that aren't mentioned in the 
project they want to use, requires the use of the command line, or - in some cases - isn't well explained at all. 
I solved this problem in my [Fermentrack](http://www.fermentrack.com/) project by building in a guided "firmware flash" 
workflow - but this only helps when the user has installed Fermentrack. BrewFlasher was designed to take the best parts 
of the Fermentrack firmware flash workflow and integrate them into a standalone desktop application.


## Supported Firmware
BrewFlasher is designed to specifically support a handful of beer- and brewing-related projects for the ESP32 or 
ESP8266. Those projects include:

- BrewPi-ESP8266
- TiltBridge
- BrewBubbles
- Keg Cop
- Flite
- iSpindHub

If you have a beer- or brewing-related project you would like supported, raise an [issue](https://github.com/thorrak/brewflasher/issues) and we can discuss it. 

If you are looking to flash generic firmware, I recommend the [NodeMCU PyFlasher](https://github.com/marcelstoer/nodemcu-pyflasher) tool that BrewFlasher was based on. It works great for ESP8266 boards (and might work for some ESP32 boards as well)!


## Installation
BrewFlasher doesn't have to be installed; just double-click it and it'll start. BrewFlasher is available for both MacOS
and Windows.



## Background & Development
BrewFlasher is based *heavily* on the [NodeMCU PyFlasher](https://github.com/marcelstoer/nodemcu-pyflasher) project. In 
comparison to that project, BrewFlasher adds explicit ESP32 support as well as a workflow to automate selecting and
downloading brewing-related firmware to flash. The firmware selection is taken from a curated list maintained 
behind-the-scenes on Fermentrack.com.


## License
This package was based on the NodeMCU PyFlasher project which is licensed under [MIT](http://opensource.org/licenses/MIT) 
license, the code for which is © Marcel Stör

All subsequent additions are additionally licensed under the [MIT](http://opensource.org/licenses/MIT) license and are 
© John Beeler

As noted in the license, BrewFlasher is provided without warranty of any kind. As when flashing any microcontroller,
a possibility of damage exists. Be careful, as all use of BrewFlasher is at your own risk. 
