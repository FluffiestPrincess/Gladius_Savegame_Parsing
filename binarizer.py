"""
Some utilities for reading mixed-format binary files.
"""

import struct
import mmap
import os
import re
import json
import io


def pretty_hex(b):
    return b.hex(" ").upper()


def pretty_binary(b):
    binary = [bin(char) for char in b]  # Convert bytes to strings representing binary
    binary = [string.replace("0b", "") for string in binary]  # Remove binary format specifier
    binary = ['{:0>8}'.format(string) for string in binary]  # Pad to 8 digits per block
    binary = " ".join(binary)
    return binary


def bytes_object_hook(d):
    """
    Used as object_hook in json.load to convert the pretty hex objects - like {"bytes": "12 20"} back into bytes.
    """
    if list(d.keys()) == ["bytes"]:
        return bytes.fromhex(d["bytes"])
    else:
        return d


class BytesJSONEncoder(json.JSONEncoder):
    """
    A JSON encoder that supports writing bytes object as strings like '10 00 DE AD BE EF', although wrapped in an
    object for easy decoding.
    """
    def default(self, o):
        return {"bytes": pretty_hex(o)}


class DataFormat(object):
    """
    A utility object for storing the values that BinReader look for when deciding how much data to read, and how to
    format it. Acts like an extremely budget iterable.
    """
    def __init__(self, until, from_bytes=None, to_bytes=None, allow_zero_length=True, inclusive=True):
        self.until = until
        self.from_bytes = from_bytes
        # allow_zero_length is no longer used but is retained for backwards-compatibility
        self.allow_zero_length = allow_zero_length
        self.inclusive = inclusive
        if to_bytes is None:
            self.to_bytes = from_bytes
        else:
            self.to_bytes = to_bytes

    def __iter__(self):
        # Needed to support func(*DataType)
        # Notably does NOT return to_bytes!
        return (self.until, self.from_bytes, self.allow_zero_length, self.inclusive).__iter__()

    def __repr__(self):
        return f"{__name__}.{type(self).__name__}(" \
               f"until={self.until.__repr__()}, " \
               f"from_bytes={self.from_bytes.__repr__()}, " \
               f"to_bytes={self.to_bytes.__repr__()}, " \
               f"allow_zero_length={self.allow_zero_length.__repr__()}, " \
               f"inclusive={self.inclusive.__repr__()})"


BYTE = DataFormat(1)
WORD = DataFormat(2)
DWORD = DataFormat(4)
QWORD = DataFormat(8)
CHAR = DataFormat(1, "c")
SCHAR = DataFormat(1, "b")
UCHAR = DataFormat(1, "B")
SHORT = DataFormat(2, "h")
USHORT = DataFormat(2, "H")
INT = DataFormat(4, "i")
UINT = DataFormat(4, "I")
LONG = DataFormat(4, "l")
ULONG = DataFormat(4, "L")
LLONG = DataFormat(8, "q")
ULLONG = DataFormat(8, "Q")
FLOAT = DataFormat(4, "f")
DOUBLE = DataFormat(8, "d")
BOOL = DataFormat(1, "?")
STRING = DataFormat(b"\x00", lambda x: x.decode(), lambda x: bytes(x, "UTF-8")+b'\x00')

# Non-zero-length string, used until I realized it was almost certainly an error.
# NZ_STRING = DataFormat(b"\x00", lambda x: x.decode(), lambda x: bytes(x, "UTF-8")+b'\x00' allow_zero_length=False)


def format_output(output, form):
    """
    Used by BinReader to convert binary data into other types of object.
    :param output: The data to format.
    :param form: How to format it.
        If a string, passes to struct.unpack.
        If a function, calls the function on the result before returning it.
        If None, does nothing and just returns the result as-is.
    :return:
    """
    if form is None:
        return output
    elif callable(form):
        return form(output)
    elif isinstance(form, str):
        return struct.unpack(form, output)[0]
    else:
        raise TypeError("Currently only supports formatting outputs with callable functions or with a string that "
                        "is passed as a pattern to struct.unpack.")


class BinReader(mmap.mmap):

    def read(self, n=None):
        to_return = mmap.mmap.read(self, n)
        if n is not None and len(to_return) < n:
            raise EOFError("End of memory-mapped section reached.")
        return to_return

    def read_until(self, sub):
        """
        Read everything up until the chosen subunit of bytes is found, (not including the subunit itself), then
        advances the pointer to *after* the subunit.
        :param sub: Subunit to read until.
        :return: bytes
        """
        loc = self.find(sub)
        if loc == -1:
            print(f"WARNING: desired bytes unit {sub.__repr__()} not found, returning entire rest of data.")
            loc = loc - self.tell()
            front = self.read(loc)
            self.seek(len(self))
            return front
        else:
            loc = loc - self.tell()
            front = self.read(loc)
            # Advance the pointer past the separator substring
            self.seek(len(sub), os.SEEK_CUR)
            return front

    def read_until_re(self, pattern, inclusive=False):
        match = pattern.search(self, pos=self.tell())
        if match is None:
            raise RuntimeError(f"Could not find requested pattern {pattern.pattern} in data.")
        elif inclusive:
            return self.read(match.end() - match.pos)
        else:
            return self.read(match.start() - match.pos)

    def fpop(self, until, form=None, allow_zero_length=True, inclusive=False):
        """
        Get a value of the specified type from the current pointer position onwards, advancing the pointer in the
        process.
        :param until:
            If an integer, returns that many bytes of data.
            If a bytes object, returns everything up to the first occurence of that sequence of bytes.
            If a regular expression compiled pattern, returns everything up to the first occurence of that pattern.
            If a DataType, uses the splitby and form values from that DataType.
        :param form:
            If a string, passes to struct.unpack.
            If a function, calls the function on the result before returning it.
            If None, does nothing and just returns the result as-is.
            Note: If splitby is a DataType, form is ignored.
        :param allow_zero_length: If true, can return a zero-lenth result. If false, will respond to a zero-length
        result by silently skipping forward the length of the separator and trying again. Currently only used for
        matching by bytes objects.
        :param inclusive: Whether or not to return the contents of the regular expression match. Currently only used
        for matching by regular expression.
        """
        if isinstance(until, bytes):
            # Split by separator
            front = self.read_until(until)
            if len(front) == 0 and not allow_zero_length:
                # Keep trying
                front = self.fpop(until, None, False)
        elif isinstance(until, int):
            # Split by length
            front = self.read(until)
        elif isinstance(until, re.Pattern):
            # Split by regular expression
            front = self.read_until_re(until, inclusive)
        elif isinstance(until, DataFormat):
            front = self.fpop(*until)
            form = None  # To avoid formatting the output twice
        else:
            raise TypeError("Currently only supports splitting by 'bytes', 'int', and 're.Pattern' objects.")
        return format_output(front, form)

    def get(self, until, form=None, allow_zero_length=False):
        """
        Get the next value *without* changing the contents of the binary data.
        :param until:
            If an integer, returns that many bytes of data.
            If a bytes object, returns everything up to the first occurence of that sequence of bytes.
        :param form:
            If a string, passes to struct.unpack.
            If a function, calls the function on the result before returning it.
            If None, does nothing and just returns the result as-is.
        :param allow_zero_length: If true, can return a zero-lenth result. If false, will respond to a zero-length
        result by silently skipping forward the length of the separator and trying again.
        """
        position_before_get = self.tell()
        output = self.fpop(until, form, allow_zero_length)
        self.seek(position_before_get)
        return output

    def fpop_structure(self, structure):
        """
        :param structure: Examples:
            [STRING, 10]: The data contains a sequence of ten null-terminated strings, which will be returned in a list.
            [STRING, UINT]: The data contains a sequence of null-terminated strings, preceded by a UINT length marker
            specifying how many strings there are. This will be returned as a list of strings.
            [STRING, ULONG]: As above, but with a ULONG rather than a UINT. Any numeric DataType can be specified.
            [STRING]: A shortened form of [STRING, UINT], provided because most length indicators are UINTs.
            [(STRING, FLOAT), 10]: The data contains ten blocks, each of which is a null-terminated string followed by a
            FLOAT. This will be returned as a list of 2-tuples.
            [{"name": STRING, "price": FLOAT}, 10]: As above, but instead of a list of tuples, the return value
            will be a list of dictionaries each with keys "name" and "price".
            [[STRING], 10]: The data contains a sequence of ten blocks, each of which is a sequence of strings
            preceded by a UINT length indicator

        :return: Varies depending on structure.
        """
        # Maybe I should implement this as a generator
        if isinstance(structure, DataFormat):
            # structure specifies the length and format of data
            return self.fpop(*structure)
        elif isinstance(structure, list):
            substructure = structure[0]
            if len(structure) == 1:
                # Shorthand for [substructure, UINT]
                length = self.fpop(UINT)
            elif isinstance(structure[1], int):
                # A fixed-length list
                length = structure[1]
            elif isinstance(structure[1], DataFormat):
                # A list prefixed with the length of the list
                length = self.fpop(*structure[1])
            else:
                raise TypeError(f"Second element in list must by int or DataFormat, not {type(structure[1])}")
            return [self.fpop_structure(substructure) for _ in range(length)]
        elif isinstance(structure, dict):
            # Just a sequence of other objects, but this time we have labels for them
            return {name: self.fpop_structure(structure[name]) for name in structure}
        else:
            # Anything else is probably an iterable.
            return [self.fpop_structure(substructure) for substructure in structure]


class BinWriter(io.BufferedWriter):

    def translate(self, data, translator):
        if callable(translator):
            self.write(translator(data))
        elif isinstance(translator, str):
            self.write(struct.pack(translator, data))
        elif isinstance(translator, DataFormat):
            # Unpack and recurse
            self.translate(data, translator.to_bytes)
        elif translator is None:
            self.write(data)
        else:
            raise TypeError("Currently only supports formatting inputs with callable functions or with a string that "
                            "is passed as a pattern to struct.pack.")

    def write_structure(self, data_structure, spec_structure):
        if isinstance(spec_structure, DataFormat):
            self.translate(data_structure, spec_structure)

        # elif callable(spec_structure):
        #     self.write_structure(data_structure, spec_structure(data_structure, self))

        elif isinstance(spec_structure, list) and len(spec_structure) == 1:
            # This is just shorthand for [substructure, UINT]
            self.write_structure(data_structure, [spec_structure[0], UINT])

        elif isinstance(spec_structure, list) and len(spec_structure) == 2:
            if isinstance(spec_structure[1], int) or spec_structure[1] is None:
                # Fixed length implies no length indicator
                pass
            elif isinstance(spec_structure[1], DataFormat):
                # Write a length indicator, then the list
                self.translate(len(data_structure), spec_structure[1])
            else:
                raise TypeError(f"Second element in list must by int, DataFormat, or None, not "
                                f"{type(spec_structure[1])}")

            for data_instance in data_structure:
                self.write_structure(data_instance, spec_structure[0])

        elif isinstance(spec_structure, list):
            raise ValueError("Length of list must be 1 or 2.")

        elif isinstance(spec_structure, tuple):
            for data_instance, spec_instance in zip(data_structure, spec_structure):
                self.write_structure(data_instance, spec_instance)

        elif isinstance(spec_structure, dict):
            for data_instance, spec_instance in zip(data_structure.values(), spec_structure.values()):
                self.write_structure(data_instance, spec_instance)

        else:
            raise TypeError(f"write_structure does not know how to handle {type(spec_structure)}")
