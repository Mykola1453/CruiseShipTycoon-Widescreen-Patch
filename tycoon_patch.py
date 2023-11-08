# tycoon_patch.py
#
# Author: Mykola1453
#
# Patches several tycoon games to support widescreen resolutions,
# replacing the default letterbox resolution.
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

def get_res(res=False):
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
        print("Using user-defined resolution")
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

# Arguments
arguments = sys.argv
game_path = False
res_arg = False
laa_true = False
laa_false = False
restore_arg = False
games_arg = False
help_arg = False
for arg in arguments:
    if arg.endswith('.exe'):
        game_path = arg
    elif re.match(r'\d+x\d+', arg):
        res_arg = arg
    elif arg == "--lla=true":
        laa_true = True
    elif arg == "--lla=false":
        laa_false = True
    elif arg == "--restore" or arg == "-r":
        restore_arg = True
    elif arg == "--games" or arg == "-g":
        games_arg = True
    elif arg == "--help" or arg == "-h":
        help_arg = True

if not game_path:
    # When adding new game, don't forget to update array here
    known_exes = [
        "SkiGame.exe",
        "CruiseShipTycoon.exe",
        "SC.exe",
        "SchoolTycoon.exe",
        "SRE.exe",
        "Wildfire.exe",
        "Mall3Game.exe"
    ]

    # Check if each file exists
    for known_exe in known_exes:
        if os.path.isfile(known_exe):
            game_path = known_exe
            break

if not os.path.isfile(game_path) or not game_path:
    print("Game is not found!")

if restore_arg:
    restore_backup()
elif games_arg:
    # When adding new game, don't forget to update list here
    games_msg = """
List of supported games:
    - Cruise Ship Tycoon (2003), replaces 1280x960 resolution
    - Outdoor Life: Sportsman's Challenge (2004), replaces 1280x960 resolution
    - School Tycoon (2004), replaces 1280x960 resolution
    - Ski Resort Extreme (2004), replaces 1280x960 resolution
    - Mall Tycoon 3 (2005), replaces 1280x960 resolution
        """
    print(games_msg)
elif help_arg:
    help_msg = """
This is a patch for several tycoon games from the early 2000s.
It replaces the default letterbox resolution (4:3) with a widescreen one (16:9, 16:10). 
If necessary, LAA fix (4GB patch) and HUD fixes are also applied to accommodate new resolutions.
Usually it's enough to run the patch from the game folder, it should detect your screen resolution automatically.
On Linux, you will need to have pyautogui pip package to detect your screen resolution.
If you need to define the game path, resolution, and so on, use the following arguments:

    "path\\to\\the\\game.exe" defines path to the game exe
    (width)x(height) sets custom resolution (for example, 1920x1080)
    --lla=true enables LAA fix (4GB patch) that improves stability, it's on if resolution >= 2560x1440
    --lla=false disables LAA fix even if resolution >= 2560x1440
    --restore (-r) restores the game exe from the backup and resets user settings, using the backup created during patching
    --games (-g) prints the list of supported games
    --help (-h) prints this help message
        """
    print(help_msg)
else:
    # When adding new game, don't forget to update this section
    # Checking CRC of exe file
    calculated_crc = calculate_crc(game_path)

    known_crcs = {
        1447773004: "ski",
        1142252342: "cruise", # old version
        3759243516: "cruise", # latest version
        554985168: "challenge", # with copy protection removed
        490347772: "school",
        3371513462: "extreme",
        667719983: "wildfire",
        495043694: "mall3"
    }

    copy_protected_crcs = {
        3047680879: "ski",
        695746026: "challenge",
        3801619499: "extreme",
        1646831127: "wildfire",
        1814945630: "mall3"
    }

    old_crcs = {
        3298446386: "ski",
        4056039368: "school",
        2176966923: "extreme"
    }

    if calculated_crc in known_crcs:
        # Identifying the game
        game_name = known_crcs[calculated_crc]
        # Create a backup of the original file
        print(f"Making a backup")
        shutil.copy(game_path, f"{game_path}.bak")

        print("Patching the game")
        with open(game_path, 'rb') as game:
            game_content = game.read()

        # Getting the resolution
        width, height = get_res(res_arg)

        # Applying LAA fix (4GB patch) if needed
        # So far it is the same line for all the games
        if not laa_false:
            if (width >= 2560 or height >= 1440) or laa_true:
                print("LAA fix for better stability")
                game_content = replace_bytes(game_content, "0F010B01",
                                             f"2F010B01")
        else:
            if (width >= 2560 or height >= 1440):
                print("LAA fix is disabled, things may be unstable")

        width_le = struct.pack('<I', width).hex()
        height_le = struct.pack('<I', height).hex()

        # Perform actions based on the identified game
        if game_name == "ski":
            # Have no idea how to that one yet
            pass
        elif game_name == "cruise":
            # Notice if game version is not the latest
            if calculated_crc == 1142252342:
                print(" FYI: this is not the latest version of the game")
                print(" Not that it matters, this patch will work as is.")
                print(" But if you wish, look for Update 3 of the game,")
                print(" and patch again after updating.")

            # Main Menu resolution
            menu_height = height
            menu_width = (4 * menu_height) / 3
            menu_width = round(menu_width)

            if (menu_width == 1067 and menu_height == 800) or \
                    (menu_width == 1200 and menu_height == 900):
                # These 4:3 resolutions make the game render in 640x480,
                # using 1024x768
                menu_width = 1024
                menu_height = 768
            elif (menu_width == 960 and menu_height == 720):
                # Same as above
                # using 1920x1440
                menu_width = 800
                menu_height = 600
            elif (menu_width == 2880 and menu_height == 2160):
                # Same as above
                # using 1920x1440
                menu_width = 1920
                menu_height = 1440

            menu_width_le = struct.pack('<I', menu_width).hex()
            menu_height_le = struct.pack('<I', menu_height).hex()

            print(f"Changing menu resolution to {menu_width}x{menu_height}")
            if calculated_crc == 1142252342:
                game_content = replace_bytes(game_content, "20030000C744243858020000",
                                             f"{menu_width_le}C7442438{menu_height_le}")
            elif calculated_crc == 3759243516:
                game_content = replace_bytes(game_content, "20030000C744243458020000",
                                             f"{menu_width_le}C7442434{menu_height_le}")

            # In-game resolution
            if calculated_crc == 1142252342:
                game_content = replace_bytes(game_content, "00050000E8DCF80100C74030C0030000",
                                            f"{width_le}E8DCF80100C74030{height_le}")
            elif calculated_crc == 3759243516:
                game_content = replace_bytes(game_content, "00050000E80AE50100C74030C0030000",
                                            f"{width_le}E80AE50100C74030{height_le}")

            # HUD fixes
            game_content = replace_bytes(game_content, "3d000500007505",
                                         f"3d{width_le}7505")

            fix_height = height - 600

            # Convert fix value to little-endian hexadecimal value
            fix_h_le = struct.pack('<I', fix_height).hex()

            game_content = replace_bytes(game_content, "BD68010000C7", f"BD{fix_h_le}C7")
            game_content = replace_bytes(game_content, "000500007509BD68010000", f"{width_le}7509BD{fix_h_le}")
        elif game_name == "challenge":
            game_content = replace_bytes(game_content, "c7402c00050000", f"c7402c{width_le}")
            game_content = replace_bytes(game_content, "c74030c0030000", f"c74030{height_le}")

            # HUD fixes
            game_content = replace_bytes(game_content, "740b3d00050000", f"740b3d{width_le}")
            game_content = replace_bytes(game_content, "741a3d00050000", f"741a3d{width_le}")

            # This moves the options window in-game to the upper left corner, so that it no longer mutes the game
            game_content = replace_bytes(game_content, "2BC2D1F889442410E8", "2BC231C089442410E8")
            game_content = replace_bytes(game_content, "8BC5992BC28BE8D1FD", "8BC5992BC28BE831ED")
        elif game_name == "school":
            # In-game resolution
            game_content = replace_bytes(game_content, "402C00050000",
                                         f"402C{width_le}")
            game_content = replace_bytes(game_content, "4030C0030000",
                                         f"4030{height_le}")

            # HUD fixes
            if width != 1280:
                # Fixing position of the buttons in the lower side of the screen
                # by replacing E0FCFFFF (-800) with negative value of the current width
                negative_width = -width
                negative_width_le = struct.pack('<i', negative_width).hex()
                game_content = replace_bytes(game_content, "8D81E0FCFFFF",
                                             f"8D81{negative_width_le}")

                # Prevents game crashes
                game_content = replace_bytes(game_content, "741A3D00050000",
                                             f"741A3D{width_le}")
                game_content = replace_bytes(game_content, "eb093d00050000",
                                             f"eb093d{width_le}")
                game_content = replace_bytes(game_content, "740B3D00050000",
                                             f"740B3D{width_le}")
                game_content = replace_bytes(game_content, "e8896502003d00050000",
                                             f"e8896502003d{width_le}")
                game_content = replace_bytes(game_content, "74243d00050000",
                                             f"74243d{width_le}")
                game_content = replace_bytes(game_content, "e8dece00003d00050000",
                                             f"e8dece00003d{width_le}")
                game_content = replace_bytes(game_content, "e893cb00003d00050000",
                                             f"e893cb00003d{width_le}")
                game_content = replace_bytes(game_content, "e851c900003d00050000",
                                             f"e851c900003d{width_le}")

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
            objective_y_instant = objective_y - 25

            if objective_x < 0:
                o_x_le = struct.pack('<i', int(objective_x)).hex()
            else:
                o_x_le = struct.pack('<I', int(objective_x)).hex()
            o_y_le = struct.pack('<I', int(objective_y)).hex()
            o_y_i_le = struct.pack('<I', int(objective_y_instant)).hex()

            if history_x < 0:
                h_x_le = struct.pack('<i', int(history_x)).hex()
            else:
                h_x_le = struct.pack('<I', int(history_x)).hex()
            h_y_le = struct.pack('<I', int(history_y)).hex()

            game_content = replace_bytes(game_content, "740B81C730020000",
                                         f"740B81C7{o_y_le}")
            game_content = replace_bytes(game_content, "81c717020000",
                                         f"81c7{o_y_i_le}")
            game_content = replace_bytes(game_content, "526A4F81C6DC000000",
                                         f"526A4F81C6{o_x_le}")

            game_content = replace_bytes(game_content, "68930200006831010000",
                                         f"68{h_y_le}68{h_x_le}")

            # Save game window
            if width == 1280 and height == 720:
                game_content = replace_bytes(game_content, "81FB00040000",
                                             f"81FB{width_le}")
                game_content = replace_bytes(game_content, "81FB00050000",
                                             f"81FB00000000")

                save_x = (width / 2)
                save_y = (height / 2)
            else:
                game_content = replace_bytes(game_content, "81FB00050000",
                                             f"81FB{width_le}")

                save_x = (width / 2) - 240
                save_y = (height / 2) - 180

            save_x_le = struct.pack('<I', int(save_x)).hex()
            save_y_le = struct.pack('<I', int(save_y)).hex()

            game_content = replace_bytes(game_content, "2D90010000",
                                         f"2D{save_x_le}")
            game_content = replace_bytes(game_content, "2D2C010000",
                                         f"2D{save_y_le}")

            # Removes displaced frame in a classroom view
            game_content = replace_bytes(game_content, "313238307839363000", f"000000000000000000")
        elif game_name == "extreme" or game_name == "wildfire":
            # In-game resolution
            game_content = replace_bytes(game_content, "c7402c00050000",
                                         f"c7402c{width_le}")
            game_content = replace_bytes(game_content, "c74030c0030000",
                                         f"c74030{height_le}")

            # HUD fixes
            game_content = replace_bytes(game_content, "740B3D00050000",
                                         f"740B3D{width_le}")
        elif game_name == "mall3":
            # Resolution
            game_content = replace_bytes(game_content, "c7402800050000", f"c74028{width_le}")
            game_content = replace_bytes(game_content, "c7402cc0030000", f"c7402c{height_le}")

            # HUD fixes
            game_content = replace_bytes(game_content, "740e3d00050000", f"740e3d{width_le}")
            game_content = replace_bytes(game_content, "0f84e70000003d00050000", f"0f84e70000003d{width_le}")

        # Save the modified content to a new file
        with open(game_path, 'wb') as game:
            game.write(game_content)

        print("File has been patched successfully")
        if game_name != "ski":
            print("Don't forget to set game resolution to 1280x960 in options!")
    elif calculated_crc in copy_protected_crcs:
        # Identifying the game
        game_name = copy_protected_crcs[calculated_crc]
        # Removing copy protection
        print('This version of the game requires CD to play the game.')
        print('Disk check will be removed')
        response = input("Write yes to proceed (yes/no): ").strip().lower()
        if response == "yes":
            print("Removing disk check")
            shutil.copy(game_path, f"{game_path}.orig")
            print(f"Original executable is saved to \"{game_path}.orig\"")
            with open(game_path, 'rb') as game:
                game_content = game.read()

            if game_name == "ski":
                game_content = replace_bytes(game_content, "74206A15", "EB206A15")
            elif game_name == "challenge":
                game_content = replace_bytes(game_content, "E8D8FDFFFF85C07547", "E8D8FDFFFF85C0EB47")
            elif game_name == "extreme":
                game_content = replace_bytes(game_content,
                                             "752D84C08BCF7427A014E06900908D64240084C074198A1980CB200C203AD8750E8A440E014184C0746E",
                                             "909084C08BCF9090A014E06900908D64240084C090908A1980CB200C203AD890908A440E014184C0EB6E")
            elif game_name == "wildfire":
                game_content = replace_bytes(game_content, "0F8518FFFFFFE8", "E919FFFFFFFFE8")
            elif game_name == "mall3":
                game_content = replace_bytes(game_content, "8B35B0F26B00EB09", "8B35B0F26B00EB2B")

            with open(game_path, 'wb') as game:
                game.write(game_content)
            print("Disk check was removed")
            print("Re-run this patch to change resolution of the game")
    elif calculated_crc in old_crcs:
        # For Ski Resort Tycoon: https://www.patches-scrolls.de/patch/3781/7/30965
        print('This is an old version of the game!')
        print('Update the game and run the patch again.')
    else:
        print(f"Wrong file! Didn't recognize CRC: {calculated_crc}. Maybe this is not the latest version or the patch was already applied.")