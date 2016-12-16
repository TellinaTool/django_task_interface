"""
Contains functions to manipulate JSON-represented filesystems.

Given the following directory:

dir1/
    file1
    file2
    dir2/
        dir3/
            file3

Its JSON representation is:

{
    "dir1": {
        "dir2": {
            "dir3": {
                "file3": null
            }
        },
        "file1": null,
        "file2": null
    }
}
"""

import pathlib
import json
import shutil

USER = 'vagrant'
GROUP = 'vagrant'

def merge_dictionaries(a: dict, b: dict) -> dict:
    """Merges the entries of 2 dictionaries."""
    return {**a, **b}

def disk_2_dict(path: pathlib.Path) -> dict:
    """
    Returns:
        JSON representation of the directory named by path
    """
    if path.is_dir():
        subtrees = {}
        for subpath in path.iterdir():
            subtrees = merge_dictionaries(subtrees, disk_2_dict(subpath))
        return {path.parts[-1]: subtrees}
    else:
        return {path.parts[-1]: None}

def dict_2_disk(tree: dict, root_path: pathlib.Path):
    """Writes the directory described by tree to root_path."""
    for name, subtree in tree.items():
        path = root_path / name
        if subtree is None:
            # file
            newfile = path.open(mode='w+')
            newfile.close()
            shutil.chown(path.as_posix(), user=USER, group=GROUP)
        else:
            # directory
            path.mkdir()
            shutil.chown(path.as_posix(), user=USER, group=GROUP)
            dict_2_disk(subtree, root_path / name)
