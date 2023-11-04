# mall3_patch.py
#
# Author: Mykola1453
#
# Patches Mall3Game.exe to support widescreen resolutions,
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
        "2560x1440": (2560, 1440),
        "3840x2160": (3840, 2160)
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
    if os.path.isfile(f"{game_path}.bak"):
        directory = os.path.dirname(game_path)
        if directory:
            settings_path = f"{directory}/settings.dat"
        else:
            settings_path = "settings.dat"

        if os.path.isfile(settings_path):
            print("Resetting settings")
            os.remove(settings_path)

        print(f"Restoring backup")
        shutil.copy(f"{game_path}.bak", game_path)
    else:
        print(f"No backup is found")


# Command line arguments
arguments = sys.argv
game_path = False
res_arg = False
restore_arg = False
laa_true = False
laa_false = False
help_arg = False
for arg in arguments:
    if arg.endswith('.exe'):
        game_path = arg
    elif re.match(r'\d+x\d+', arg):
        res_arg = arg
    elif arg == "--restore" or arg == "-r":
        restore_arg = True
    elif arg == "--lla=true":
        laa_true = True
    elif arg == "--lla=false":
        laa_false = True
    elif arg == "--help" or arg == "-h":
        help_arg = True

if not game_path:
    game_path = 'Mall3Game.exe'

if not os.path.isfile(game_path):
    print("File is not found!")

if not help_arg and not restore_arg:
    # Checking CRC of exe file
    calculated_crc = calculate_crc(game_path)

    tested_versions = [
        495043694 # the latest version, without DRM
    ]

    if calculated_crc in tested_versions:
        # Create a backup of the original file
        print(f"Making a backup")
        shutil.copy(game_path, f"{game_path}.bak")

        print("Patching the game")
        with open(game_path, 'rb') as game:
            game_content = game.read()

        # Getting the resolution and converting the resolution to hexadecimal (little endian)
        width, height = get_res_le(res_arg)

        width_le = struct.pack('<I', width).hex()
        height_le = struct.pack('<I', height).hex()

        # Resolution
        game_content = replace_bytes(game_content, "c7402800050000", f"c74028{width_le}")
        game_content = replace_bytes(game_content, "c7402cc0030000", f"c7402c{height_le}")

        if not laa_false:
            if (width >= 2560 or height >= 1440) or laa_true:
                # LAA fix (4GB patch), improves stability
                print("LAA fix for better stability")
                game_content = replace_bytes(game_content, "0F010B01",
                                             f"2F010B01")
        else:
            if (width >= 2560 or height >= 1440):
                print("LAA fix is disabled, stability is not guaranteed")

        # HUD fixes
        game_content = replace_bytes(game_content, "740e3d00050000", f"740e3d{width_le}")
        game_content = replace_bytes(game_content, "0f84e70000003d00050000", f"0f84e70000003d{width_le}")

        # Save the modified content to a new file
        with open(game_path, 'wb') as game:
            game.write(game_content)

        print("File has been patched successfully")
        print("Don't forget to set game resolution to 1280x960 in options!")
    elif calculated_crc == 1814945630:
        print('This is the latest version of the game.')
        print('It requires CD to play the game')
        print('Disk check will be removed')
        response = input("Write yes to proceed (yes/no): ").strip().lower()
        if response == "yes":
            print("Removing disk check")
            shutil.copy(game_path, f"{game_path}.orig")
            print(f"Original executable is saved to \"{game_path}.orig\"")
            with open(game_path, 'rb') as game:
                game_content = game.read()
            game_content = replace_bytes(game_content, "8B35B0F26B00EB09", "8B35B0F26B00EB2B")
            with open(game_path, 'wb') as game:
                game.write(game_content)
            print("Disk check was removed")
            print("Re-run this patch to change resolution of the game")
    else:
        print(f"Wrong file! Didn't recognize CRC: {calculated_crc}. Maybe this is not the latest version or the patch was already applied.")
        # restore_backup()
elif restore_arg:
    restore_backup()
else:
    help_msg = """
    This is a patch that replaces the default 1280x960 (4:3) resolution with a widescreen one, and fixes the game's HUD to accommodate the new resolution.
    Run it in the root of the game to set the resolution to your screen's resolution.
    Menu resolution is the same as in-game resolution.
    (On Linux, you'll need to have pyautogui pip package to detect your screen resolution, otherwise you can define it manually, as explained below)\n
    Patch accepts the following arguments:
    "path/to/the/game.exe" defines path to the game's exe (not needed if the patch is already in the game folder)
    (width)x(height) sets custom resolution
    --lla=true enables LLA fix (4GB patch) that improves stability by allocating 4GB of RAM instead of 2GB; enabled by default if resolution >= 2560x1440
    --lla=false disables LLA fix even if resolution is bigger than 1920x1080
    --restore (-r) if backup file is present, restores the game exe's backup and deletes user settings
    --help (-h) prints help message
    """
    print(help_msg)
