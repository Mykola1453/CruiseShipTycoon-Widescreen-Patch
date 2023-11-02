# extreme_patch.py
#
# Author: Mykola1453
#
# Patches SRE.exe to support widescreen resolutions,
# replacing the default '1280x960' resolution.
#
# MIT License
#
# Copyright (c) 2023 Mykola1453
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import shutil
import struct
import zlib
import sys
import os
import re

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

def replace_bytes_range(content, start_offset_hex, end_offset_hex, replacement_bytes_hex):
    # Convert hexadecimal offsets to integers
    start_offset = int(start_offset_hex, 16)
    end_offset = int(end_offset_hex, 16)

    # Convert the hexadecimal replacement bytes to bytes
    replacement_bytes = bytes.fromhex(replacement_bytes_hex)

    if start_offset < 0 or end_offset > len(content) or start_offset >= end_offset:
        raise ValueError("Invalid start or end offset.")

    # Calculate the length of the original range
    range_length = end_offset - start_offset

    # Calculate how many times the replacement bytes should be repeated
    repeat_count = range_length // len(replacement_bytes)

    # Calculate the remaining bytes if the replacement is shorter than the range
    remaining_bytes = range_length % len(replacement_bytes)

    # Replace the specified range with the repeated replacement bytes
    replaced_content = content[:start_offset] + replacement_bytes * repeat_count
    replaced_content += replacement_bytes[:remaining_bytes]
    replaced_content += content[end_offset:]

    return replaced_content

def get_res_le(res=False):
    tested_resolutions = {
        "1280x720": (1280, 720),
        "1280x800": (1280, 800),
        "1360x768": (1360, 768),
        "1366x768": (1366, 768),
        "1600x900": (1600, 900),
        "1920x1080": (1920, 1080),
        # "2560x1440": (2560, 1440),
        # "3840x2160": (3840, 2160)
    }

    if res:
        print("Using custom resolution")
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

    print(f"Changing resolution to {width}x{height}")

    # Check if the actual resolution matches any of the tested resolutions
    matching_resolution = False
    for resolution, (expected_width, expected_height) in tested_resolutions.items():
        if (width == expected_width and height == expected_height):
            matching_resolution = True
            break

    if not matching_resolution:
        print(f" NOTE: {width}x{height} resolution was not tested, it might or might not work.")

    return width, height


def restore_backup():
    if os.path.isfile(f"{extreme_path}.bak"):
        directory = os.path.dirname(extreme_path)
        if directory:
            settings_path = f"{directory}/settings.dat"
        else:
            settings_path = "settings.dat"

        if os.path.isfile(settings_path):
            print("Resetting settings")
            os.remove(settings_path)

        print(f"Restoring backup")
        shutil.copy(f"{extreme_path}.bak", extreme_path)
    else:
        print(f"No backup is found")


# Command line arguments
arguments = sys.argv
extreme_path = False
res_arg = False
restore_arg = False
help_arg = False
for arg in arguments:
    if arg.endswith('.exe'):
        extreme_path = arg
    elif re.match(r'\d+x\d+', arg):
        res_arg = arg
    elif arg == "--restore" or arg == "-r":
        restore_arg = True
    elif arg == "--help" or arg == "-h":
        help_arg = True

if not extreme_path:
    extreme_path = 'SRE.exe'

if not os.path.isfile(extreme_path):
    print("File is not found!")

if not help_arg and not restore_arg:
    # Checking CRC of exe file
    calculated_crc = calculate_crc(extreme_path)

    tested_versions = [
        3371513462   # the latest version, without DRM / noCD
    ]

    if calculated_crc in tested_versions:
        # Create a backup of the original file
        print(f"Making a backup")
        shutil.copy(extreme_path, f"{extreme_path}.bak")

        print("Patching the game")
        with open(extreme_path, 'rb') as extreme:
            extreme_content = extreme.read()

        # Getting the resolution and converting the resolution to hexadecimal (little endian)
        width, height = get_res_le(res_arg)

        width_le = struct.pack('<I', width).hex()
        height_le = struct.pack('<I', height).hex()

        # Main Menu resolution
        # It's rendered in 800x600 by default and doesn't scale well to other resolutions

        # In-game resolution
        extreme_content = replace_bytes(extreme_content, "c7402c00050000",
                                   f"c7402c{width_le}")
        extreme_content = replace_bytes(extreme_content, "c74030c0030000",
                                   f"c74030{height_le}")

        # HUD fixes
        # No need

        # Save the modified content to a new file
        with open(extreme_path, 'wb') as extreme:
            extreme.write(extreme_content)

        print("File has been patched successfully")
        print("Don't forget to set game resolution to 1280x960 in options!")
    elif calculated_crc == 2176966923:
        print('This is an old version that requires CD to play the game!')
        print('The latest update is Update 4.')
        print('You can update your game by pressing "Check for updates" button from the game\'s launcher (SREUpdater.exe).')
        print('Then run the patch again to change resolution of the game.')
    elif calculated_crc == 3801619499:
        print('This is the latest version of the game.')
        print('It requires CD to play the game')
        print('CD protection can be removed')
        response = input("Write yes to remove it (yes/no): ").strip().lower()
        if response == "yes":
            print("Removing CD protection")
            shutil.copy(extreme_path, f"{extreme_path}.orig")
            print(f"Original executable is saved to \"{extreme_path}.orig\"")
            with open(extreme_path, 'rb') as extreme:
                extreme_content = extreme.read()
            extreme_content = replace_bytes(extreme_content, "752D84C08BCF7427A014E06900908D64240084C074198A1980CB200C203AD8750E8A440E014184C0746E", "909084C08BCF9090A014E06900908D64240084C090908A1980CB200C203AD890908A440E014184C0EB6E")
            with open(extreme_path, 'wb') as extreme:
                extreme.write(extreme_content)
            print("CD protection was removed")
            print("Re-run this patch to change resolution of the game")
    else:
        print(f"Wrong file! Didn't recognize CRC: {calculated_crc}")
        # restore_backup()
elif restore_arg:
    restore_backup()
else:
    help_msg = """
    This is a patch that replaces the default 1280x960 (4:3) resolution with a widescreen one, and fixes the game's HUD to accommodate the new resolution.
    Run it in the root of the game to set the resolution to your screen's resolution.
    Menu resolution stays at 800x600 (4:3), because other resolutions don't work well with the menu. This doesn't influence in-game resolution.
    (On Linux, you'll need to have pyautogui pip package to detect your screen resolution, otherwise you can define it manually, as explained below)\n
    Patch accepts the following arguments:
    "path/to/the/game.exe" defines path to the game's exe (not needed if the patch is already in the game folder)
    (width)x(height) sets custom resolution
    --restore (-r) if backup file is present, restores the game exe's backup and deletes user settings
    --help (-h) prints help message
    """
    print(help_msg)
