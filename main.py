import os, subprocess, time

'''
Drive class, representing an individual drive.
'''
class Drive:
    def __init__(self, device_path, name, file_system):
        self.device_path = device_path
        self.name = name
        self.file_system = file_system
        self.mount_point = None

'''
DriveDetector class, responsible for detecting newly connected drives and notifying the DriveMounter.
'''
class DriveDetector:
    def __init__(self, drive_mounter):
        self.drive_mounter = drive_mounter
    def start(self):
        self.detect_drives()
        while True:
            time.sleep(1)
            self.detect_drives()
            self.check_disconnected_drives()
    def detect_drives(self):
        devices = os.listdir("/dev")
        for device in devices:
            if device.startswith(("sd", "nvme")):
                device_path = f"/dev/{device}"
                if not self.drive_exists(device_path):
                    drive = self.create_drive(device_path)
                    self.drive_mounter.mount_drive(drive)
    def drive_exists(self, device_path):
        if not os.path.exists(device_path):
            return False
        for drive in self.drive_mounter.drives:
            if os.path.samefile(drive.device_path, device_path):
                return True
        return False
    def create_drive(self, device_path):
        name = self.get_unique_drive_name(device_path)
        file_system = self.get_drive_file_system(device_path)
        drive = Drive(device_path, name, file_system)
        self.drive_mounter.drives.append(drive)
        return drive
    def get_unique_drive_name(self, device_path):
        name = device_path.split("/")[-1]
        if self.drive_name_exists(name):
            i = 1
            while self.drive_name_exists(f"{name}_{i}"):
                i += 1
            name = f"{name}_{i}"
        return name
    def drive_name_exists(self, name):
        for drive in self.drive_mounter.drives:
            if drive.name == name:
                return True
        return False
    def get_drive_file_system(self, device_path):
        file_system = os.popen(f"blkid -o value -s TYPE {device_path}").read().strip()
        return file_system
    def check_disconnected_drives(self):
        for drive in self.drive_mounter.drives:
            if not os.path.exists(drive.mount_point):
                self.drive_mounter.unmount_drive(drive)

'''
DriveMounter class, responsible for managing the mounting and unmounting of drives.
'''
class DriveMounter:
    def __init__(self):
        self.drives = []
        self.drive_detector = DriveDetector(self)
    def start_detection(self):
        self.drive_detector.start()
    def mount_drive(self, drive):
        mount_point = self.get_unique_mount_point(drive)
        os.makedirs(mount_point, exist_ok=True)
        subprocess.run(["mount", drive.device_path, mount_point])
        drive.mount_point = mount_point
    def unmount_drive(self, drive):
        subprocess.run(["umount", drive.mount_point])
        os.rmdir(drive.mount_point)
        drive.mount_point = None
    def get_unique_mount_point(self, drive):
        mount_point = f"/var/run/mnt/{drive.name}"
        if os.path.exists(mount_point):
            i = 1
            while os.path.exists(f"{mount_point}_{i}"):
                i += 1
            mount_point = f"{mount_point}_{i}"
        return mount_point

'''
This initializes the DriveMounter and starts the drive detection process.
'''
if __name__ == "__main__":
    drive_mounter = DriveMounter()
    drive_mounter.start_detection()