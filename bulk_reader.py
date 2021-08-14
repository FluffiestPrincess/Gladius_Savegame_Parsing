from bulk_reader_tools import *

testing = True
input_dir = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\unpacked saves"
input_file = r"robots vs robots.bulk"
input_path = os.path.join(input_dir, input_file)
json_output_path = os.path.splitext(input_path)[0] + ".json"

# According to Rok, structure is:
# world parameters, climates, events, actions, traits, players, tiles, features, cities,
# buildingGroups, buildings, units, weapons, items, quests, notifications
# In five passes

master = {}
locations = {}
data = getfile(input_path)

for key in master_structure:
    locations[key] = data.tell()
    master[key] = data.fpop_structure(master_structure[key])

locations["notifications"] = data.tell()
notification_count = data.fpop(b.UINT)
master["notifications"] = []
for n in range(notification_count):
    notif = dict(type=data.fpop(b.STRING),
                 number=data.fpop(b.UINT),
                 player=data.fpop(b.UINT),
                 bin1=data.fpop(3, bytes))
    extra = data.fpop_structure(notification_types[notif["type"]])
    notif.update(extra)
    master["notifications"].append(notif)

# ================================= #
# ==== Second pass starts here ==== #
# ================================= #

# current player, actions, traits, players, tiles, features, cities,
# buildingGroups, buildings, units, weapons, items, quests, notifications

master["current_player"] = data.fpop(b.UINT)
locations["actions2"] = data.tell()
master["actions2"] = []
for action in master["actions"]:
    if is_weapon(action["path"]):
        my_data = data.fpop_structure(action2_weapon_structure)
        master["actions2"].append(my_data)
    else:
        my_data = data.fpop_structure(action2_normal_structure)
        master["actions2"].append(my_data)

locations["traits2"] = data.tell()
master["traits2"] = data.fpop_structure([trait2_structure, len(master["traits"])])

locations["players2"] = data.tell()
master["players2"] = data.fpop_structure([player2_structure, len(master["players"])])

locations["tiles2"] = data.tell()
master["tiles2"] = data.fpop_structure([tile2_structure, len(master["tiles"])])

locations["features2"] = data.tell()
master["features2"] = data.fpop_structure([feature2_structure, len(master["features"])])

locations["cities2"] = data.tell()
master["cities2"] = data.fpop_structure([city2_structure, len(master["cities"])])

locations["building_groups2"] = data.tell()
master["building_groups2"] = data.fpop_structure([building_group2_structure, len(master["building_groups"])])

locations["buildings2"] = data.tell()
master["buildings2"] = data.fpop_structure([building2_structure, len(master["buildings"])])

locations["units2"] = data.tell()
master["units2"] = data.fpop_structure([unit2_structure, len(master["units"])])

locations["weapons2"] = data.tell()
master["weapons2"] = data.fpop_structure([weapon2_structure, len(master["weapons"])])

locations["magic_items2"] = data.tell()
master["magic_items2"] = data.fpop_structure([[b.INT], len(master["magic_items"])])

locations["quests2"] = data.tell()

if len(master["quests"]) != 0:
    # Need to deserialize the quests section, which sucks.
    # I'm not going to try very hard since there's no need to write quests.
    first_notif_type = master["notifications"][0]["type"]
    first_notif_prefix = bytes(str(notification2_prefix_lengths[first_notif_type]), "UTF-8")
    first_notif_re = b'[\x00-\x01]{' + first_notif_prefix + rb'}\w{5}'
    quest2_binary = b.DataFormat(re.compile(first_notif_re), bytes, inclusive=False)
    master["quests2"] = data.fpop_structure(quest2_binary)
else:
    master["quests2"] = b''

locations["notifications2"] = data.tell()
master["notifications2"] = []

for notif in master["notifications"]:
    notif2 = dict(bin1=data.fpop(7, bytes))
    extra = data.fpop_structure(notification_types[notif["type"]])
    notif2.update(extra)
    master["notifications2"].append(notif2)

# ================================ #
# ==== Third pass starts here ==== #
# ================================ #

# traits, players, tiles, features, cities,
# buildingGroups, buildings, units, weapons, items, quests, notifications

print("Position in file as of end of reading:")
print(data.tell())
