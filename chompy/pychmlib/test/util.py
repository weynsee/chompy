import struct

def read_file(filename):
    f = open(filename, "rb")
    try:
        return f.read()
    finally:
        f.close()