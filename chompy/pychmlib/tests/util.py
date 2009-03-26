import struct
import os
import sys

def read_file(filename):
    f = open(filename, "rb")
    try:
        return f.read()
    finally:
        f.close()
        
def load_modules():
    parpath = os.path.join(os.path.dirname(sys.argv[0]), os.pardir)
    sys.path.insert(0, os.path.abspath(parpath))
    
def get_filename(filename):
    return os.path.join(os.path.dirname(sys.argv[0]), filename)