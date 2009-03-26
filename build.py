import os
import shutil

def will_be_ignored(name):
    return name.startswith("test") or name.endswith(".pyc")

def copy_tree(src, dst):
    names = os.listdir(src)
    os.makedirs(dst)
    errors = []
    for name in names:
        if will_be_ignored(name):
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if os.path.isdir(srcname):
            copy_tree(srcname, dstname)
        else:
            shutil.copy2(srcname, dstname)

if os.path.exists("dist"):
    shutil.rmtree("dist", ignore_errors=False)

copy_tree("chompy","dist/chompy")