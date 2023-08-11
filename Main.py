#!/usr/bin/env python
import subprocess
from time import sleep

import serial
import wx
import wx.adv
import wx.lib.inspection
import wx.lib.mixins.inspection

import sys
import os
import esptool
import threading
import json
import images as images
from serial import SerialException
from serial.tools import list_ports
from esptool import ESPLoader
from esptool import NotImplementedInROMError
from esptool import FatalError
from argparse import Namespace
import gettext
from shutil import which

# Load the import & initialize the firmware_list
import brewflasher_com_integration
firmware_list = brewflasher_com_integration.FirmwareList()

import locale
import platform
# import sentry_sdk
# sentry_sdk.init(
#     "http://36f4457e97c34b169aaa9014920c6e5e@sentry.optictheory.com:9000/12",
#     traces_sample_rate=0.0
# )
def get_language_code():
    # getdefaultlocale returns a tuple where first element is 'language_encoding'
    lang_encoding = locale.getdefaultlocale()

    if lang_encoding is not None and lang_encoding[0] is not None:
        # The language code is the first two characters of the locale string
        return lang_encoding[0][0:2]
    else:
        if platform.system() == 'Darwin':
            # For MacOS we need to use the Foundation framework to get the language code. This is because the
            # getdefaultlocale() function returns None for the language code on MacOS in instances where the language
            # and the location do not match (ie. English language in Germany). This is a known issue with Python on
            # MacOS. See https://bugs.python.org/issue18378 for more details.
            import objc
            from Foundation import NSLocale
            # # Get the NSLocale class
            # NSLocaleClass = objc.lookUpClass('NSLocale')

            # Use the class method 'currentLocale' to retrieve the current locale
            language_code = NSLocale.preferredLanguages()[0][0:2]
            return language_code
        # Force fallback to English
        return None

# Bundle_dir makes sure this works when frozen with PyInstaller
bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__))) # get the bundle dir if bundled or simply the __file__ dir if not bundled
localedir = os.path.abspath(os.path.join(bundle_dir, 'locales'))
translate = gettext.translation('brewflasher', localedir, languages=[get_language_code()], fallback=True)
_ = translate.gettext

__version__ = "1.5.1"
# __flash_help__ = '''
# <p>This setting depends on your device - but in most cases you will want to use DIO.<p>
# <p>
# <ul>
#   <li>Most ESP32 and ESP8266 ESP-12 use DIO.</li>
#   <li>Most ESP8266 ESP-01/07 use QIO.</li>
#   <li>ESP8285 requires DOUT.</li>
# </ul>
# </p>
# <p>
#   For more information, details are found at at <a style="color: #004CE5;"
#         href="https://www.esp32.com/viewtopic.php?p=5523&sid=08ef44e13610ecf2a2a33bb173b0fd5c#p5523">http://bit.ly/2v5Rd32</a>
#   and in the <a style="color: #004CE5;" href="https://github.com/espressif/esptool/#flash-modes">esptool
#   documentation</a>
#
# </p>
# '''
__auto_select__ = _("Auto-select")
__auto_select_explanation__ = _("(first port with Espressif device)")
__supported_baud_rates__ = [9600, 57600, 74880, 115200, 230400, 460800, 921600]


# ---------------------------------------------------------------------------
def has_avrdude() -> bool:
    if which("avrdude") is not None or which("avrdude.exe") is not None:
        return True
    else:
        return False


# See discussion at http://stackoverflow.com/q/41101897/131929
class RedirectText:
    def __init__(self, text_ctrl):
        self.__out = text_ctrl

    def write(self, string):
        if string.startswith("\r"):
            # carriage return -> remove last line i.e. reset position to start of last line
            current_value = self.__out.GetValue()
            last_newline = current_value.rfind("\n")
            new_value = current_value[:last_newline + 1]  # preserve \n
            new_value += string[1:]  # chop off leading \r
            wx.CallAfter(self.__out.SetValue, new_value)
        else:
            wx.CallAfter(self.__out.AppendText, string)

    # noinspection PyMethodMayBeStatic
    def flush(self):
        # noinspection PyStatementEffect
        None

    def isatty(self):
        return False

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
class FlashingThread(threading.Thread):
    def __init__(self, parent, config):
        threading.Thread.__init__(self)
        self.daemon = True
        self._parent = parent
        self._config = config

    def run(self):
        command = []

        # Fermentrack-specific config options
        if self._config.project_string == "" or  self._config.project_id is None:
            print(_("Must select the project, device family, and firmware to flash before flashing."))
            return
        if self._config.device_family_string == "" or self._config.device_family_id is None:
            print(_("Must select the project, device family, and firmware to flash before flashing."))
            return
        if self._config.firmware_string == "" or self._config.firmware_obj is None:
            print(_("Must select the project, device family, and firmware to flash before flashing."))
            return

        print(_("Verifying firmware list is up-to-date before downloading..."))
        if not self._config.firmware_obj.pre_flash_web_verify(brewflasher_version=__version__):
            print(_("Firmware list is not up to date.") + " " + _("Relaunch BrewFlasher and try again."))
            return

        print(_("Downloading firmware..."))
        device_family = firmware_list.DeviceFamilies[self._config.firmware_obj.family_id]
        if self._config.firmware_obj.download_to_file(device_family=device_family):
            print(_("Downloaded successfully!\n"))
        else:
            print(_("Error - unable to download firmware.\n"))
            return

        # This is where the paths for flashing with esptool and avrdude diverge.
        if self._config.device_family_flash_method == "esptool":
            # ESPTool flashing is pretty much the same as Arduino, except that it calls avrdude directly using
            # subprocess. All of this could almost certainly get cleaned up.
            if self._config.device_family_string == "ESP32" or self._config.device_family_string == "ESP32-S2" or \
                    self._config.device_family_string == "ESP32-C3":
                if self._config.device_family_string == "ESP32":
                    # This command matches the ESP32 flash options JSON from BrewFlasher.com
                    command_extension = ["--chip", "esp32",
                                         "--baud", str(self._config.baud),
                                         "--before", "default_reset", "--after", "hard_reset",
                                         "write_flash",  "0x10000",
                                         self._config.firmware_obj.full_filepath("firmware")]
                elif self._config.device_family_string == "ESP32-S2":
                    # This command matches the ESP32-S2 flash options JSON from BrewFlasher.com
                    command_extension = ["--chip", "esp32s2",
                                         "--baud", str(self._config.baud),
                                         "--before", "default_reset", "--after", "hard_reset",
                                         "write_flash", "-z", "--flash_mode", "dio", "--flash_freq", "80m",
                                         "0x10000",
                                         self._config.firmware_obj.full_filepath("firmware")]
                elif self._config.device_family_string == "ESP32-C3":
                    # This command matches the ESP32-C3 flash options JSON from BrewFlasher.com
                    command_extension = ["--chip", "esp32c3",
                                         "--baud", str(self._config.baud),
                                         "--before", "default_reset", "--after", "hard_reset",
                                         "write_flash", "-z", "--flash_mode", "dio", "--flash_freq", "80m",
                                         "0x10000",
                                         self._config.firmware_obj.full_filepath("firmware")]
                else:
                    print(_("Invalid device family detected.") + " " + _("Relaunch BrewFlasher and try again."))
                    return

                # For the ESP32, we can flash a custom partition table if we need it. If this firmware template involves
                # flashing a partition table, lets add that to the flash request
                if len(self._config.firmware_obj.download_url_partitions) > 0 and len(
                        self._config.firmware_obj.checksum_partitions) > 0:
                    command_extension.append("0x8000")
                    command_extension.append(self._config.firmware_obj.full_filepath("partitions"))

                # For now, I'm assuming bootloader flashing is ESP32 only
                if len(device_family.download_url_bootloader) > 0 and \
                        len(device_family.checksum_bootloader) > 0:
                    if self._config.device_family_string == "ESP32-C3":
                        command_extension.append("0x0")
                    else:
                        command_extension.append("0x1000")
                    command_extension.append(self._config.firmware_obj.full_filepath("bootloader"))

            elif self._config.device_family_string == "ESP8266":
                command_extension = ["--chip", "esp8266",
                                     "write_flash",
                                     # "--flash_mode", self._config.mode,
                                     "0x00000",
                                     self._config.firmware_obj.full_filepath("firmware")]
            else:
                print(_("Invalid device family detected.") + " " + _("Relaunch BrewFlasher and try again."))
                return

            # For both ESP32 and ESP8266 we can directly flash an image to SPIFFS/LittleFS
            if len(self._config.firmware_obj.download_url_spiffs) > 0 and \
                    len(self._config.firmware_obj.checksum_spiffs) > 0 and \
                    len(self._config.firmware_obj.spiffs_address) > 2:
                # We need to flash SPIFFS. The location is dependent on the partition scheme
                command_extension.append(self._config.firmware_obj.spiffs_address)
                command_extension.append(self._config.firmware_obj.full_filepath("spiffs"))

            # For both ESP32 and ESP8266 we can directly flash an image to the otadata section
            if len(device_family.download_url_otadata) > 0 and \
                    len(device_family.checksum_otadata) > 0 and \
                    len(device_family.otadata_address) > 2:
                # We need to flash the otadata section. The location is dependent on the partition scheme
                command_extension.append(device_family.otadata_address)
                command_extension.append(self._config.firmware_obj.full_filepath("otadata"))

            if not self._config.port.startswith(__auto_select__):
                command.append("--port")
                command.append(self._config.port)
            elif self._config.device_family_1200_bps:
                # For some reason, this code never executes (at least on Mac OS)
                print(_("ERROR - Cannot automatically select the serial port for this device family. Please explicitly "
                      "select the correct device to continue."))
                return

            # command.extend(["--baud", str(self._config.baud),
            #                 "--after", "no_reset",
            #                 "write_flash",
            #                 "--flash_mode", self._config.mode,
            #                 "0x00000", self._config.firmware_path])
            command.extend(command_extension)

            if self._config.erase_before_flash:
                command.append("--erase-all")

            # There is a breaking change in esptool 3.0 that changes the flash size from detect to keep. We want to
            # support "detect" by default.
            command.append("-fs")
            command.append("detect")

            # For certain devices (such as the ESP32-S2) there is a requirement that we open a brief connection to the
            # controller at 1200bps to signal to the controller that it should set itself into a flashable state. We do
            # this using basic pyserial, as esptool doesn't have this functionality built in.
            if self._config.device_family_1200_bps:
                try:
                    sleep(0.1)
                    print(_("Performing 1200 bps touch"))
                    sleep(0.1)
                    ser = serial.Serial(self._config.port, baudrate=1200, timeout=5, write_timeout=0)
                    sleep(1.5)
                    print("...done\n")
                    ser.close()
                except SerialException as e:
                    # sleep(0.1)
                    # self._parent.report_error(e.strerror)
                    sleep(0.1)
                    print(_("...unable to perform 1200bps touch."))

                    print("")
                    print(_("Make sure you have selected the correct serial port (auto-select will not work for this chip) and try again."))
                    print("")
                    print(_("Alternatively, you may need to manually set the device into 'flash' mode."))
                    print("")
                    print(_("For instructions on how to do this, check this website:\nhttp://www.brewflasher.com/manualflash/"))
                    raise e

            print("Command: esptool.py %s\n" % " ".join(command))

            try:
                esptool.main(command)
            except SerialException as e:
                sleep(0.1)
                self._parent.report_error(e.strerror)
                raise e
            except Exception as e:
                sleep(0.1)
                print(_("Firmware flashing FAILED. esptool.py raised an error."))
                print("")
                print(_("Try flashing again, or try flashing with a slower speed."))
                print("")
                if self._config.device_family_1200_bps:
                    print("")
                    print(_("Alternatively, you may need to manually set the device into 'flash' mode."))
                    print("")
                    print(_("For instructions on how to do this, check this website:\nhttp://www.brewflasher.com/manualflash/"))
                # sleep(0.1)
                # sentry_sdk.capture_exception(e)
                return

        elif self._config.device_family_flash_method == "avrdude":
            if not has_avrdude():
                # We can't flash Arduino firmware if we don't have avrdude
                print("")
                print(_("Avrdude was not found. Arduino firmware cannot be flashed."))
                print(_("To install Avrdude, follow the instructions at https://github.com/avrdudes/avrdude/"))
                return

            command = ["avrdude", "-p", "atmega328p", "-c", "arduino", "-P", self._config.port, "-D", "-U",
                       f"flash:w:{self._config.firmware_obj.full_filepath('firmware')}:i"]

            print("Avrdude command: avrdude %s\n" % " ".join(command))

            try:
                subprocess.run(command)
            except SerialException as e:
                sleep(0.1)
                raise e
            except Exception as e:
                sleep(0.1)
                print(_("Firmware flashing FAILED. esptool.py raised an error."))
                print("")
                print(_("Try flashing again, or try flashing with a slower speed."))
                print("")
                if self._config.device_family_1200_bps:
                    print("")
                    print(_("Alternatively, you may need to manually set the device into 'flash' mode."))
                    print("")
                    print(_("For instructions on how to do this, check this website:\nhttp://www.brewflasher.com/manualflash/"))
                # sleep(0.1)
                # sentry_sdk.capture_exception(e)
                return

        else:
            print(_("Invalid device family detected.") + " " + _("Relaunch BrewFlasher and try again."))

        # The last line printed by esptool is "Staying in bootloader." -> some indication that the process is
        # done is needed
        print("")
        print(_("Firmware successfully flashed. Reset device to switch back to normal boot mode."))


# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# DTO between GUI and flashing thread
class FlashConfig:
    def __init__(self):
        self.baud = 115200
        self.erase_before_flash = False
        # self.mode = "dio"
        self.firmware_path = None
        # self.port = None
        self.port = __auto_select__

        # Fermentrack-specific config options
        self.project_string = ""
        self.project_id = None
        self.device_family_string = ""
        self.device_family_id = None
        self.device_family_1200_bps = False
        self.device_family_flash_method = ""
        self.firmware_string = ""
        self.firmware_obj = None

    @classmethod
    def load(cls, file_path):
        conf = cls()
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            # conf.port = data['port']
            conf.baud = data['baud']
            # conf.mode = data['mode']
            conf.erase_before_flash = data['erase']
        return conf

    def safe(self, file_path):
        data = {
            'port': self.port,
            'baud': self.baud,
            # 'mode': self.mode,
            'erase': self.erase_before_flash,
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)

    def is_complete(self):
        return self.firmware_path is not None and self.port is not None

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
class NodeMcuFlasher(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, size=(725, 650),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        self._config = FlashConfig.load(self._get_config_file_path())

        self._build_status_bar()
        self._set_icons()
        self._build_menu_bar()
        self._init_ui()

        sys.stdout = RedirectText(self.console_ctrl)

        self.Centre(wx.BOTH)
        self.Show(True)
        print(_("Connect your device"))
        print("")
        print(_("If you chose the serial port auto-select feature you might need to turn off Bluetooth"))

        if not has_avrdude():
            print("")
            print(_("Avrdude was not found. Arduino firmware cannot be flashed."))
            print(_("To install Avrdude, follow the instructions at https://github.com/avrdudes/avrdude/"))

    def _init_ui(self):
        def on_reload(event):
            self.choice.SetItems(self._get_serial_ports())  # self.choice corresponds to the serial port choice

        def on_baud_changed(event):
            radio_button = event.GetEventObject()

            if radio_button.GetValue():
                self._config.baud = radio_button.rate

        # def on_mode_changed(event):
        #     radio_button = event.GetEventObject()
        #
        #     if radio_button.GetValue():
        #         self._config.mode = radio_button.mode

        def on_erase_changed(event):
            radio_button = event.GetEventObject()

            if radio_button.GetValue():
                self._config.erase_before_flash = radio_button.erase

        def on_clicked(event):
            # todo - Add error messages here
            self.console_ctrl.SetValue("")
            worker = FlashingThread(self, self._config)
            worker.start()

        def on_select_port(event):
            choice = event.GetEventObject()
            self._config.port = choice.GetString(choice.GetSelection())

        def on_select_project(event):
            choice = event.GetEventObject()
            # Set the _config options to our selection (and look up the ID)
            self._config.project_string = choice.GetString(choice.GetSelection())
            self._config.project_id = firmware_list.get_project_id(self._config.project_string)

            # reset the device_family items
            self._config.device_family_string = ""
            self._config.device_family_id = None
            self._config.device_family_flash_method = ""
            self._config.device_family_1200_bps = False
            list_of_device_families = [""] + firmware_list.get_device_family_list(selected_project_id=self._config.project_id)
            self.device_choice.SetItems(list_of_device_families)

            # reset the firmware items
            self._config.firmware_string = ""
            self._config.firmware_obj = None
            list_of_firmware = [""] + firmware_list.get_firmware_list(selected_project_id=self._config.project_id)
            self.firmware_choice.SetItems(list_of_firmware)

        def on_select_device_family(event):
            choice = event.GetEventObject()
            self._config.device_family_string = choice.GetString(choice.GetSelection())
            if len(self._config.device_family_string) > 0:
                self._config.device_family_id = firmware_list.get_device_family_id(self._config.project_id,
                                                                                   self._config.device_family_string)
                self._config.device_family_1200_bps = firmware_list.Projects[self._config.project_id].device_families[self._config.device_family_id].use_1200_bps_touch
                self._config.device_family_flash_method = firmware_list.Projects[self._config.project_id].device_families[self._config.device_family_id].flash_method
            else:
                self._config.device_family_id = None
                self._config.device_family_1200_bps = False
                self._config.device_family_flash_method = ""

            # reset the firmware items
            self._config.firmware_string = ""
            self._config.firmware_obj = None
            list_of_firmware = [""] + firmware_list.get_firmware_list(selected_project_id=self._config.project_id,
                                                                      selected_family_id=self._config.device_family_id)
            self.firmware_choice.SetItems(list_of_firmware)

        def on_select_firmware(event):
            choice = event.GetEventObject()
            self._config.firmware_string = choice.GetString(choice.GetSelection())
            if len(self._config.firmware_string) > 0:
                self._config.firmware_obj = firmware_list.get_firmware(self._config.project_id,
                                                                       self._config.device_family_id,
                                                                       self._config.firmware_string)
            else:
                self._config.firmware_obj = None


        panel = wx.Panel(self)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # (col, row, x, x)
        fgs = wx.FlexGridSizer(9, 2, 10, 10)

        self.choice = wx.Choice(panel, choices=self._get_serial_ports())
        self.choice.Bind(wx.EVT_CHOICE, on_select_port)
        self._select_configured_port()
        bmp = images.Reload.GetBitmap()
        reload_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp,
                                        size=(bmp.GetWidth() + 7, bmp.GetHeight() + 7))
        reload_button.Bind(wx.EVT_BUTTON, on_reload)
        reload_button.SetToolTip(_("Reload serial device list"))

        list_of_projects = [""] + firmware_list.get_project_list()
        self.project_choice = wx.Choice(panel, choices=list_of_projects)
        self.project_choice.Bind(wx.EVT_CHOICE, on_select_project)

        list_of_families = [""] + firmware_list.get_device_family_list()
        self.device_choice = wx.Choice(panel, choices=list_of_families)
        self.device_choice.Bind(wx.EVT_CHOICE, on_select_device_family)

        list_of_firmware = [""] + firmware_list.get_firmware_list()
        self.firmware_choice = wx.Choice(panel, choices=list_of_firmware)
        self.firmware_choice.Bind(wx.EVT_CHOICE, on_select_firmware)


        serial_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        serial_boxsizer.Add(self.choice, 1, wx.EXPAND)
        serial_boxsizer.AddStretchSpacer(0)
        serial_boxsizer.Add(reload_button, 0, 0, 20)

        project_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        project_boxsizer.Add(self.project_choice, 1, wx.EXPAND)

        device_family_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        device_family_boxsizer.Add(self.device_choice, 1, wx.EXPAND)

        firmware_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        firmware_boxsizer.Add(self.firmware_choice, 1, wx.EXPAND)

        baud_boxsizer = wx.BoxSizer(wx.HORIZONTAL)

        def add_baud_radio_button(sizer, index, baud_rate):
            style = wx.RB_GROUP if index == 0 else 0
            radio_button = wx.RadioButton(panel, name="baud-%d" % baud_rate, label="%d" % baud_rate, style=style)
            radio_button.rate = baud_rate
            # sets default value
            radio_button.SetValue(baud_rate == self._config.baud)
            radio_button.Bind(wx.EVT_RADIOBUTTON, on_baud_changed)
            sizer.Add(radio_button)
            sizer.AddSpacer(10)

        for idx, rate in enumerate(__supported_baud_rates__):
            add_baud_radio_button(baud_boxsizer, idx, rate)

        # As of esptool 2.0 flash_mode is autodetected from the firmware. We've also always ignored it for ESP32.
        # flashmode_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        #
        # def add_flash_mode_radio_button(sizer, index, mode, label):
        #     style = wx.RB_GROUP if index == 0 else 0
        #     radio_button = wx.RadioButton(panel, name="mode-%s" % mode, label="%s" % label, style=style)
        #     radio_button.Bind(wx.EVT_RADIOBUTTON, on_mode_changed)
        #     radio_button.mode = mode
        #     radio_button.SetValue(mode == self._config.mode)
        #     sizer.Add(radio_button)
        #     sizer.AddSpacer(10)
        #
        # add_flash_mode_radio_button(flashmode_boxsizer, 0, "qio", "Quad I/O (QIO)")
        # add_flash_mode_radio_button(flashmode_boxsizer, 1, "dio", "Dual I/O (DIO)")
        # add_flash_mode_radio_button(flashmode_boxsizer, 2, "dout", "Dual Output (DOUT)")

        erase_boxsizer = wx.BoxSizer(wx.HORIZONTAL)

        def add_erase_radio_button(sizer, index, erase_before_flash, label, value):
            style = wx.RB_GROUP if index == 0 else 0
            radio_button = wx.RadioButton(panel, name="erase-%s" % erase_before_flash, label="%s" % label, style=style)
            radio_button.Bind(wx.EVT_RADIOBUTTON, on_erase_changed)
            radio_button.erase = erase_before_flash
            radio_button.SetValue(value)
            sizer.Add(radio_button)
            sizer.AddSpacer(10)

        erase = self._config.erase_before_flash
        add_erase_radio_button(erase_boxsizer, 0, False, _("no"), erase is False)
        add_erase_radio_button(erase_boxsizer, 1, True, _("yes, wipes all data"), erase is True)

        button = wx.Button(panel, -1, _("Download Firmware and Flash Controller"))
        button.Bind(wx.EVT_BUTTON, on_clicked)

        self.console_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.console_ctrl.SetFont(wx.Font((0, 13), wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                                          wx.FONTWEIGHT_NORMAL))
        self.console_ctrl.SetBackgroundColour(wx.WHITE)
        self.console_ctrl.SetForegroundColour(wx.BLUE)
        self.console_ctrl.SetDefaultStyle(wx.TextAttr(wx.BLUE))

        port_label = wx.StaticText(panel, label=_("Serial port"))
        project_label = wx.StaticText(panel, label=_("Project") + " ")
        device_family_label = wx.StaticText(panel, label=_("Device Family") + " ")
        firmware_label = wx.StaticText(panel, label=_("Firmware") + " ")
        baud_label = wx.StaticText(panel, label=_("Baud rate") + " ")
        # flashmode_label = wx.StaticText(panel, label="Flash mode ")

        # def on_info_hover(event):
        #     from HtmlPopupTransientWindow import HtmlPopupTransientWindow
        #     win = HtmlPopupTransientWindow(self, wx.SIMPLE_BORDER, __flash_help__, "#FFB6C1", (410, 140))
        #
        #     image = event.GetEventObject()
        #     image_position = image.ClientToScreen((0, 0))
        #     image_size = image.GetSize()
        #     win.Position(image_position, (0, image_size[1]))
        #
        #     win.Popup()
        #
        # icon = wx.StaticBitmap(panel, wx.ID_ANY, images.Info.GetBitmap())
        # icon.Bind(wx.EVT_MOTION, on_info_hover)

        # flashmode_label_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        # flashmode_label_boxsizer.Add(flashmode_label, 1, wx.EXPAND)
        # flashmode_label_boxsizer.AddStretchSpacer(0)
        # flashmode_label_boxsizer.Add(icon, 0, 0, 20)

        erase_label = wx.StaticText(panel, label=_("Erase flash"))
        console_label = wx.StaticText(panel, label=_("Console"))

        fgs.AddMany([
                    port_label, (serial_boxsizer, 1, wx.EXPAND),
                    project_label, (project_boxsizer, 1, wx.EXPAND),
                    device_family_label, (device_family_boxsizer, 1, wx.EXPAND),
                    firmware_label, (firmware_boxsizer, 1, wx.EXPAND),
                    baud_label, baud_boxsizer,
                    # flashmode_label_boxsizer, flashmode_boxsizer,
                    erase_label, erase_boxsizer,
                    (wx.StaticText(panel, label="")), (button, 1, wx.EXPAND),
                    (console_label, 1, wx.EXPAND), (self.console_ctrl, 1, wx.EXPAND)])
        fgs.AddGrowableRow(7, 1)
        fgs.AddGrowableCol(1, 1)
        hbox.Add(fgs, proportion=2, flag=wx.ALL | wx.EXPAND, border=15)
        panel.SetSizer(hbox)

    def _select_configured_port(self):
        count = 0
        for item in self.choice.GetItems():
            if item == self._config.port:
                self.choice.Select(count)
                break
            count += 1

    @staticmethod
    def _get_serial_ports():
        ports = [__auto_select__ + " " + __auto_select_explanation__]
        for port, desc, hwid in sorted(list_ports.comports()):
            ports.append(port)
        return ports

    def _set_icons(self):
        self.SetIcon(images.Icon.GetIcon())

    def _build_status_bar(self):
        self.statusBar = self.CreateStatusBar(2, wx.STB_SIZEGRIP)
        self.statusBar.SetStatusWidths([-2, -1])
        status_text = _("Welcome to BrewFlasher {version}").format(version=__version__)
        self.statusBar.SetStatusText(status_text, 0)

    def _build_menu_bar(self):
        self.menuBar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        wx.App.SetMacExitMenuItemId(wx.ID_EXIT)
        # TODO - Figure out what internationalization needs to take place here
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", _("Exit BrewFlasher"))
        exit_item.SetBitmap(images.Exit.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_exit_app, exit_item)
        self.menuBar.Append(file_menu, "&File")

        # Help menu
        help_menu = wx.Menu()
        help_item = help_menu.Append(wx.ID_ABOUT, '&About BrewFlasher', _('About'))
        self.Bind(wx.EVT_MENU, self._on_help_about, help_item)
        self.menuBar.Append(help_menu, '&Help')

        self.SetMenuBar(self.menuBar)

    @staticmethod
    def _get_config_file_path():
        return wx.StandardPaths.Get().GetUserConfigDir() + "/nodemcu-pyflasher.json"

    # Menu methods
    def _on_exit_app(self, event):
        self._config.safe(self._get_config_file_path())
        self.Close(True)

    def _on_help_about(self, event):
        from About import AboutDlg
        about = AboutDlg(self)
        about.ShowModal()
        about.Destroy()

    def report_error(self, message):
        self.console_ctrl.SetValue(message)

    def log_message(self, message):
        self.console_ctrl.AppendText(message)

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
class MySplashScreen(wx.adv.SplashScreen):
    def __init__(self):
        wx.adv.SplashScreen.__init__(self, images.Splash.GetBitmap(),
                                     wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT, 2500, None, -1)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        # TODO - Rewrite the splash function so as to actually do this in the background
        firmware_list.load_from_website(False)
        self.__fc = wx.CallLater(2000, self._show_main)

    def _on_close(self, evt):
        # Make sure the default handler runs too so this window gets
        # destroyed
        evt.Skip()
        self.Hide()

        # if the timer is still running then go ahead and show the
        # main frame now
        if self.__fc.IsRunning():
            self.__fc.Stop()
            self._show_main()

    def _show_main(self):
        frame = NodeMcuFlasher(None, "BrewFlasher")
        frame.Show()
        if self.__fc.IsRunning():
            self.Raise()

# ---------------------------------------------------------------------------


# ----------------------------------------------------------------------------
class App(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):
        wx.SystemOptions.SetOption("mac.window-plain-transition", 1)
        self.SetAppName("BrewFlasher")

        # Create and show the splash screen.  It will then create and
        # show the main frame when it is time to do so.  Normally when
        # using a SplashScreen you would create it, show it and then
        # continue on with the application's initialization, finally
        # creating and showing the main application window(s).  In
        # this case we have nothing else to do so we'll delay showing
        # the main frame until later (see ShowMain above) so the users
        # can see the SplashScreen effect.
        splash = MySplashScreen()
        splash.Show()

        return True


# ---------------------------------------------------------------------------
def main():
    app = App(False)
    app.MainLoop()
# ---------------------------------------------------------------------------


if __name__ == '__main__':
    __name__ = 'Main'
    main()

