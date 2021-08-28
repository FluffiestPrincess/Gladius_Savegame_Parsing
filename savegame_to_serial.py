import argparse
import os
import sys
import configparser
import zlib
from mmap import ACCESS_READ
from bulk_reader_tools import header_structure
import binarizer as b

testing = True
master_config_name = "Config.ini"
test_file_name = r"C:\Users\rosa\Documents\Proxy Studios\Gladius\SavedGames\SinglePlayer\Enslavers.GladiusSave"

config = configparser.ConfigParser(allow_no_value=True)
# Default behaviour is to make all config option names lowercase
# We don't want to do that so we override optionxform
config.optionxform = lambda option: option
config.read(master_config_name)

unpack_dir_name = config["GLADIUS"]["unpacked directory"]

if testing:
    file_in_name = test_file_name
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
config_output_path = os.path.join(directory, name + ".ini")
binary_output_path = os.path.join(directory, name + ".bin")

config_out = configparser.ConfigParser(allow_no_value=True)

# Default behaviour is to make all config option names lowercase
# We don't want to do that so we override optionxform
config_out.optionxform = lambda option: option
config_out.add_section("HEADER")
config_out.add_section("MODS")
header = config_out["HEADER"]

with open(file_in_name, 'r+b') as file:
    data = b.BinReader(file.fileno(), 0, access=ACCESS_READ)

for name in header_structure:
    value = data.fpop(*header_structure[name])
    header[name] = str(value)

# Mod names are separated by null bytes
for n in range(int(header["mod_count"])):
    mod = data.fpop(*b.STRING)
    # noinspection PyTypeChecker
    config_out["MODS"][mod] = None

with open(config_output_path, 'w') as file:
    config_out.write(file)

# Remainder of file is compressed with zlib
remainder = len(data) - data.tell()
decompressed_data = zlib.decompress(data.get(remainder))

with open(binary_output_path, 'wb') as file:
    file.write(decompressed_data)
    print(f"Decompressed savegame data written to {unpack_dir_name}.")

data.close()
