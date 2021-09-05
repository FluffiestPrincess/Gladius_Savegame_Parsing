import argparse
import os.path
import configparser
import struct
import zlib

testing = False
master_config_name = "Config.ini"

# Used for testing only
test_file_name = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\unpacked saves" \
                 r"\Enslavers_2.bin"

# Configuration file currently not used
# config = configparser.ConfigParser(allow_no_value=True)
# Default behaviour is to make all config option names lowercase
# We don't want to do that so we override optionxform
# config.optionxform = lambda option: option
# config.read(master_config_name)


if testing:
    file_in_name = test_file_name
else:
    parser = argparse.ArgumentParser(description="Compress extracted files back into a playable Gladius saved game.")
    parser.add_argument("filename")
    args = parser.parse_args()
    file_in_name = os.path.abspath(args.filename)

config_in_name = os.path.splitext(file_in_name)[0] + ".ini"
save_out_name = os.path.splitext(file_in_name)[0] + ".GladiusSave"

config_in = configparser.ConfigParser(allow_no_value=True)

# Default behaviour is to make all config option names lowercase
# We don't want to do that so we override optionxform
config_in.optionxform = lambda option: option
config_in.read(config_in_name)
header = config_in["HEADER"]

with open(file_in_name, 'rb') as file:
    binary_data = file.read()

# Null byte used as a separator
nul = b"\x00"

mods = [bytes(s, encoding="utf-8") for s in config_in["MODS"]]

data = b''.join([
    bytes(header["version"], encoding="utf-8"),
    nul,
    bytes(header["branch"], encoding="utf-8"),
    nul,
    bytes(header["revision"], encoding="utf-8"),
    nul,
    bytes(header["build"], encoding="utf-8"),
    nul,
    bytes(header["steamuser"], encoding="utf-8"),
    nul,
    struct.pack('<iii',
                int(header["turn"]),
                int(header["checksum"]),  # Not actually used so don't sweat it
                len(mods)),     # Note: Use the *actual* number of mods, not whatever the config file says
    nul.join(mods),
    nul,
    zlib.compress(binary_data)])

with open(save_out_name, 'wb') as file:
    file.write(data)
