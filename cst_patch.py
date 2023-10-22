#!/usr/bin/env python3

import zlib
import shutil
import os

# Patches CruiseShipTycoon.exe to support widescreen resolutions
# replaces the default '1280x800' resolution

# Functions
def calculate_crc(file_path):
    crc = 0
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(1024)
            if not chunk:
                break
            crc = zlib.crc32(chunk, crc)

    crc = crc & 0xFFFFFFFF

    return crc

def replace_bytes(content, search, replace):
    search_bytes = bytes.fromhex(search)
    replace_bytes = bytes.fromhex(replace)
    return content.replace(search_bytes, replace_bytes)

def detect_screen_size():
    import struct

    if os.name == 'nt':
        import ctypes

        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
    else:
        try:
            import pyautogui

            # Get the screen resolution using pyautogui
            screen_width, screen_height = pyautogui.size()
        except:
            print("Install pyautogui to detect screen size (pip install pyautogui)")

    print(f"Detected screen size: {screen_width}x{screen_height}")
    # Convert the screen resolution to little-endian hexadecimal values
    screen_width_le = struct.pack('<I', screen_width).hex()
    screen_height_le = struct.pack('<I', screen_height).hex()

    return screen_width_le, screen_height_le

# Checking CRC of exe file
cst_path = 'CruiseShipTycoon.exe'
calculated_crc = calculate_crc(cst_path)

v1001_crc = 1142252342 # Value for v1.0.0.1
v1001patched_crc = 1175784216

if calculated_crc == v1001_crc:
    print(f"CRC for {cst_path} matches the expected CRC: {v1001_crc}")

    # Create a backup of the original file
    print(f"Making a backup")
    shutil.copy(cst_path, f"{cst_path}.bak")

    print(f"Patching v1.0.0.1 version of the exe file")
    # Open the file for reading in binary mode
    with open(cst_path, 'rb') as cst:
        # Read the contents of the file
        cst_content = cst.read()

    # Detecting screen size
    width_le, height_le = detect_screen_size()

    # Main Menu resolution
    cst_content = replace_bytes(cst_content, "20030000C744243858020000", f"{width_le}C7442438{height_le}")

    # Ingame resolution
    cst_content = replace_bytes(cst_content, "00050000E8DCF80100C74030C0030000", f"{width_le}E8DCF80100C74030{height_le}")

    # GUI fixes

    # Save the modified content to a new file
    with open(cst_path, 'wb') as cst:
        cst.write(cst_content)

    print(f"File '{cst_path}' has been patched successfully.")
else:
    print(f"Expected {v1001_crc} CRC for {cst_path}, but got {calculated_crc}")

    if os.path.isfile(f"{cst_path}.bak"):
        print(f"Restoring backup")
        shutil.copy(f"{cst_path}.bak", cst_path)
    else:
        print(f"No backup found")