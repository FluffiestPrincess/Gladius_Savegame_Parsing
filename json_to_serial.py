import argparse
import os
import json
import configparser
from bulk_reader_tools import *

testing = True
master_config_name = "Config.ini"
test_file_name = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\unpacked saves" \
                 r"\Enslavers.json"

config = configparser.ConfigParser(allow_no_value=True)
# Default behaviour is to make all config option names lowercase
# We don't want to do that so we override optionxform
config.optionxform = lambda option: option
config.read(master_config_name)

passes = [{}, {}, {}, {}, {}]
locations = [{}, {}, {}, {}, {}]  # Location within the bulk file of each interesting section

# ==================================================================== #
# ==== Get the name of the json data file and open it for reading ==== #
# ==================================================================== #

if testing:
    input_path = test_file_name
else:
    parser = argparse.ArgumentParser(description="Serializes json files into the binary component of a Gladius saved "
                                                 "game.")
    parser.add_argument("filename")
    args = parser.parse_args()
    input_path = os.path.abspath(args.filename)

serial_output_path = os.path.splitext(input_path)[0] + "_2.bin"
config_output_path = os.path.splitext(input_path)[0] + "_2.ini"

print(f"Serializing {os.path.basename(input_path)}")

with open(input_path, "r") as file:
    consolidated_data = json.load(file, object_hook=b.bytes_object_hook)

raw = open(serial_output_path, 'wb', buffering=0)
# noinspection PyTypeChecker
binary = b.BinWriter(raw)

# ====================================================== #
# ==== Save some data to the ini file for use later ==== #
# ====================================================== #

config_out = configparser.ConfigParser(allow_no_value=True)

# Default behaviour is to make all config option names lowercase
# We don't want to do that so we override optionxform
config_out.optionxform = lambda option: option
config_out.add_section("HEADER")
config_out.add_section("MODS")

# These values are stored in the master config file
for value in ["version", "branch", "revision", "build"]:
    config_out["HEADER"][value] = config["GLADIUS"][value]

current_player_id = consolidated_data["world_params"][1]["current_player"]

config_out["HEADER"]["steamuser"] = consolidated_data["players"][current_player_id][0]["name"]
config_out["HEADER"]["turn"] = str(consolidated_data["world_params"][0]["turn_number"])
config_out["HEADER"]["checksum"] = "0"
config_out["HEADER"]["mod_count"] = str(len(consolidated_data["world_params"][0]["mods"]))

for mod in consolidated_data["world_params"][0]["mods"]:
    # noinspection PyTypeChecker
    config_out["MODS"][mod] = None

with open(config_output_path, 'w') as file:
    config_out.write(file)

# ============================== #
# ==== Separate into passes ==== #
# ============================== #

zipped_keys = ["actions", "traits", "players", "tiles", "features", "cities", "building_groups", "buildings",
               "units", "weapons", "magic_items"]

unzipped_data = {key: (list(zip(*value))
                       if (key in zipped_keys)
                       else value)
                 for key, value in consolidated_data.items()}

for n in range(len(passes)):
    passes[n] = {key: value[n] for key, value in unzipped_data.items() if len(value) > n}

if not testing:
    del unzipped_data
    del consolidated_data  # Save memory

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
binary.translate(passes[1]["world_params"]["current_player"], b.UINT)

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
