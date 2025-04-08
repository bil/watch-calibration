import os

def make_abs_path(working_dir, path):
    if os.path.isabs(path):
        return path
    else:
        return os.path.join(working_dir, path)
