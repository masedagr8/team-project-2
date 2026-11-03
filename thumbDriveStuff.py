"""python3 -m pip install pyudev"""

import os
import re
import time
import shutil
import subprocess
from pathlib import Path

import pyudev


def is_usb_partition(device):
    """Check whether a block partition belongs to a USB device."""

    if device.get("DEVTYPE") != "partition":
        return False

    current = device

    while current is not None:
        if current.get("ID_BUS") == "usb":
            return True

        current = current.parent

    return False


def wait_for_usb():
    """Wait for one USB storage device to become available."""

    context = pyudev.Context()

    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="block", device_type="partition")
    monitor.start()

    print("\nwaiting for USB thumb drive...")

    # Check whether a USB drive is already connected.
    for device in context.list_devices(
        subsystem="block",
        DEVTYPE="partition"
    ):
        if is_usb_partition(device) and device.device_node:
            print("USB drive detected:", device.device_node)
            return device.device_node

    # Otherwise, wait for a new USB partition.
    while True:
        device = monitor.poll(timeout=1)

        if device is None:
            continue

        if (
            device.action == "add"
            and is_usb_partition(device)
            and device.device_node
        ):
            print("USB drive detected:", device.device_node)
            return device.device_node


def find_mount_point(device_node):
    """Find the mount location for a USB partition."""

    device_real_path = os.path.realpath(device_node)

    with open("/proc/mounts", "r", encoding="utf-8") as mounts:

        for line in mounts:
            fields = line.split()

            if len(fields) < 2:
                continue

            source = fields[0]

            if os.path.realpath(source) == device_real_path:

                mount_point = re.sub(
                    r"\\([0-7]{3})",
                    lambda match: chr(int(match.group(1), 8)),
                    fields[1]
                )

                return mount_point

    return None


def get_usb_mount_point(device_node):
    """Find or mount the USB drive."""

    # Give automatic mounting time to finish.
    for _ in range(10):
        mount_point = find_mount_point(device_node)

        if mount_point:
            print("USB mounted at:", mount_point)
            return mount_point

        time.sleep(1)

    # Try mounting manually through udisks2.
    udisksctl = shutil.which("udisksctl")

    if not udisksctl:
        raise RuntimeError(
            "USB drive is not mounted and udisksctl was not found. "
            "Install udisks2."
        )

    result = subprocess.run(
        [udisksctl, "mount", "-b", device_node],
        capture_output=True,
        text=True,
        timeout=30
    )

    # Check again in case the drive was mounted automatically.
    for _ in range(10):
        mount_point = find_mount_point(device_node)

        if mount_point:
            print("USB mounted at:", mount_point)
            return mount_point

        time.sleep(1)

    raise RuntimeError(
        f"Could not mount USB drive {device_node}.\n"
        f"{result.stderr or result.stdout}"
    )


def copy_png_images(usb_path, destination_path):
    """Copy all PNG images from USB into the Images directory."""

    usb_folder = Path(usb_path)
    destination_folder = Path(destination_path)

    destination_folder.mkdir(parents=True, exist_ok=True)

    # Search the entire USB drive for PNG images.
    png_files = sorted(
        path for path in usb_folder.rglob("*")
        if path.is_file() and path.suffix.lower() == ".png"
    )

    if not png_files:
        raise RuntimeError("No PNG images were found on the USB drive.")

    copied_count = 0

    for source in png_files:

        # Keep the Images folder flat for the existing sorter.
        destination = destination_folder / source.name

        # Avoid overwriting files with duplicate names.
        counter = 1

        while destination.exists():
            destination = destination_folder / (
                f"{source.stem}_{counter}{source.suffix}"
            )
            counter += 1

        shutil.copy2(source, destination)

        copied_count += 1

        print(f"Copied: {source.name}")

    #print(f"\nsuccessfully copied {copied_count} PNG image(s).")
    #print("Images saved to:", destination_folder)

    return copied_count


def import_images_from_usb(destination_path):
    """Wait for one USB drive and import its PNG images."""

    device_node = wait_for_usb()

    mount_point = get_usb_mount_point(device_node)

    return copy_png_images(mount_point, destination_path)


#After your existing argument parser processes --input, add:
#Import images from one USB drive before running the sorter.
input_dir = os.path.abspath(args.input)

import_images_from_usb(input_dir)
