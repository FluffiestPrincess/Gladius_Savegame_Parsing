import argparse
import os.path
import sys
import configparser
import struct
import zlib

parser = argparse.ArgumentParser(description="Compress extracted files back into a playable Gladius saved game.")
parser.add_argument("filename")
args = parser.parse_args()

file_in_name = os.path.abspath(args.filename)

if file_in_name.lower().endswith(".cfg"):
    pass
elif file_in_name.lower().endswith(".bulk"):
    pass
else:
    print("File name must end with .cfg or .bulk")
    input("Press enter.")
    sys.exit(1)

config_in_name = os.path.splitext(file_in_name)[0] + ".cfg"
bulk_in_name = os.path.splitext(file_in_name)[0] + ".bulk"
save_out_name = os.path.splitext(file_in_name)[0] + ".GladiusSave"

config = configparser.ConfigParser(allow_no_value=True)

# Default behaviour is to make all config option names lowercase
# We don't want to do that so we override optionxform
config.optionxform = lambda option: option
config.read(config_in_name)
header = config["HEADER"]

with open(bulk_in_name, 'rb') as file:
    bulk_data = file.read()

compressed_data = zlib.compress(bulk_data)

# Null byte used as a separator
nul = b"\x00"

mods = [bytes(s, encoding="utf-8") for s in config["MODS"]]
mods = nul.join(mods)

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
                len(config["MODS"])),     # Note: Use the *actual* number of mods, not whatever the config file says
    mods,
    nul,
    compressed_data])

with open(save_out_name, 'wb') as file:
    file.write(data)
