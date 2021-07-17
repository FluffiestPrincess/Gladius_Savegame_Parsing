import argparse
import os
import struct

import binarizer as b


testing = True

# According to Rok, structure is:
# world parameters, climates, events, actions, traits, players, tiles, features, cities,
# buildingGroups, buildings, units, weapons, items, quests, notifications
# In five passes

# The DataFormat to get a 4-byte UINT and add one.
# Only seems to be used in one place so far
uint_plus_one = b.DataFormat(4, lambda x: struct.unpack('I', x)[0] + 1)

if testing:
    file_in_name = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames"\
                   r"\save_2\unpacked saves\Rhana Dandra.bulk"
else:
    parser = argparse.ArgumentParser(description="Take a clumsy shot at reading the bulk files.")
    parser.add_argument("filename")
    args = parser.parse_args()
    file_in_name = os.path.abspath(args.filename)

with open(file_in_name, 'r+b') as file:
    data = b.BinReader(file.fileno(), 0)

header_structure = dict(
    unk_bytes_1=b.DataFormat(9, bytes),
    mods=[b.STRING],
    adaptive_turn_timer=b.BOOL,
    AI_controls_disconnected_players=b.BOOL,
    arctic_region_density=b.UINT,
    artefact_density=b.UINT,
    desert_region_density=b.UINT,
    difficulty=b.UINT,
    dlcs=[(b.STRING, b.BOOL)],
    forest_density=b.UINT,
    game_name=b.STRING,
    game_visibility=b.UINT,  # Behaves oddly in single player mode
    imperial_ruins_density=b.UINT,
    jokaero_density=b.UINT,
    land_mass=b.UINT,
    multiplayer=b.BOOL,  # Might actually be the "lord of skulls" setting
    debug_panel_enabled=b.BOOL,  # Multiplayer only
    necron_tomb_density=b.UINT,
    webway_density=b.UINT,
    ork_fungus_density=b.UINT,
    game_pace=b.UINT,
    quests=b.BOOL,
    region_density=b.UINT,
    region_size=b.UINT,
    river_density=b.UINT,
    ruins_vaul_density=b.UINT,
    world_seed=b.UINT,
    simultaneous_turns=b.BOOL,
    world_size=b.UINT,
    special_resource_density=b.UINT,
    tropical_region_density=b.UINT,
    turn_number=b.UINT,
    turn_timer=b.UINT,
    volcanic_region_density=b.UINT,
    wire_weed_density=b.UINT,
    unk_int_3=b.UINT
)

header = data.fpop_structure(header_structure)

# I'm not honestly sure what's going on here
# According to Rok, the next sections are "climates, events, actions, traits"
# But I can only see three distinct sections

# Why is this one number a SIGNED CHAR when everything else is INTs?
climates_count = data.fpop(b.SCHAR)
climates = data.fpop_structure([b.DataFormat(48, bytes), climates_count])

unk_bytes_1 = data.fpop(4, bytes)  # Possibly an int, possibly the length marker for events

# According to Rok, this is either events or actions
things1_structure = dict(
    path=b.NZ_STRING,
    bin=b.DataFormat(25, bytes)
)
things1 = data.fpop_structure([things1_structure])

# According to Rok, this is either actions or traits
things2_structure = dict(
    number=b.INT,
    names=[b.NZ_STRING, uint_plus_one],
    bin=b.DataFormat(23, bytes)
)
things2 = data.fpop_structure([things2_structure])

player_count = data.fpop(b.INT)
player_structure = dict(
    player_bin_1=b.DataFormat(34, bytes),
    player_bin_2=[b.QWORD],
    player_bin_3=[b.QWORD],
    player_bin_4=[b.QWORD],
    player_items_1=[(b.NZ_STRING, b.INT)],
    player_items_2=[(b.NZ_STRING, b.DOUBLE)],
    player_items_3=[(b.NZ_STRING, b.DOUBLE)],
    player_bin_5=b.DataFormat(8, bytes),
    player_resources=[(b.NZ_STRING, b.DOUBLE)],
    player_items_4=[(b.NZ_STRING, b.INT)],
    player_items_5=[(b.NZ_STRING, b.INT)],
    player_items_6=[(b.NZ_STRING, b.INT)],
    player_name=b.STRING,
    player_faction=b.STRING,
    player_is_AI=b.BOOL,
    player_bin_7=b.DataFormat(38, bytes),
    player_colour=b.STRING,
    player_bool_1=b.BOOL,
    player_bin_8=b.DataFormat(8, bytes),
    player_items_7=[b.NZ_STRING],
    player_items_8=[b.NZ_STRING],
    player_DLCs=[b.NZ_STRING],
    player_bin_9=b.DataFormat(104, bytes),
    player_items_9=[b.NZ_STRING],
    player_items_10=[b.NZ_STRING],
    player_items_11=[b.NZ_STRING],
    player_bin_10=b.DataFormat(6, bytes)
)
players = data.fpop_structure([player_structure, player_count])

tile_structure = dict(
    number=b.UINT,
    mystery_int=b.UINT,
    bin1=b.DataFormat(10, bytes),
    region_name=b.STRING,
    bin2=b.DataFormat(9, bytes),
)
tiles = data.fpop_structure([tile_structure])

# features
feature_structure = dict(
    number=b.UINT,
    mystery_int=b.UINT,
    bin1=b.DataFormat(15, bytes),
    feature=b.STRING
)
features = data.fpop_structure([feature_structure])

# cities,  buildingGroups, buildings, units, weapons, items, quests, notifications

data.close()
input("Press enter.")
