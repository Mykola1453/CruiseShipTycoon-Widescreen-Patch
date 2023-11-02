# school_patch.py
#
# Author: Mykola1453
#
# Patches SchoolTycoon.exe to support widescreen resolutions,
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
    if os.path.isfile(f"{school_path}.bak"):
        directory = os.path.dirname(school_path)
        if directory:
            settings_path = f"{directory}/settings.dat"
        else:
            settings_path = "settings.dat"

        if os.path.isfile(settings_path):
            print("Resetting settings")
            os.remove(settings_path)

        print(f"Restoring backup")
        shutil.copy(f"{school_path}.bak", school_path)
    else:
        print(f"No backup is found")


# Command line arguments
arguments = sys.argv
school_path = False
res_arg = False
restore_arg = False
help_arg = False
for arg in arguments:
    if arg.endswith('.exe'):
        school_path = arg
    elif re.match(r'\d+x\d+', arg):
        res_arg = arg
    elif arg == "--restore" or arg == "-r":
        restore_arg = True
    elif arg == "--help" or arg == "-h":
        help_arg = True

if not school_path:
    school_path = 'SchoolTycoon.exe'

if not os.path.isfile(school_path):
    print("File is not found!")

if not help_arg and not restore_arg:
    # Checking CRC of exe file
    calculated_crc = calculate_crc(school_path)

    tested_versions = [
        1373379655,  # old version, without DRM
        490347772  # latest version, no DRM
    ]

    if calculated_crc in tested_versions:
        # Create a backup of the original file
        print(f"Making a backup")
        shutil.copy(school_path, f"{school_path}.bak")

        print("Patching the game")
        with open(school_path, 'rb') as school:
            school_content = school.read()

        # Getting the resolution and converting the resolution to hexadecimal (little endian)
        width, height = get_res_le(res_arg)

        width_le = struct.pack('<I', width).hex()
        height_le = struct.pack('<I', height).hex()

        # Main Menu resolution
        # It's rendered in 800x600 by default and doesn't scale well to other resolutions
        # school_content = replace_bytes(school_content, "C744243420030000",
        #                            f"C7442434{width_le}")
        # school_content = replace_bytes(school_content, "C744243858020000",
        #                            f"C7442438{height_le}")

        # In-game resolution
        school_content = replace_bytes(school_content, "402C00050000",
                                   f"402C{width_le}")
        school_content = replace_bytes(school_content, "4030C0030000",
                                   f"4030{height_le}")

        # HUD fixes
        print("Fixing HUD")
        if width != 1280:
            # Fixing position of the buttons in the lower side of the screen
            # by replacing E0FCFFFF (-800) with negative value of the current width
            negative_width = -width
            negative_width_le = struct.pack('<i', negative_width).hex()
            school_content = replace_bytes(school_content, "8D81E0FCFFFF",
                                       f"8D81{negative_width_le}")

            # Prevents game crashes
            school_content = replace_bytes(school_content, "3D00050000",
                                       f"3D{width_le}")

        # Fixing position of objectives button and history button
        # The position is relative to the respective window that's opened after button is pressed,
        # so we calculate needed value based on that
        if width == 1280:
            # Buttons are centered, so their position is a bit different
            objective_x = 712 - ((width / 2) - 148)
            history_x = 770 - ((width / 2) - 175)
        else:
            objective_x = 472 - ((width / 2) - 148)
            history_x = 530 - ((width / 2) - 175)

        history_y = (height - 33) - ((height / 2) - 212)
        objective_y = (height - 33) - ((height / 2) - 113)

        if objective_x < 0:
            o_x_le = struct.pack('<i', int(objective_x)).hex()
        else:
            o_x_le = struct.pack('<I', int(objective_x)).hex()
        o_y_le = struct.pack('<I', int(objective_y)).hex()

        if history_x < 0:
            h_x_le = struct.pack('<i', int(history_x)).hex()
        else:
            h_x_le = struct.pack('<I', int(history_x)).hex()
        h_y_le = struct.pack('<I', int(history_y)).hex()

        school_content = replace_bytes(school_content, "740B81C730020000",
                                   f"740B81C7{o_y_le}")
        school_content = replace_bytes(school_content, "526A4F81C6DC000000",
                                   f"526A4F81C6{o_x_le}")

        school_content = replace_bytes(school_content, "68930200006831010000",
                                   f"68{h_y_le}68{h_x_le}")

        # Save game window
        if width == 1280 and height == 720:
            school_content = replace_bytes(school_content, "81FB00040000",
                                       f"81FB{width_le}")
            school_content = replace_bytes(school_content, "81FB00050000",
                                       f"81FB00000000")

            save_x = (width / 2)
            save_y = (height / 2)
        else:
            school_content = replace_bytes(school_content, "81FB00050000",
                                       f"81FB{width_le}")

            save_x = (width / 2) - 240
            save_y = (height / 2) - 180

        save_x_le = struct.pack('<I', int(save_x)).hex()
        save_y_le = struct.pack('<I', int(save_y)).hex()

        school_content = replace_bytes(school_content, "2D90010000",
                                   f"2D{save_x_le}")
        school_content = replace_bytes(school_content, "2D2C010000",
                                   f"2D{save_y_le}")

        # Removes displaced frame in a classroom view
        school_content = replace_bytes(school_content, "313238307839363000", f"000000000000000000")

        # Save the modified content to a new file
        with open(school_path, 'wb') as school:
            school.write(school_content)

        print("File has been patched successfully")
        print("Don't forget to set game resolution to 1280x960 in options!")
    elif calculated_crc == 4056039368:
        print('This is an old version that requires CD to play the game')
        print(
            'You should update your game by pressing "Check for updates" button from the game\'s launcher (School.exe)')
        print('If you still want to use this version, CD protection can be removed')
        response = input("Write yes, if so (yes/no): ").strip().lower()
        if response == "yes":
            print("Removing CD protection")
            shutil.copy(school_path, f"{school_path}.orig")
            print(f"Backing up original executable: {school_path}.orig")
            with open(school_path, 'rb') as school:
                school_content = school.read()
            school_content = replace_bytes(school_content, "E845BA000084C07549", "E845BA000084C0EB49")
            school_content = replace_bytes_range(school_content, "89097", "8909C", "90")
            school_content = replace_bytes_range(school_content, "890A9", "890AE", "90")
            school_content = replace_bytes_range(school_content, "890B1", "890B6", "90")
            with open(school_path, 'wb') as school:
                school.write(school_content)
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
