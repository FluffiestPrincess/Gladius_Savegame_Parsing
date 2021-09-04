from bulk_reader_tools import *

testing = True

# Used for testing
input_path = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\unpacked saves" \
             r"\Enslavers.json"
output_path = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\unpacked saves" \
             r"\Enslavers modified.json"


class GladiusSave(object):

    def __init__(self, data):
        self.data = data

    def get(self, type_, id_):
        if self.data[type_][id_][0]["id"] == id_:
            return self.data[type_][id_]
        else:
            gen = (x for x in self.data[type_] if x[0]["id"] == id_)
            return next(gen)

    def delete_action(self, action_id):
        try:
            action = self.get("actions", action_id)
        except StopIteration:
            return
        except IndexError:
            return
        linked_traits = action[1]["linked_traits"].copy()
        self.data["actions"].remove(action)
        for trait_id in linked_traits:
            self.delete_trait(trait_id)

    def delete_trait(self, trait_id):
        try:
            trait = self.get("traits", trait_id)
        except StopIteration:
            return
        except IndexError:
            return
        linked_action_id = trait[1]["linked_action"]
        self.data["traits"].remove(trait)
        self.delete_trait(linked_action_id)

    def delete_player(self, player_id):
        player = self.get("players", player_id)

    def delete_feature(self, feature_id):
        try:
            feature = self.get("features", feature_id)
        except StopIteration:
            return
        except IndexError:
            return
        for trait_id in feature[1]["traits"]:
            self.delete_trait(trait_id)
        self.data["features"].remove(feature)

    def delete_unit(self, unit_id, via_transport=False):
        # via_transport: This unit deletion is occuring as a result of the parent transport being deleted,
        # so there is no need to also delete the unit from the parent transport's list.
        try:
            unit = self.get("units", unit_id)
        except StopIteration:
            return
        except IndexError:
            return
        for action_id in unit[1]["actions"]:
            self.delete_action(action_id)
        for trait_id in (dict_["id"] for dict_ in unit[1]["traits"]):
            self.delete_trait(trait_id)
        for weapon_id in unit[1]["weapons"]:
            self.delete_weapon(weapon_id)

        if unit[1]["transport"] != -1 and not via_transport:
            # If this unit is in a transport, remove it from the transport.
            # The via_transport parameter skips this bit to avoid altering a list while iterating over it
            transport = self.get("units", unit[1]["transport"])
            transport[1]["transported_units"].remove(unit_id)

        for subunit_id in unit[1]["transported_units"]:
            # Delete everything this unit is transporting
            self.delete_unit(subunit_id, via_transport=True)



    def delete_weapon(self, weapon_id):
        try:
            weapon = self.get("weapons", weapon_id)
        except StopIteration:
            return
        except IndexError:
            return
        for trait_id in (dict_["id"] for dict_ in weapon[1]["traits"]):
            self.delete_trait(trait_id)
        self.data["weapons"].remove(weapon)

    def delete_magic_item(self, magic_item_id):
        try:
            magic_item = self.get("magic_items", magic_item_id)
        except StopIteration:
            return
        except IndexError:
            return
        for action_id in magic_item[1]["actions"]:
            self.delete_action(action_id)
        self.data["magic_items"].remove(magic_item)

    def change_player_faction(self, player_id, new_faction):
        pass

    def delete_player_nonfaction_units(self, player_id):
        pass

    def flood_terrain(self, new_terrain_type=None, new_terrain_height=None):
        """
        Flood-fills the entire map with a chosen terrain type and height.
        :param new_terrain_type: The terrain type to use. Set to None to leave existing features in place.
        :param new_terrain_height: The height. Set to None to leave existing heights in place.
        :return:
        """

        if new_terrain_type is not None:
            [self.delete_feature(feature[0]["id"]) for feature in self.data["features"]]

            self.data["features"] = [
                [
                    {
                        "id": tile[0]["id"],
                        "bin1": b"\x01",
                        "duration": 0.0,
                        "cooldown": 0.0,
                        "visited": False,
                        "bool1": False,
                        "feature": new_terrain_type
                    },
                    {
                        "traits": [],
                        "owner": 4,
                        "tile_id": tile[0]["id"]
                    }
                ]
                for tile in self.data["tiles"]]

        if new_terrain_height is not None:
            for tile in self.data["tiles"]:
                tile[0]["height"] = new_terrain_height

    def reset_to_start(self):
        # Set turn number to 0

        # Delete economy_score, military_score, research_score, damage_dealt_cumulative, damage_taken_cumulative,
        # resources_cumulative, units_created_cumulative, units_killed_cumulative, units_lost_cumulative, features_seen,
        # units_seen, research_unk1, research_unk2, research_underway, quests_in_progress, quests_completed,
        # known_enemy_factions, regions_discovered from each player

        # Reset player resources to starting values

        # Un-aggro all neutral units

        self.clear_quests()
        self.clear_notifications()
        pass

    def clear_notifications(self):
        self.data["notifications"] = [[], [], [], [], []]

    def clear_quests(self):
        self.data["quests"] = [[], []]

    def clear_climates(self):
        self.data["climates"] = [[]]

    def reveal_map(self, player_id):
        player = self.get("players", player_id)
        player[1]["tiles_revealed"] = [tile[0]["id"] for tile in self.data["tiles"]]

    def hide_map(self, player_id):
        player = self.get("players", player_id)
        player[1]["tiles_revealed"] = player[1]["tiles_watched"]


if testing:
    import json
    with open(input_path, "r") as file:
        gs = GladiusSave(json.load(file, object_hook=b.bytes_object_hook))

    def save(gs):
        with open(output_path, "w") as file:
            json.dump(gs.data, file, cls=b.BytesJSONEncoder, indent="    ")
