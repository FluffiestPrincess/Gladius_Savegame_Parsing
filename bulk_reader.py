import argparse
import os
import re
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
    file_in_name = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\unpacked saves" \
                   r"\Enslavers.bulk"
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
    unknown_int=b.UINT  # I have genuinely no idea
)

# I'm not honestly sure what's going on here
# According to Rok, the next sections are "climates, events, actions, traits"
# But I can only see three distinct sections

climates_structure = b.DataFormat(48, bytes)

# According to Rok, this is either events or actions
things1_structure = dict(
    path=b.NZ_STRING,
    bin=b.DataFormat(25, bytes)
)

# According to Rok, this is either actions or traits
things2_structure = dict(
    number=b.INT,
    names=[b.NZ_STRING, uint_plus_one],
    bin=b.DataFormat(23, bytes)
)

player_structure = dict(
    bin_1=b.DataFormat(34, bytes),
    economy_score=[b.DOUBLE],
    military_score=[b.DOUBLE],
    research_score=[b.DOUBLE],
    items_1=[(b.NZ_STRING, b.INT)],
    items_2=[(b.NZ_STRING, b.DOUBLE)],
    items_3=[(b.NZ_STRING, b.DOUBLE)],
    bin_5=b.DataFormat(8, bytes),
    resources_cumulative=[(b.NZ_STRING, b.DOUBLE)],
    items_4=[(b.NZ_STRING, b.INT)],
    items_5=[(b.NZ_STRING, b.INT)],
    items_6=[(b.NZ_STRING, b.INT)],
    name=b.STRING,
    faction=b.STRING,
    is_AI=b.BOOL,
    bin_7=b.DataFormat(38, bytes),
    colour=b.STRING,
    bool_1=b.BOOL,
    bin_8=b.DataFormat(8, bytes),
    items_7=[b.NZ_STRING],
    items_8=[b.NZ_STRING],
    DLCs=[b.NZ_STRING],
    bin_9=b.DataFormat(104, bytes),
    items_9=[b.NZ_STRING],
    items_10=[b.NZ_STRING],
    items_11=[b.NZ_STRING],
    bin_10=b.DataFormat(6, bytes)
)

tile_structure = dict(
    number=b.UINT,
    mystery_int=b.UINT,
    bin1=b.DataFormat(10, bytes),
    region_name=b.STRING,
    bin2=b.DataFormat(8, bytes),
    quest_tag=b.STRING
)

feature_structure = dict(
    number=b.UINT,
    mystery_int=b.UINT,
    bin1=b.DataFormat(15, bytes),
    feature=b.STRING
)

city_structure = dict(
    number=b.UINT,
    bin1=b.DataFormat(26, bytes),
    faction1=b.STRING,
    faction2=b.STRING,
    name=b.STRING,
    bin2=b.DataFormat(9, bytes)
)

building_group_structure = dict(
    number=b.UINT,
    bin=b.DataFormat(26, bytes),
    type=b.STRING
)

building_structure = dict(
    number=b.UINT,
    type=b.STRING,
    bin=b.DataFormat(2, bytes)
)

unit_structure = dict(
    number=b.UINT,
    bin1=b.DataFormat(26, bytes),
    type=b.STRING,
    bin2=b.DataFormat(50, bytes),
    name=b.STRING,
    bin3=b.DataFormat(11, bytes)
)

# Tile height, possibly?
mystery_structure = dict(
    number=b.UINT,
    bool1=b.BOOL,
    bool2=b.BOOL,
    int1=b.INT
)

magic_item_structure = dict(
    bin1=b.DataFormat(4, bytes),
    name=b.STRING
)

# (Factions/|....[a-z,A-Z]{4,}\x00)
# Either the string "Factions/" (start of the next quest)
# OR four characters (the length marker INT) followed by 4+ letters followed by a null byte (start of the
# notifications section)
quest_binary = b.DataFormat(re.compile(rb'(Factions/|....[a-z,A-Z]{4,}\x00)'), bytes, inclusive=False)

quest_structure = dict(
    name=b.STRING,
    number=b.UINT,
    stage=b.UINT,
    bin1=quest_binary
)

notification_types = dict(
    CityGrown=dict(
        city=b.STRING,
        details=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    FactionDefeated=None,   # Cannot find in sample files
    FactionDiscovered=dict(
        faction=b.UINT,
        bin2=b.DataFormat(4, bytes)
    ),
    FeatureExplored=dict(
        feature=b.STRING,
        details=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    FeatureTypeDiscovered=dict(
        feature=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    LordOfSkullsAppeared=None,
    LordOfSkullsDisppeared=None,
    PlayerLost=b.DataFormat(0, None),  # This is a no-op
    PlayerWon=None,
    PlayerWonElimination=b.DataFormat(0, None),  # This is a no-op
    PlayerWonQuest=b.DataFormat(0, None),  # This is a no-op
    ProductionCompleted=dict(
        produced=b.STRING,
        city=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    QuestAdded=dict(
        bin2=b.DataFormat(4, bytes)
    ),
    QuestCompleted=dict(
        bin2=b.DataFormat(4, bytes)
    ),
    QuestUpdated=dict(
        bin2=b.DataFormat(8, bytes)
    ),
    RegionDiscovered=dict(
        bin2=b.DataFormat(4, bytes)
    ),
    ResearchCompleted=dict(
        research=b.STRING
    ),
    ResourcesGainedTile=dict(
        amount=b.DOUBLE,
        resource=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    ResourcesGainedUnit=dict(
        amount=b.DOUBLE,
        resource=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    TileAcquired=dict(
        city=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    TileCaptured=dict(
        bin3=b.DataFormat(8, bytes),
        capturer=b.STRING
    ),
    TileCleared=dict(
        city=b.STRING,
        feature=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    UnitAttacked=dict(
        bin3=b.DataFormat(24, bytes),
        unit1=b.STRING,
        bin4=b.DataFormat(24, bytes),
        unit2=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    UnitCaptured=dict(
        bin3=b.DataFormat(4, bytes),
        capturer=b.STRING,
        capturee=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    UnitKilled=dict(
        bin3=b.DataFormat(24, bytes),
        killer=b.STRING,
        bin4=b.DataFormat(24, bytes),
        killee=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    UnitGainedTrait=dict(
        trait=b.STRING,
        bin2=b.DataFormat(4, bytes),
        unit=b.STRING
    ),
    UnitTransformed=None,  # I'm pretty sure this is CSM DLC only
    UnitTypeDiscovered=dict(
        bool=b.BOOL,
        unit=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    UnitUsedActionOn=dict(
        bin3=b.DataFormat(4, bytes),
        action=b.STRING,
        bin4=b.DataFormat(4, bytes),
        user=b.STRING,
        bin5=b.DataFormat(4, bytes),
        target=b.STRING,
        bin2=b.DataFormat(4, bytes)
    )
)

header = data.fpop_structure(header_structure)
climate_start = data.tell()
climates = data.fpop_structure([climates_structure, b.SCHAR])  # why is this a SCHAR when everything else is UINTs?
unk_bytes_1 = data.fpop(4, bytes)  # Possibly an int, possibly the length marker for events
things1_start = data.tell()
things1 = data.fpop_structure([things1_structure])
things2_start = data.tell()
things2 = data.fpop_structure([things2_structure])
players_start = data.tell()
players = data.fpop_structure([player_structure])
tiles_start = data.tell()
tiles = data.fpop_structure([tile_structure])
features_start = data.tell()
features = data.fpop_structure([feature_structure])
cities_start = data.tell()
cities = data.fpop_structure([city_structure])
building_groups_start = data.tell()
building_groups = data.fpop_structure([building_group_structure])
buildings_start = data.tell()
buildings = data.fpop_structure([building_structure])
units_start = data.tell()
units = data.fpop_structure([unit_structure])
mysteries_start = data.tell()
mysteries = data.fpop_structure([mystery_structure])
magic_items_start = data.tell()
magic_items = data.fpop_structure([magic_item_structure])
quests_start = data.tell()
quests = data.fpop_structure([quest_structure])
notifications_start = data.tell()
notification_count = data.fpop(b.UINT)
notifications = []
for n in range(notification_count):
    notif = dict(type=data.fpop(b.STRING),
                 number=data.fpop(b.UINT),
                 player=data.fpop(b.UINT),
                 bin1=data.fpop(3, bytes))
    extra = data.fpop_structure(notification_types[notif["type"]])
    notif.update(extra)
    notifications.append(notif)
binary_hell_start = data.tell()

# data.close()
input("Press enter.")
