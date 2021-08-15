from bulk_reader_tools import *

testing = True
input_dir = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\unpacked saves"
input_file = r"robots vs robots.bulk"
input_path = os.path.join(input_dir, input_file)
json_output_path = os.path.splitext(input_path)[0] + ".json"

passes = [{}, {}, {}, {}, {}]
locations = [{}, {}, {}, {}, {}]
data = getfile(input_path)

# ================================ #
# ==== First pass starts here ==== #
# ================================ #

# world parameters, climates, events, actions, traits, players, tiles, features, cities,
# buildingGroups, buildings, units, weapons, items, quests, notifications

for key in first_pass_structure:
    locations[0][key] = data.tell()
    passes[0][key] = data.fpop_structure(first_pass_structure[key])

locations[0]["notifications"] = data.tell()
notification_count = data.fpop(b.UINT)
passes[0]["notifications"] = []
for n in range(notification_count):
    notif = dict(type=data.fpop(b.STRING),
                 number=data.fpop(b.UINT),
                 player=data.fpop(b.UINT),
                 bin1=data.fpop(3, bytes))
    extra = data.fpop_structure(notification_types[notif["type"]])
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
passes[1]["current_player"] = data.fpop(b.UINT)

locations[1]["actions"] = data.tell()
passes[1]["actions"] = []
for action in passes[0]["actions"]:
    if is_weapon(action["path"]):
        my_data = data.fpop_structure(action2_weapon_structure)
        passes[1]["actions"].append(my_data)
    else:
        my_data = data.fpop_structure(action2_normal_structure)
        passes[1]["actions"].append(my_data)

# traits, players, tiles, features, cities, buildingGroups, buildings, units, weapons, items
for key in second_pass_structure:
    locations[1][key] = data.tell()
    passes[1][key] = data.fpop_structure(second_pass_structure[key])

# Quests - not deserialized, just scanned
locations[1]["quests"] = data.tell()
if len(passes[0]["quests"]) != 0:
    first_notif_type = passes[0]["notifications"][0]["type"]
    first_notif_prefix = bytes(str(notification2_prefix_lengths[first_notif_type]), "UTF-8")
    first_notif_re = b'[\x00-\x01]{' + first_notif_prefix + rb'}\w{5}'
    quest2_binary = b.DataFormat(re.compile(first_notif_re), bytes, inclusive=False)
    passes[1]["quests"] = data.fpop_structure(quest2_binary)
else:
    passes[1]["quests"] = b''

# Notifications
locations[1]["notifications"] = data.tell()
passes[1]["notifications"] = []

for notif in passes[0]["notifications"]:
    notif2 = dict(bin1=data.fpop(7, bytes))
    extra = data.fpop_structure(notification_types[notif["type"]])
    notif2.update(extra)
    passes[1]["notifications"].append(notif2)

# ================================ #
# ==== Third pass starts here ==== #
# ================================ #

# traits, then order data for players, cities, and buildingGroups
for key in third_pass_structure:
    locations[2][key] = data.tell()
    passes[2][key] = data.fpop_structure(third_pass_structure[key])

# locations[2]["traits"] = data.tell()
# passes[2]["traits"] = data.fpop_structure([trait3_structure, len(passes[0]["traits"])])
#
# locations[2]["players"] = data.tell()
# passes[2]["players"] = data.fpop_structure([order_structure, len(passes[0]["players"])])
#
# locations[2]["cities"] = data.tell()
# passes[2]["cities"] = data.fpop_structure([order_structure, len(passes[0]["cities"])])
#
# locations[2]["building_groups"] = data.tell()
# passes[2]["building_groups"] = data.fpop_structure([order_structure, len(passes[0]["building_groups"])])
#
# locations[2]["units"] = data.tell()
# passes[2]["units"] = data.fpop_structure([order_structure, len(passes[0]["units"])])

# Notifications again
locations[2]["notifications"] = data.tell()
passes[2]["notifications"] = []
for notif in passes[0]["notifications"]:
    notif3 = dict(bin1=data.fpop(7, bytes))
    extra = data.fpop_structure(notification_types[notif["type"]])
    notif3.update(extra)
    passes[2]["notifications"].append(notif3)

# ================================= #
# ==== Fourth pass starts here ==== #
# ================================= #

# Tiles, units
for key in fourth_pass_structure:
    locations[3][key] = data.tell()
    passes[3][key] = data.fpop_structure(fourth_pass_structure[key])

# locations[3]["tiles"] = data.tell()
# passes[3]["tiles"] = data.fpop_structure([tile4_structure, len(passes[0]["tiles"])])
#
# locations[3]["units"] = data.tell()
# passes[3]["units"] = data.fpop_structure([unit4_structure, len(passes[0]["units"])])

# Notifications *again*
locations[3]["notifications"] = data.tell()
passes[3]["notifications"] = []
for notif in passes[0]["notifications"]:
    notif4 = dict(bin1=data.fpop(7, bytes))
    extra = data.fpop_structure(notification_types[notif["type"]])
    notif4.update(extra)
    passes[3]["notifications"].append(notif4)

# ================================ #
# ==== Fifth pass starts here ==== #
# ================================ #

# Seems to be just notifications for a fifth and final time
locations[4]["notifications"] = data.tell()
passes[4]["notifications"] = []
for notif in passes[0]["notifications"]:
    notif5 = dict(bin1=data.fpop(7, bytes))
    extra = data.fpop_structure(notification_types[notif["type"]])
    notif5.update(extra)
    passes[4]["notifications"].append(notif5)

# =================================== #
# ==== Cleanup and testing tools ==== #
# =================================== #

if testing:
    print("Position in file as of end of reading:")
    print(data.tell())
if not testing:
    data.close()
