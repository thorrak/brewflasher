import requests
import copy

FERMENTRACK_COM_URL = "http://www.fermentrack.com"


class Project:
    def __init__(self, name="", weight=0, description="", support_url="", id=0, project_url="", documentation_url=""):
        self.name = name
        self.weight = weight
        self.description = description
        self.support_url = support_url
        self.id = id
        self.project_url = project_url
        self.documentation_url = documentation_url

        self.device_families = {}

    def __str__(self):
        return self.name


class Firmware:
    def __init__(self, name="", version="", revision="", family_id=0, variant="", is_fermentrack_supported="",
                 in_error="", description="", variant_description="", download_url="", id=0, project_id=0,
                 project_url="", documentation_url="", weight="", download_url_partitions="",
                 download_url_spiffs="", checksum="", checksum_partitions="", checksum_spiffs="", spiffs_address=""):
        self.name = name
        self.version = version
        self.revision = revision
        self.family_id = family_id
        self.variant = variant
        self.is_fermentrack_supported = is_fermentrack_supported
        self.in_error = in_error
        self.description = description
        self.variant_description = variant_description
        self.download_url = download_url
        self.project_url = project_url
        self.documentation_url = documentation_url
        self.weight = weight
        self.download_url_partitions = download_url_partitions
        self.download_url_spiffs = download_url_spiffs
        self.checksum = checksum
        self.checksum_partitions = checksum_partitions
        self.checksum_spiffs = checksum_spiffs
        self.spiffs_address = spiffs_address
        self.id = id
        self.project_id = project_id

    def __str__(self):
        return self.name


class DeviceFamily:
    def __init__(self, name="", flash_method="", id=0, detection_family=""):
        self.name = name
        self.flash_method = flash_method
        self.detection_family = detection_family
        self.id = id
        self.firmware = []

    def __str__(self):
        return self.name


# FirmwareList is intended as a singleton
class FirmwareList:
    def __init__(self):
        self.DeviceFamilies = {}
        self.Projects = {}

        self.valid_family_ids = []  # Used to store the ESP IDs, since that's all we can use here to flash

    def __str__(self):
        return "Device Families"

    def load_projects_from_website(self) -> bool:
        try:
            url = FERMENTRACK_COM_URL + "/api/project_list/all/"
            response = requests.get(url)
            data = response.json()
        except:
            return False

        if len(data) > 0:
            for row in data:
                try:
                    # This gets wrapped in a try/except as I don't want this failing if the local copy of Fermentrack
                    # is slightly behind what is available at Fermentrack.com (eg - if there are new device families)
                    newProject = Project(name=row['name'], weight=row['weight'], id=row['id'],
                                         description=row['description'], support_url=row['support_url'],
                                         project_url=row['project_url'], documentation_url=row['documentation_url'])
                    self.Projects[row['id']] = copy.deepcopy(newProject)
                except:
                    pass

            return True
        return False  # We didn't get data back from Fermentrack.com, or there was an error

    def load_families_from_website(self) -> bool:
        try:
            url = FERMENTRACK_COM_URL + "/api/firmware_family_list/"
            response = requests.get(url)
            data = response.json()
        except:
            return False

        if len(data) > 0:
            for row in data:
                try:
                    # This gets wrapped in a try/except as I don't want this failing if the local copy of Fermentrack
                    # is slightly behind what is available at Fermentrack.com (eg - if there are new device families)
                    newFamily = DeviceFamily(name=row['name'], flash_method=row['flash_method'], id=row['id'],
                                             detection_family=row['detection_family'])
                    if newFamily.flash_method == "esptool":  # Only save families that use esptool
                        self.DeviceFamilies[newFamily.id] = copy.deepcopy(newFamily)
                        self.valid_family_ids.append(newFamily.id)
                        for this_project in self.Projects:
                            self.Projects[this_project].device_families[newFamily.id] = copy.deepcopy(newFamily)
                except:
                    pass

            return True
        return False  # We didn't get data back from Fermentrack.com, or there was an error

    def load_firmware_from_website(self) -> bool:
        # This is intended to be run after load_families_from_website
        try:
            url = FERMENTRACK_COM_URL + "/api/firmware_list/all/"
            response = requests.get(url)
            data = response.json()
        except:
            return False

        if len(data) > 0:
            # Then loop through the data we received and recreate it again
            for row in data:
                try:
                    # This gets wrapped in a try/except as I don't want this failing if the local copy of Fermentrack
                    # is slightly behind what is available at Fermentrack.com (eg - if there are new device families)
                    newFirmware = Firmware(
                        name=row['name'], version=row['version'], revision=row['revision'], family_id=row['family_id'],
                        variant=row['variant'], is_fermentrack_supported=row['is_fermentrack_supported'],
                        in_error=row['in_error'], description=row['description'],
                        variant_description=row['variant_description'], download_url=row['download_url'],
                        project_url=row['project_url'], documentation_url=row['documentation_url'],
                        weight=row['weight'],
                        download_url_partitions=row['download_url_partitions'],
                        download_url_spiffs=row['download_url_spiffs'], checksum=row['checksum'],
                        checksum_partitions=row['checksum_partitions'], checksum_spiffs=row['checksum_spiffs'],
                        spiffs_address=row['spiffs_address'], project_id=row['project_id'],
                    )
                    if newFirmware.family_id in self.valid_family_ids:  # The firmware is for an ESP of some sort
                        # Add the firmware to the appropriate DeviceFamily's list
                        self.DeviceFamilies[newFirmware.family_id].firmware.append(newFirmware)
                        self.Projects[newFirmware.project_id].device_families[newFirmware.family_id].firmware.append(
                            newFirmware)
                except:
                    pass

            return True  # Firmware table is updated
        return False  # We didn't get data back from Fermentrack.com, or there was an error

    def cleanse_projects(self):
        for this_project_id in list(self.Projects):
            this_project = self.Projects[this_project_id]
            for this_device_family_id in list(
                    this_project.device_families):  # Iterate the list as we're deleting members
                this_device_family = this_project.device_families[this_device_family_id]
                if len(this_device_family.firmware) <= 0:
                    # If there aren't any firmware instances in this device family, delete it
                    del this_project.device_families[this_device_family_id]

            # Once we've run through and cleaned up the device family list for this project, check if anything remains
            if len(this_project.device_families) <= 0:
                # If there are no remaining device families, then there isn't any (flashable) firmware for this project.
                # Delete the project.
                del self.Projects[this_project_id]

    # We need to load everything in a specific order for it to work
    def load_from_website(self) -> bool:
        if self.load_projects_from_website():
            if self.load_families_from_website():
                if self.load_firmware_from_website():
                    self.cleanse_projects()
                    return True
        return False


if __name__ == "__main__":
    import pprint

    firmware_list = FirmwareList()
    firmware_list.load_from_website()

    pprint.pprint(firmware_list)