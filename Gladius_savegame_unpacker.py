import argparse
import os
import sys
import configparser
import zlib
from mmap import ACCESS_READ
import binarizer as b

testing = False
unpack_dir_name = "unpacked saves"

header_structure = dict(version=b.STRING,
                        branch=b.STRING,
                        revision=b.STRING,
                        build=b.STRING,
                        steamuser=b.STRING,
                        turn=b.INT,
                        checksum=b.INT,
                        mod_count=b.INT)

if testing:
    file_in_name = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\test.GladiusSave"
else:
    parser = argparse.ArgumentParser(description="Decompress Gladius saved games.")
    parser.add_argument("filename")
    args = parser.parse_args()
    file_in_name = os.path.abspath(args.filename)

if not file_in_name.lower().endswith(".gladiussave"):
    print("File name must end with .GladiusSave")
    input("Press enter.")
    sys.exit(1)

directory, name = os.path.split(file_in_name)
directory = os.path.join(directory, unpack_dir_name)
name = os.path.splitext(name)[0]
if os.path.isfile(directory):
    raise OSError(f"Path {directory} already exists and is a file.")
elif os.path.isdir(directory):
    pass
else:
    os.mkdir(directory)
config_out_name = os.path.join(directory, name + ".cfg")
bulk_out_name = os.path.join(directory, name + ".bulk")

config = configparser.ConfigParser(allow_no_value=True)

# Default behaviour is to make all config option names lowercase
# We don't want to do that so we override optionxform
config.optionxform = lambda option: option
config.add_section("HEADER")
config.add_section("MODS")
header = config["HEADER"]

with open(file_in_name, 'r+b') as file:
    data = b.BinReader(file.fileno(), 0, access=ACCESS_READ)

for name in header_structure:
    value = data.fpop(*header_structure[name])
    header[name] = str(value)

# Mod names are separated by null bytes
for n in range(int(header["mod_count"])):
    mod = data.fpop(*b.STRING)
    config["MODS"][mod] = None

with open(config_out_name, 'w') as file:
    config.write(file)

# Remainder of file is compressed with zlib
remainder = len(data) - data.tell()
decompressed_data = zlib.decompress(data.get(remainder))

with open(bulk_out_name, 'wb') as file:
    file.write(decompressed_data)

data.close()
