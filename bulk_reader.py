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
master["traits2"] = data.fpop_structure([b.QWORD, len(master["traits"])])

mystery_quest_data_re = rb'([\x10-\xff].\x00\x00|[\x01-\xff][\x01-\xff]\x00\x00)'
mystery_quest_data_binary = b.DataFormat(re.compile(mystery_quest_data_re), bytes, inclusive=False)

player2_structure = dict(
    numbers1=[b.INT],
    global_effects=[{"name": b.STRING, "number": b.INT}],
    F=b.DWORD,
    player_id_again=b.UINT,
    quests_in_progress=[b.UINT],
    quests_completed=[b.UINT],
    blank1=b.DWORD,
    # mystery_quest_data=mystery_quest_data_binary,
    # TODO I honestly think this might be
    # {"current": [b.INT], "completed": [b.INT], "unknown": b.DWORD}
    bin1=b.DWORD,
    fog_data=[b.UINT],
    numbers2=[b.INT],
    numbers3=[b.INT],
    numbers4=[b.INT],
    known_enemies=[b.UINT],
    numbers5=[b.INT],
    numbers6=[b.INT]
)

locations["players2"] = data.tell()
master["players2"] = data.fpop_structure([player2_structure, len(master["players"])])

tile2_structure = dict(
    wurds=[(b.STRING, b.INT)],
    eff=b.DWORD,
    numbaz=[b.INT],
    sumtimez_eff=b.QWORD,
    mor_numbaz=[b.INT]
)

locations["tiles2"] = data.tell()
master["tiles2"] = data.fpop_structure([tile2_structure, len(master["tiles"])])

feature2_structure = dict(
    wurds=[(b.STRING, b.INT)],
    four=b.INT,
    numba=b.INT,
)

locations["features2"] = data.tell()
master["features2"] = data.fpop_structure([feature2_structure, len(master["features"])])

city2_structure = dict(
    numbers1=[b.INT],
    productions=[{"name": b.STRING, "id": b.INT}],
    bin1=b.DataFormat(8, bytes),
    buildings=[b.INT],
    building_groups=[b.INT]
)  # TODO unfinished

# buildingGroups, buildings, units, weapons, items, quests, notifications

print("Position in file as of end of reading:")
print(data.tell())
