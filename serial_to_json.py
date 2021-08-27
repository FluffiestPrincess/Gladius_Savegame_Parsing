from bulk_reader_tools import *

testing = True
passes = [{}, {}, {}, {}, {}]  # The main data structure
locations = [{}, {}, {}, {}, {}]  # Location within the bulk file of each interesting section

# Used for testing
input_path = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\unpacked saves" \
             r"\Enslavers.bulk"

# ====================================================================== #
# ==== Get the name of the binary data file and open it for reading ==== #
# ====================================================================== #

if not testing:
    parser = argparse.ArgumentParser(description="Deserializes the bulk files into native Python objects.")
    parser.add_argument("filename")
    args = parser.parse_args()
    input_path = os.path.abspath(args.filename)

json_output_path = os.path.splitext(input_path)[0] + ".json"

binary = getfile(input_path)

# ================================ #
# ==== First pass starts here ==== #
# ================================ #

# world parameters, climates, events, actions, traits, players, tiles, features, cities,
# buildingGroups, buildings, units, weapons, items, quests, notifications

for key in first_pass_structure:
    locations[0][key] = binary.tell()
    passes[0][key] = binary.fpop_structure(first_pass_structure[key])

locations[0]["notifications"] = binary.tell()
notification_count = binary.fpop(b.UINT)
passes[0]["notifications"] = []
for n in range(notification_count):
    notif = dict(type=binary.fpop(b.STRING),
                 number=binary.fpop(b.UINT),
                 player=binary.fpop(b.UINT),
                 bin1=binary.fpop(3, bytes))
    extra = binary.fpop_structure(notification_types[notif["type"]])
    notif.update(extra)
    passes[0]["notifications"].append(notif)

# ======================================================= #
# ==== Allocating length fields to subsequent passes ==== #
# ======================================================= #

for structure in [second_pass_structure, third_pass_structure, fourth_pass_structure, fifth_pass_structure]:
    for key in structure:
        length = len(passes[0][key])
        structure[key][1] = length

# ================================= #
# ==== Second pass starts here ==== #
# ================================= #

# ID of the current active player
passes[1]["current_player"] = binary.fpop(b.UINT)

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
passes[1]["notifications"] = []

for notif in passes[0]["notifications"]:
    notif2 = dict(bin1=binary.fpop(7, bytes))
    extra = binary.fpop_structure(notification_types[notif["type"]])
    notif2.update(extra)
    passes[1]["notifications"].append(notif2)

# ================================ #
# ==== Third pass starts here ==== #
# ================================ #

# traits, then order data for players, cities, and buildingGroups
for key in third_pass_structure:
    locations[2][key] = binary.tell()
    passes[2][key] = binary.fpop_structure(third_pass_structure[key])

# Notifications again
locations[2]["notifications"] = binary.tell()
passes[2]["notifications"] = []
for notif in passes[0]["notifications"]:
    notif3 = dict(bin1=binary.fpop(7, bytes))
    extra = binary.fpop_structure(notification_types[notif["type"]])
    notif3.update(extra)
    passes[2]["notifications"].append(notif3)

# ================================= #
# ==== Fourth pass starts here ==== #
# ================================= #

# Tiles, units
for key in fourth_pass_structure:
    locations[3][key] = binary.tell()
    passes[3][key] = binary.fpop_structure(fourth_pass_structure[key])

# Notifications *again*
locations[3]["notifications"] = binary.tell()
passes[3]["notifications"] = []
for notif in passes[0]["notifications"]:
    notif4 = dict(bin1=binary.fpop(7, bytes))
    extra = binary.fpop_structure(notification_types[notif["type"]])
    notif4.update(extra)
    passes[3]["notifications"].append(notif4)

# ================================ #
# ==== Fifth pass starts here ==== #
# ================================ #

# Seems to be just notifications for a fifth and final time
locations[4]["notifications"] = binary.tell()
passes[4]["notifications"] = []
for notif in passes[0]["notifications"]:
    notif5 = dict(bin1=binary.fpop(7, bytes))
    extra = binary.fpop_structure(notification_types[notif["type"]])
    notif5.update(extra)
    passes[4]["notifications"].append(notif5)

# =================================== #
# ==== Cleanup and testing tools ==== #
# =================================== #

if testing:
    print("Position in file as of end of reading:")
    print(binary.tell())
if not testing:
    binary.close()
