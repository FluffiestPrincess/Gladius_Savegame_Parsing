import argparse
import os
import re
import binarizer as b


def getfile(file=None):
    if file is None:
        parser = argparse.ArgumentParser(description="Deserializes the bulk files into native Python objects.")
        parser.add_argument("filename")
        args = parser.parse_args()
        file = os.path.abspath(args.filename)
    print(f"Parsing {os.path.basename(file)}")
    # If you try to open(file_in_name, 'rb') without setting access=b.mmap.ACCESS_READ, you get an error.
    with open(file, 'rb') as file:
        data = b.BinReader(file.fileno(), 0, access=b.mmap.ACCESS_READ)
    return data


# To make it slightly easier to get the lengths of structures.
def trylen(x):
    try:
        return len(x)
    except TypeError:
        return 1


def events_error(_):
    raise NotImplementedError("This save file contains an Events section, which I unfortunately do not yet know how "
                              "to parse.")


#  A bit of a hack; this is a valid DataFormat, but if it's ever used it returns NotImplementedError.
events_notimplemented_structure = b.DataFormat(0, events_error)

# Actions that are also weapons seem to work differently - they have an extra byte of data at the end.
# Because of this, we need a mechanism to identify them.
weapons_directory = r"C:\Program Files (x86)\Steam\steamapps\common\Warhammer 40000 Gladius - Relics of " \
                    r"War\Data\World\Weapons"
weapons = [os.path.splitext(file)[0].lower() for file in os.listdir(weapons_directory)]
weapon_like_actions = ["throwGrenade",
                       "useWeapon",
                       "heavyBombClusters",
                       "moltenBeam",
                       "lifeLeech",
                       "psychicMaelstrom",
                       "rollOverThem",
                       "flameBreath",
                       "exaltedStrike",
                       "destroyerBlades",
                       "mechatendrils",
                       "eldritchStorm",
                       "serpentShield",
                       "stomp",
                       "voidStrike",
                       "transdimensionalThunderbolt",
                       "skyOfFallingStars",
                       "seismicAssault",
                       "burnaBomb",
                       "attackSquig",
                       "frazzle",
                       "powerStrike",
                       "preciseShot"]
weapon_like_actions = [s.lower() for s in weapon_like_actions]
weapons_log = []


def is_weapon(path):
    global weapons_log
    split_path = path.split('/')
    # This is only very approximate
    if split_path[0] == "Units"\
            and split_path[-1].lower() in weapons \
            and len(split_path) >= 5 \
            and split_path[-2].lower() in weapon_like_actions:
        weapons_log.append(f"{path} is a weapon - begins with Units, ends in a weapon, length >= 5, penultimate "
                           f"section {split_path[-2].lower()} found in weapon_like_actions")
        return True
    elif split_path[0] == "Units" \
            and split_path[-1].lower() in weapons \
            and len(split_path) >= 5:
        weapons_log.append(f"{path} is probably a weapon - begins with Units, ends in a weapon, length >= 5, but "
                           f"penultimate section {split_path[-2].lower()} NOT found in weapon_like_actions")
        raise RuntimeError(f"Unable to determine if {path} is a weapon.")
    elif split_path[-2].lower() in weapon_like_actions:
        weapons_log.append(f"{path} MIGHT be a weapon - penultimate "
                           f"section {split_path[-2].lower()} found in weapon_like_actions")
        raise RuntimeError(f"Unable to determine if {path} is a weapon.")
    elif split_path[-1].lower() == "spawnunits":
        weapons_log.append(f"""{path} isn't a weapon, but it is "spawn units".""")
        return True
    else:
        return False


# Analysis basically done, except the weird initial bytes.
world_params_structure = dict(
    bin1=b.DataFormat(8, bytes),
    achievements_enabled=b.BOOL,
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
    multiplayer=b.BOOL,
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
    wildlife_density=b.UINT,
    wire_weed_density=b.UINT
)

# Note that these do NOT correspond to tile coordinates!
# The right-hand edge of a Medium-size map is around 8000.
# I'm not going to do more analysis because these are purely cosmetic.
climate_structure = dict(
    x_coord=b.FLOAT,
    y_coord=b.FLOAT,
    arctic=b.DOUBLE,  # I've only ever seen a value of 1 for any of these.
    desert=b.DOUBLE,
    unknown_climate=b.DOUBLE,  # Probably unused
    jungle=b.DOUBLE,
    volcanic=b.DOUBLE,
)

# Basically done
action_structure = dict(
    path=b.NZ_STRING,
    id1=b.UINT,
    id2=b.UINT,  # Always seems to be the same as id1
    cooldown=b.DOUBLE,  # Confirmed
    not_hold_fire=b.BOOL,  # Guess. Always seems to be 0 for HoldFire and 1 for everything else.
    level=b.UINT,  # Guess
    item_id=b.INT  # -1 if not associated with an item
)

action2_normal_structure = dict(
    linked_traits=[b.INT],
    bin1=b.DWORD,  # Only ever 00 00 00 00
    item_id_2=b.INT  # Beats me why this is listed twice
)

action2_weapon_structure = dict(
    linked_traits=[b.INT],
    bin1=b.DWORD,  # Only ever 00 00 00 00
    item_id=b.INT,
    weapon_id=b.INT
)

# Mostly done
trait_structure = dict(
    id=b.INT,
    prerequisites=[b.NZ_STRING],  # Guess
    name=b.STRING,
    duration=b.DOUBLE,  # Confirmed
    turns_active=b.INT,  # You'd think this could be calculated from the current turn and the start turn, but guess not
    level=b.INT,  # Guess
    maxlevel=b.INT,  # Guess
    Enslaved=b.BOOL,  # Only used by the Enslaved status, as far as I can tell
    start_turn=b.USHORT  # Confirmed, although I don't know why it's a USHORT
)

trait2_structure = dict(
    player=b.INT,
    origin_unit=b.INT  # for traits that apply to one entity but are caused by another
)

trait3_structure = dict(
    linked_action=b.INT
)

player_structure = dict(
    id=b.UINT,
    bin1=b.DataFormat(30, bytes),  # Unknown purpose
    economy_score=[b.DOUBLE],
    military_score=[b.DOUBLE],
    research_score=[b.DOUBLE],
    buildings=[(b.NZ_STRING, b.INT)],  # Count of buildings does not appear to be accurate
    damage_dealt_cumulative=[(b.NZ_STRING, b.DOUBLE)],
    damage_taken_cumulative=[(b.NZ_STRING, b.DOUBLE)],
    bin5=b.DataFormat(8, bytes),  # Unknown purpose
    resources_cumulative=[(b.NZ_STRING, b.DOUBLE)],
    units_created_cumulative=[(b.NZ_STRING, b.INT)],
    units_killed_cumulative=[(b.NZ_STRING, b.INT)],
    units_lost_cumulative=[(b.NZ_STRING, b.INT)],
    name=b.STRING,
    faction=b.STRING,
    is_AI=b.BOOL,
    bin7=b.DataFormat(38, bytes),  # Unknown purpose
    colour=b.STRING,
    bin8=b.DataFormat(9, bytes),  # Unknown purpose
    features_seen=[b.NZ_STRING],
    items8=[b.NZ_STRING],  # Unknown purpose
    DLCs=[b.NZ_STRING],
    bin9=b.DataFormat(8, bytes),  # Unknown purpose
    double1=b.DOUBLE,  # Unknown purpose
    energy=b.DOUBLE,
    double2=b.DOUBLE,  # Unknown purpose
    food=b.DOUBLE,
    double3=b.DOUBLE,  # Unknown purpose
    influence=b.DOUBLE,
    double4=b.DOUBLE,  # Unknown purpose
    ore=b.DOUBLE,
    double5=b.DOUBLE,  # Unknown purpose
    requisition=b.DOUBLE,
    double6=b.DOUBLE,  # Unknown purpose
    research=b.DOUBLE,
    research_unk1=[b.NZ_STRING],  # Frequently the same list as the one below
    research_unk2=[b.NZ_STRING],  # I believe this is research completed
    research_underway=[b.NZ_STRING],
    bin10=b.DataFormat(6, bytes)  # Unknown purpose
)

player2_structure = dict(
    actions=[b.INT],
    global_effects=[{"name": b.STRING, "number": b.INT}],
    F=b.DWORD,
    player_id_again=b.UINT,
    quests_in_progress=[b.UINT],
    quests_completed=[b.UINT],
    blank1=b.DWORD,
    bin11=b.DWORD,
    tiles_revealed=[b.UINT],
    numbers2=[b.INT],
    tiles_watched=[b.INT],
    numbers4=[b.INT],
    known_enemy_factions=[b.UINT],
    regions_discovered=[b.INT],
    numbers6=[b.INT]
)

# Basically done, apart from bin1, which I have a few hints about, and F which is impenetrable
tile_structure = dict(
    id=b.UINT,
    bin1=b.BYTE,  # Normally 1. 0 when under artefacts. I think this might be a flags field though.
    buildings_count=b.UCHAR,  # Includes buildings currently under construction
    x=b.FLOAT,
    y=b.FLOAT,
    height=b.UINT,
    region_name=b.STRING,
    river_in=b.INT,
    river_out=b.INT,
    quest_tag=b.STRING
)

tile2_structure = dict(
    effects=[(b.STRING, b.INT)],
    F=b.DataFormat(4, bytes),  # I have never seen this be anything other than FF FF FF FF
    features=[b.INT],
    city_feature_id=b.INT,  # The ID of the city feature in the Features section
    city_id=b.INT,  # The ID of the parent city in the Cities section
    building_ids=[b.INT]
)

tile4_structure = dict(
    unknown=b.INT
)

# Done apart from two possibly-boolean values that I've only ever seen with one value
feature_structure = dict(
    id=b.UINT,
    bin1=b.BYTE,  # Possibly a boolean
    duration=b.DOUBLE,  # Used for temporary orkoid fungus
    cooldown=b.DOUBLE,  # Used for skull altars
    visited=b.BOOL,  # Used for ruins, skull altars, etc.
    bin3=b.BYTE,  # Possibly a boolean
    feature=b.STRING
)

feature2_structure = dict(
    traits=[(b.STRING, b.INT)],
    owner=b.INT,  # Player ID; will be the ID of the neutral AI controller for most features.
    tile_id=b.INT,
)

# At game start there are no cities or buildings, so analysis of these sections aren't that important.
city_structure = dict(
    id=b.UINT,
    bin1=b.DataFormat(26, bytes),
    faction1=b.STRING,
    faction2=b.STRING,
    name=b.STRING,
    bin2=b.DataFormat(9, bytes)
)

city2_structure = dict(
    numbers1=[b.INT],
    productions=[{"name": b.STRING, "id": b.INT}],
    bin3=b.DataFormat(8, bytes),
    buildings=[b.INT],
    building_groups=[b.INT],
    tiles_occupied=[b.INT],
    bin4=[b.DWORD, 4]
)

building_group_structure = dict(
    id=b.UINT,
    bin1=b.DataFormat(26, bytes),
    type=b.STRING
)

building_group2_structure = dict(
    numbers1=[b.INT],
    strings=[{"name": b.STRING, "id": b.INT}],
    bin2=b.DataFormat(8, bytes),
    buildings=[b.UINT],
    bin3=b.DataFormat(8, bytes)
)

building_structure = dict(
    id=b.UINT,
    type=b.STRING,
    bool1=b.BOOL,
    finished=b.BOOL  # Is the building actually finished, or just under construction?
)

building2_structure = dict(
    bin2=b.DataFormat(20, bytes)
)

unit_structure = dict(
    id=b.UINT,
    not_artefact=b.BOOL,  # I'm not 100% on this, but I've only seen it be 00 for Artefacts and 01 otherwise
    bin1=b.DataFormat(25, bytes),
    type=b.STRING,
    action_points=b.DOUBLE,  # Guess
    engaged=b.BOOL,  # Guess. Seems to relate to whether a unit is within 1 tile of an enemy
    experience=b.DOUBLE,
    health=b.DOUBLE,
    double3=b.DOUBLE,
    morale=b.DOUBLE,
    bin3=b.DataFormat(1, bytes),  # My guess is that this is whether or not a unit is able to make a melee attack
    movement_remaining=b.DOUBLE,
    veteran_title=b.STRING,
    bin4=b.DataFormat(4, bytes),
    level=b.INT,
    bin5=b.DataFormat(3, bytes)
)

unit2_structure = dict(
    actions=[b.INT],
    traits=[{"name": b.STRING, "id": b.INT}],
    bin6=b.DataFormat(16, bytes),
    int1=b.INT,
    bin7=b.DataFormat(4, bytes),
    numbers2=[b.INT],
    threat_tile=b.INT,  # Appears to correlate with the tile occupied by an enemy unit when units are in melee range?
    bin8=b.DataFormat(12, bytes),
    numbers3=[b.INT],
    numbers4=[b.INT],
    F=b.DWORD,
    numbers5=[b.INT],
    numbers6=[b.INT]
)

unit4_structure = dict(
    unknown=b.INT
)

weapon_structure = dict(
    id=b.UINT,
    bool1=b.BOOL,
    bool2=b.BOOL,
    int1=b.INT
)

weapon2_structure = dict(
    traits=[{"name": b.STRING, "id": b.INT}],
    F=b.DWORD,
    number=b.INT
)

# No analysis needed
magic_item_structure = dict(
    id=b.DataFormat(4, bytes),
    name=b.STRING
)

# Either the string "Factions/" (start of the next quest)
# OR four characters (the length marker INT) followed by 4+ letters followed by a null byte (start of the
# notifications section)
# This might fail if the Lord of Skulls quest is active
# ideally I would find a better way to get the right amount of data
# However, I don't need to worry too much - no quests are active at game start.
quest_re = rb'(Factions/|....[a-z,A-Z]{4,}\x00)'
quest_binary = b.DataFormat(re.compile(quest_re), bytes, inclusive=False)

quest_structure = dict(
    name=b.STRING,
    number=b.UINT,
    stage=b.UINT,
    bin1=quest_binary  # Variable length
)

# No analysis needed
notification_base_structure = dict(
    type=b.STRING,
    number=b.UINT,
    player=b.UINT,
    bin1=b.DataFormat(3, bytes)
)

# I *think* bin2 is the tile the notification is tied to.
# Again, this is of basically no importance because there are no notifications at game start.
notification_types = dict(
    CityGrown=dict(
        city=b.STRING,
        details=b.STRING,
        bin2=b.DataFormat(4, bytes)
    ),
    FactionDefeated=None,  # TODO: Make a save file after surrendering
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
    LordOfSkullsAppeared=None,  # I don't have this DLC and can't easily test
    LordOfSkullsDisppeared=None,
    PlayerLost=b.DataFormat(0, None),  # This is a no-op
    PlayerWon=None,  # I'm pretty sure PlayerWonElimination and PlayerWonQuest are used instead
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
    UnitTransformed=dict(
        started_as=b.STRING,
        unknown=b.DataFormat(4, bytes),
        bin2=b.DataFormat(4, bytes)
    ),
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

# Only relevant for parsing files with quest data in them
notification2_prefix_lengths = dict(
    CityGrown=7,
    FactionDefeated=None,
    FactionDiscovered=None,
    FeatureExplored=7,
    FeatureTypeDiscovered=7,
    LordOfSkullsAppeared=None,
    LordOfSkullsDisppeared=None,
    PlayerLost=None,
    PlayerWon=None,
    PlayerWonElimination=None,
    PlayerWonQuest=None,
    ProductionCompleted=7,
    QuestAdded=None,
    QuestCompleted=None,
    QuestUpdated=None,
    RegionDiscovered=None,
    ResearchCompleted=7,
    ResourcesGainedTile=15,
    ResourcesGainedUnit=15,
    TileAcquired=7,
    TileCaptured=15,
    TileCleared=7,
    UnitAttacked=31,
    UnitCaptured=11,
    UnitKilled=31,
    UnitGainedTrait=7,
    UnitTransformed=7,
    UnitTypeDiscovered=8,
    UnitUsedActionOn=11
)

master_structure = dict(
    world_params=world_params_structure,
    climates=[climate_structure, b.SCHAR],  # why is this a SCHAR when everything else is UINTs?
    events=[events_notimplemented_structure],
    actions=[action_structure],
    traits=[trait_structure],
    players=[player_structure],
    tiles=[tile_structure],
    features=[feature_structure],
    cities=[city_structure],
    building_groups=[building_group_structure],
    buildings=[building_structure],
    units=[unit_structure],
    weapons=[weapon_structure],
    magic_items=[magic_item_structure],
    quests=[quest_structure]
)

master2_structure = dict(
    traits=[b.DataFormat(8, bytes), None],
    players=[player2_structure, None],
    tiles=[tile2_structure, None],
    features=[feature2_structure, None],
    cities=[city2_structure, None],
    building_groups=[building_group2_structure, None],
    buildings=[b.DataFormat(20, bytes), None],
    units=[unit2_structure, None],
    weapons=[weapon2_structure, None],
    magic_items=[[b.INT], None]
)

suborder_structure = (b.INT, b.INT, b.INT, b.INT, b.INT)

order_structure = dict(
    action=b.INT,
    mystery=(b.INT, b.INT, b.INT, b.INT),
    suborders=[suborder_structure]
)
