import os

def is_within_directory(path: str, cwd: str) -> bool:
    abs_cwd = os.path.abspath(cwd)
    abs_path = os.path.abspath(os.path.join(abs_cwd, path))

    # Normalize paths to eliminate ../ and similar constructs
    norm_cwd = os.path.normpath(abs_cwd)
    norm_path = os.path.normpath(abs_path)

    return os.path.commonpath([norm_path, norm_cwd]) == norm_cwd
