import os

def make_abs_path(working_dir, path):
    """Ensure path is absolute. Relative paths joined to working_dir."""

    if os.path.isabs(path):
        return path
    else:
        return os.path.join(working_dir, path)
