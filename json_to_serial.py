import argparse
import os
import json
from bulk_reader_tools import *

testing = True
locations = [{}, {}, {}, {}, {}]  # Location within the bulk file of each interesting section

# Used for testing
input_path = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\unpacked saves" \
             r"\Enslavers.json"

# ====================================================================== #
# ==== Get the name of the binary data file and open it for reading ==== #
# ====================================================================== #

if not testing:
    parser = argparse.ArgumentParser(description="Serializes json files into the binary component of a Gladius saved "
                                                 "game.")
    parser.add_argument("filename")
    args = parser.parse_args()
    input_path = os.path.abspath(args.filename)

serial_output_path = os.path.splitext(input_path)[0] + ".bin"

print(f"Serializing {os.path.basename(input_path)}")

with open(input_path, "r") as file:
    passes = json.load(file, object_hook=b.bytes_object_hook)

raw = open(serial_output_path, 'wb', buffering=0)
# noinspection PyTypeChecker
binary = b.BinWriter(raw)

# ================================ #
# ==== First pass starts here ==== #
# ================================ #

# world parameters, climates
for key in first_pass_structure_1:
    locations[0][key] = binary.tell()
    binary.write_structure(passes[0][key], first_pass_structure_1[key])

# Events (always blank)
locations[0]["events"] = binary.tell()
binary.translate(0, b.UINT)

# Actions
locations[0]["actions"] = binary.tell()
binary.translate(len(passes[0]["actions"]), b.UINT)
for action in passes[0]["actions"]:
    if action["path"].endswith("CycleWeapon"):
        binary.write_structure(action, action_cycle_weapon_structure)
    else:
        binary.write_structure(action, action_structure)

# Traits, players, tiles, features, cities, buildingGroups, buildings, units, weapons, items, quests.
for key in first_pass_structure_2:
    locations[0][key] = binary.tell()
    binary.write_structure(passes[0][key], first_pass_structure_2[key])

# Finally, notifications.
locations[0]["notifications"] = binary.tell()
binary.translate(len(passes[0]["notifications"]), b.UINT)
[binary.write_structure(notification, notification_structures[notification["type"]])
 for notification in passes[0]["notifications"]]

# ================================= #
# ==== Second pass starts here ==== #
# ================================= #

# ID of the current active player
binary.translate(passes[1]["current_player"], b.UINT)

# Actions require special handling because of the weapon-actions issue
locations[1]["actions"] = binary.tell()

for n in range(len(passes[0]["actions"])):
    if is_weapon(passes[0]["actions"][n]["path"]):
        binary.write_structure(passes[1]["actions"][n], action2_weapon_structure)
    else:
        binary.write_structure(passes[1]["actions"][n], action2_normal_structure)

# traits, players, tiles, features, cities, buildingGroups, buildings, units, weapons, items
for key in second_pass_structure:
    locations[1][key] = binary.tell()
    binary.write_structure(passes[1][key], second_pass_structure[key])

# Quests - not deserialized, just scanned
locations[1]["quests"] = binary.tell()
binary.write_structure(passes[1]["quests"], b.DataFormat(None, bytes))

# Notifications
locations[1]["notifications"] = binary.tell()
[binary.write_structure(data, notification2_structures[structure_hint["type"]])
 for data, structure_hint
 in zip(passes[1]["notifications"], passes[0]["notifications"])]

# ================================ #
# ==== Third pass starts here ==== #
# ================================ #

# traits, then order data for players, cities, and buildingGroups
for key in third_pass_structure:
    locations[2][key] = binary.tell()
    passes[2][key] = binary.write_structure(passes[2][key], third_pass_structure[key])

# Notifications again
locations[2]["notifications"] = binary.tell()
[binary.write_structure(data, notification2_structures[structure_hint["type"]])
 for data, structure_hint
 in zip(passes[2]["notifications"], passes[0]["notifications"])]

# ================================= #
# ==== Fourth pass starts here ==== #
# ================================= #

# Tiles, units
for key in fourth_pass_structure:
    locations[3][key] = binary.tell()
    passes[3][key] = binary.write_structure(passes[3][key], fourth_pass_structure[key])

# Notifications *again*
locations[3]["notifications"] = binary.tell()
[binary.write_structure(data, notification2_structures[structure_hint["type"]])
 for data, structure_hint
 in zip(passes[3]["notifications"], passes[0]["notifications"])]

# ================================ #
# ==== Fifth pass starts here ==== #
# ================================ #

# Seems to be just notifications for a fifth and final time
locations[4]["notifications"] = binary.tell()
[binary.write_structure(data, notification2_structures[structure_hint["type"]])
 for data, structure_hint
 in zip(passes[4]["notifications"], passes[0]["notifications"])]

binary.close()
raw.close()
