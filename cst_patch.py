#!/usr/bin/env python3

import shutil
import struct
import zlib
import sys
import os
import re

# Patches CruiseShipTycoon.exe to support widescreen resolutions
# replaces the default '1280x960' resolution

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

def get_res_le(res=False, letterbox=False, menu=False):
    common_resolutions = {
        "1024x768": (768, 1024),
        "1280x720": (720, 1280),
        "1280x800": (800, 1280),
        "1280x960": (960, 1280),
        "1360x768": (768, 1360),
        "1366x768": (768, 1366),
        "1440x1080": (1080, 1440),
        "1600x900": (900, 1600),
        "1920x1080": (1080, 1920),
        "2560x1440": (1440, 2560),
        "3840x2160": (2160, 3840)
    }

    if res:
        print(f"Using custom resolution")
        # Using defined resolution
        nums = res.split('x')
        if len(nums) == 2:
            width = int(nums[0])
            height = int(nums[1])
    else:
        # Using resolution of current display
        if os.name == 'nt':
            import ctypes

            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
        else:
            try:
                import pyautogui

                # Get the screen resolution using pyautogui
                width, height = pyautogui.size()
            except:
                print("Install pyautogui to detect screen size: pip install pyautogui")

    if letterbox:
        width = (4 * height) / 3
        width = round(width)

        if (width == 960 and height == 720) or \
                (width == 1067 and height == 800) or \
                (width == 1200 and height == 900):
            # These 4:3 resolutions make the game render in 640x480,
            # using 1024x768
            width = 1024
            height = 768
    if not menu:
        print(f"Changing resolution to {width}x{height}")

        if wide_menu_arg:
            print(f"Changing menu resolution to {width}x{height}")
            print(f"WARNING: Menu will likely be cropped!")
    else:
        print(f"Changing menu resolution to {width}x{height}")

    # Check if the actual resolution matches any of the common resolutions
    matching_resolution = None
    for resolution, (expected_height, expected_width) in common_resolutions.items():
        if width == expected_width and height == expected_height:
            matching_resolution = resolution
            break

    if not matching_resolution:
        print(f"WARNING: {width}x{height} resolution is uncommon, things may break!")

    # Convert the screen resolution to little-endian hexadecimal values
    width_le = struct.pack('<I', width).hex()
    height_le = struct.pack('<I', height).hex()

    return width_le, height_le

def restore_backup():
    if os.path.isfile(f"{cst_path}.bak"):
        directory = os.path.dirname(cst_path)
        if directory:
            settings_path = f"{directory}/settings.dat"
        else:
            settings_path = "settings.dat"

        if os.path.isfile(settings_path):
            print("Resetting settings")
            os.remove(settings_path)

        print(f"Restoring backup")
        shutil.copy(f"{cst_path}.bak", cst_path)
    else:
        print(f"No backup found")

# Command line arguments
arguments = sys.argv
cst_path = False
res_arg = False
restore_arg = False
wide_menu_arg = False
letterbox_arg = False
help_arg = False
for arg in arguments:
    if arg.endswith('.exe'):
        cst_path = arg
    elif re.match(r'\d+x\d+', arg):
        res_arg = arg
    elif arg == "--restore" or arg == "-r":
        restore_arg = True
    elif arg == "--wide_menu" or arg == "-w":
        wide_menu_arg = True
    elif arg == "--letterbox" or arg == "-l":
        letterbox_arg = True
    elif arg == "--help" or arg == "-h":
        help_arg = True

if not help_arg:
    # Checking CRC of exe file
    if not cst_path:
        cst_path = 'CruiseShipTycoon.exe'

    if not os.path.isfile(cst_path):
        print(f"File is not found!")

    calculated_crc = calculate_crc(cst_path)

    v1001_crc = 1142252342 # Value for v1.0.0.1

    if calculated_crc == v1001_crc:
        print(f"CRC matches the expected CRC: {v1001_crc}")

        # Create a backup of the original file
        print(f"Making a backup")
        shutil.copy(cst_path, f"{cst_path}.bak")

        print(f"Patching v1.0.0.1 version of the game")
        # Open the file for reading in binary mode
        with open(cst_path, 'rb') as cst:
            # Read the contents of the file
            cst_content = cst.read()

        # Converting the resolution to hexadecimal (little endian)
        width_le, height_le = get_res_le(res_arg, letterbox_arg)
        if wide_menu_arg:
            menu_width_le, menu_height_le = width_le, height_le
        else:
            menu_width_le, menu_height_le = get_res_le(res_arg, True, True)

        # Main Menu resolution
        cst_content = replace_bytes(cst_content, "20030000C744243858020000", f"{menu_width_le}C7442438{menu_height_le}")

        # Ingame resolution
        cst_content = replace_bytes(cst_content, "00050000E8DCF80100C74030C0030000", f"{width_le}E8DCF80100C74030{height_le}")

        # GUI fix
        # Hex value below, 68 01, corresponds to 360 and is tied to height of 960
        # We need to correct it for the GUI to be placed right
        print(f"Attempting to fix GUI")
        if int.from_bytes(bytes.fromhex(height_le), byteorder='little') == 2160:
            # Needs testing
            fix_value = 1560
        elif int.from_bytes(bytes.fromhex(height_le), byteorder='little') == 1440:
            # Needs testing
            fix_value = 840
        elif int.from_bytes(bytes.fromhex(height_le), byteorder='little') == 1080:
            fix_value = 480
        elif int.from_bytes(bytes.fromhex(height_le), byteorder='little') == 900:
            fix_value = 300
        elif int.from_bytes(bytes.fromhex(height_le), byteorder='little') == 800:
            fix_value = 201
        elif int.from_bytes(bytes.fromhex(height_le), byteorder='little') == 768:
            fix_value = 169
        elif int.from_bytes(bytes.fromhex(height_le), byteorder='little') == 720:
            fix_value = 120
        else:
            # Default value for the height of 960
            fix_value = 360

        # Convert fix value to little-endian hexadecimal value
        fix_le = struct.pack('<I', fix_value).hex()

        cst_content = replace_bytes(cst_content, "BD68010000C7", f"BD{fix_le}C7")
        cst_content = replace_bytes(cst_content, "000500007509BD68010000", f"{width_le}7509BD{fix_le}")

        if fix_value == 360:
            print(f"WARNING: No GUI fix for chosen resolution, things may break!")
        else:
            print(f"GUI is fixed")

        # Save the modified content to a new file
        with open(cst_path, 'wb') as cst:
            cst.write(cst_content)

        print("File has been patched successfully")
        print("Don't forget to set game resolution to 1280x960 in options!")
    else:
        print(f"Wrong file! Expected {v1001_crc} CRC, but got {calculated_crc}")

    if restore_arg:
        restore_backup()
else:
    help_msg = """
    This is patch that replaces default 1280x960 (4:3) resolution with a widescreen one, and fixes GUI to accomodate the new resultion, if possible.
    Run it in the root of the game to set the resolution to your screen's resolution.
    Menu resolution and ingame resolution can have different value, so resolution of the menu is in 4:3 aspect ratio to avoid parts of menu being cropped.
    (On Linux, you'll need to have pyautogui pip package to use your screen resolution or define it manually, as explained below.\n
    Patch accepts the following arguments:
    "path/to/game.exe" defines path to the game's exe (not needed if the patch is already in the game folder)
    (width)x(height) sets custom resolution, but note that GUI won't be fixed if chosen resolution is uncommon
    --wide_menu (-w) sets menu resolution to be widescreen too, but the menu will get partially cropped
    --letterbox (-l) sets that 4:3 resolution which is the closest to defined widescreen resolution
    --restore (-r) restores game exe's backup and deletes user settings, if backup file is available
    --help (-h) prints this message\n
    P.S. Don't forget to change your game settings because game sets the lowest graphical settings by default.
    """
    print(help_msg)