import json
import argparse
import os
import re
# import configparser
from bulk_reader_tools import *

testing = True
master_config_name = "Config.ini"

# Used for testing only
test_file_name = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\unpacked saves" \
             r"\Enslavers.bin"

# Configuration file currently not used
# config = configparser.ConfigParser(allow_no_value=True)
# Default behaviour is to make all config option names lowercase
# We don't want to do that so we override optionxform
# config.optionxform = lambda option: option
# config.read(master_config_name)

passes = [{}, {}, {}, {}, {}]  # The main data structure
locations = [{}, {}, {}, {}, {}]  # Location within the bulk file of each interesting section

# ====================================================================== #
# ==== Get the name of the binary data file and open it for reading ==== #
# ====================================================================== #

if testing:
    input_path = test_file_name
else:
    parser = argparse.ArgumentParser(description="Deserializes the bulk files into native Python objects.")
    parser.add_argument("filename")
    args = parser.parse_args()
    input_path = os.path.abspath(args.filename)

json_output_path = os.path.splitext(input_path)[0] + ".json"

print(f"Deserializing {os.path.basename(input_path)}")

# If you try to open(file_in_name, 'rb') without setting access=b.mmap.ACCESS_READ, you get an error.
with open(input_path, 'rb') as input_path:
    binary = b.BinReader(input_path.fileno(), 0, access=b.mmap.ACCESS_READ)

# ================================ #
# ==== First pass starts here ==== #
# ================================ #

# world parameters, climates
for key in first_pass_structure_1:
    locations[0][key] = binary.tell()
    passes[0][key] = binary.fpop_structure(first_pass_structure_1[key])

# Events - not implemented yet
locations[0]["events"] = binary.tell()
passes[0]["events"] = binary.fpop(b.UINT)
if passes[0]["events"] != 0:
    raise NotImplementedError("Events section parsing is not implemented.")

# Actions
locations[0]["actions"] = binary.tell()
action_count = binary.fpop(b.UINT)
passes[0]["actions"] = []
for n in range(action_count):
    action = binary.fpop_structure(action_structure)
    if action["path"].endswith("CycleWeapon"):
        action["bool1"] = binary.fpop(b.BOOL)
    passes[0]["actions"].append(action)

# Traits, players, tiles, features, cities, buildingGroups, buildings, units, weapons, items, quests.
for key in first_pass_structure_2:
    locations[0][key] = binary.tell()
    passes[0][key] = binary.fpop_structure(first_pass_structure_2[key])

# Finally, notifications.

locations[0]["notifications"] = binary.tell()
notification_count = binary.fpop(b.UINT)
passes[0]["notifications"] = []
for n in range(notification_count):
    notif = binary.fpop_structure(notification_prefix)
    extra = binary.fpop_structure(notification_suffixes[notif["type"]])
    notif.update(extra)
    passes[0]["notifications"].append(notif)

# ======================================================= #
# ==== Allocating length fields to subsequent passes ==== #
# ======================================================= #

for structure in [second_pass_structure, third_pass_structure, fourth_pass_structure, fifth_pass_structure]:
    for key in structure:
        length = len(passes[0][key])
        try:
            structure[key][1] = length
        except TypeError:
            pass

# ================================= #
# ==== Second pass starts here ==== #
# ================================= #

# ID of the current active player
passes[1]["world_params"] = {"current_player": binary.fpop(b.UINT)}

# Actions require special handling because of the weapon-actions issue
locations[1]["actions"] = binary.tell()
passes[1]["actions"] = []
for action in passes[0]["actions"]:
    if is_weapon(action["path"]):
        my_data = binary.fpop_structure(action2_weapon_structure)
        passes[1]["actions"].append(my_data)
    else:
        my_data = binary.fpop_structure(action2_normal_structure)
        passes[1]["actions"].append(my_data)

# traits, players, tiles, features, cities, buildingGroups, buildings, units, weapons, items
for key in second_pass_structure:
    locations[1][key] = binary.tell()
    passes[1][key] = binary.fpop_structure(second_pass_structure[key])

# Quests - not deserialized, just scanned
locations[1]["quests"] = binary.tell()
if len(passes[0]["quests"]) != 0:
    first_notif_type = passes[0]["notifications"][0]["type"]
    first_notif_prefix = bytes(str(notification2_prefix_lengths[first_notif_type]), "UTF-8")
    first_notif_re = b'[\x00-\x01]{' + first_notif_prefix + rb'}\w{5}'
    quest2_binary = b.DataFormat(re.compile(first_notif_re), bytes, inclusive=False)
    passes[1]["quests"] = binary.fpop_structure(quest2_binary)
else:
    passes[1]["quests"] = b''

# Notifications
locations[1]["notifications"] = binary.tell()
passes[1]["notifications"] = [binary.fpop_structure(notification2_structures[notif["type"]])
                              for notif in passes[0]["notifications"]]
# passes[1]["notifications"] = []
#
# for notif in passes[0]["notifications"]:
#     notif2 = dict(bin1=binary.fpop(7, bytes))
#     extra = binary.fpop_structure(notification_suffixes[notif["type"]])
#     notif2.update(extra)
#     passes[1]["notifications"].append(notif2)

# ================================ #
# ==== Third pass starts here ==== #
# ================================ #

# traits, then order data for players, cities, and buildingGroups
for key in third_pass_structure:
    locations[2][key] = binary.tell()
    passes[2][key] = binary.fpop_structure(third_pass_structure[key])

# Notifications again
locations[2]["notifications"] = binary.tell()
passes[2]["notifications"] = [binary.fpop_structure(notification2_structures[notif["type"]])
                              for notif in passes[0]["notifications"]]
# passes[2]["notifications"] = []
# for notif in passes[0]["notifications"]:
#     notif3 = dict(bin1=binary.fpop(7, bytes))
#     extra = binary.fpop_structure(notification_suffixes[notif["type"]])
#     notif3.update(extra)
#     passes[2]["notifications"].append(notif3)

# A dummy value because the tiles data skips a pass for some reason.
passes[2]["tiles"] = [{} for tile in passes[0]["tiles"]]

# ================================= #
# ==== Fourth pass starts here ==== #
# ================================= #

# Tiles, units
for key in fourth_pass_structure:
    locations[3][key] = binary.tell()
    passes[3][key] = binary.fpop_structure(fourth_pass_structure[key])

# Notifications *again*
locations[3]["notifications"] = binary.tell()
passes[3]["notifications"] = [binary.fpop_structure(notification2_structures[notif["type"]])
                              for notif in passes[0]["notifications"]]
# passes[3]["notifications"] = []
# for notif in passes[0]["notifications"]:
#     notif4 = dict(bin1=binary.fpop(7, bytes))
#     extra = binary.fpop_structure(notification_suffixes[notif["type"]])
#     notif4.update(extra)
#     passes[3]["notifications"].append(notif4)

# ================================ #
# ==== Fifth pass starts here ==== #
# ================================ #

# Seems to be just notifications for a fifth and final time
locations[4]["notifications"] = binary.tell()
passes[4]["notifications"] = [binary.fpop_structure(notification2_structures[notif["type"]])
                              for notif in passes[0]["notifications"]]
# passes[4]["notifications"] = []
# for notif in passes[0]["notifications"]:
#     notif5 = dict(bin1=binary.fpop(7, bytes))
#     extra = binary.fpop_structure(notification_suffixes[notif["type"]])
#     notif5.update(extra)
#     passes[4]["notifications"].append(notif5)

# ============================= #
# ==== Rearrange by passes ==== #
# ============================== #

zippable = ["actions", "traits", "players", "tiles", "features", "cities", "building_groups", "buildings",
            "units", "weapons", "magic_items", "notifications"]

rearranged = {}
# from [{"actions": pass1_actions, "traits": pass1_traits}, {"actions": pass2_actions, "traits": pass2_traits}]
# to {"actions": [pass1_actions, pass2_actions] "traits": [pass1_traits, pass2_traits]}
for section_title in passes[0].keys():
    rearranged[section_title] = []
    for eachPass in passes:
        try:
            rearranged[section_title].append(eachPass[section_title])
        except KeyError:
            pass

zipped = {}

for section_title, section in rearranged.items():
    if section_title in zippable:
        zipped[section_title] = list(zip(*section))
    else:
        zipped[section_title] = section

# =================================== #
# ==== Cleanup and testing tools ==== #
# =================================== #

if testing:
    lengths = {key: trylen(passes[0][key]) for key in passes[0]}
    print("Found...")
    for key in passes[0]:
        print(f"{lengths[key]} {key}")

print("Position in file as of end of reading:")
print(binary.tell())

with open(json_output_path, 'w') as file:
    json.dump(zipped, file, cls=b.BytesJSONEncoder, indent="    ")

if not testing:
    binary.close()
