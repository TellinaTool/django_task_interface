"""
File system serialization and deserialization.

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
                "file": {
                    "ATTR_size": xx,
                    "ATTR_mode": xx,
                    "ATTR_user": xx,
                    ...
                }
            }
        },
        "file1": {
            "ATTR_size": xx,
            "ATTR_mode": xx,
            "ATTR_user": xx,
            ...
        }
        "file2": {
            "ATTR_size": xx,
            "ATTR_mode": xx,
            "ATTR_user": xx,
            ...
        }
    }
}
"""

import pathlib
import os, pwd, grp, shutil

# file attributes
_NAME = 0
_USER = 1
_GROUP = 2
_SIZE = 3
_MODE = 4
_ATIME = 5
_CTIME = 6
_MTIME = 7
_CONTENT = 8


class File(object):
    def __init__(self, name, user=None, group=None, size=None, mode=None,
                 atime=None, ctime=None, mtime=None, content=None):
        # None-value attributes are ignored in a specific task.
        self.name = name
        self.user = user
        self.group = group
        self.size = size
        self.mode = mode
        self.atime = atime
        self.ctime = ctime
        self.mtime = mtime
        self.content = content

    def to_dict(self):
        # A throughput-saving file object serialization method
        # None-value attributes are excluded from the serialization and are not
        # passed around the network
        d = {}
        for attr in self.__dict__:
            if self.__dict__[attr] is not None:
                d[attr] = self.__dict__['ATTR_' + attr]
        return d


def merge_dictionaries(a: dict, b: dict) -> dict:
    """Merges the entries of 2 dictionaries."""
    return {**a, **b}


def attr_format(s):
    """Add attribute name prefix to the filesystem JSON."""
    attr_prefix = 'ATTR_'
    return attr_prefix + s


def disk_2_dict(path: pathlib.Path, attrs=[_NAME]) -> dict:
    """
    :param path: location of directory
    :param attrs: list of relevant file attributes

    Returns:
        JSON representation of the directory named by path
    """
    if path.is_dir():
        subtrees = {}
        for subpath in path.iterdir():
            subtrees = merge_dictionaries(subtrees,
                                          disk_2_dict(subpath, attrs))
        return {path.parts[-1]: subtrees}
    else:
        # serialize file
        d = {}
        file_stat = None
        if len(attrs) > 1:
            file_stat = os.stat(path.as_posix())
        for attr in attrs:
            if attr == _NAME:
                d[attr_format('name')] = path.parts[-1]
            if attr == _USER:
                d[attr_format('user')] = pwd.getpwuid(file_stat.st_uid).pw_name
            if attr == _GROUP:
                d[attr_format('group')] = grp.getgrgid(file_stat.st_gid).gr_name
            if attr == _SIZE:
                d[attr_format('size')] = file_stat.st_size
            if attr == _MODE:
                d[attr_format('mode')] = file_stat.st_mode
            if attr == _ATIME:
                d[attr_format('atime')] = file_stat.st_atime
            if attr == _MTIME:
                d[attr_format('mtime')] = file_stat.st_mtime
            if attr == _CTIME:
                d[attr_format('ctime')] = file_stat.st_ctime
            if attr == _CONTENT:
                with open(path.as_posix(), encoding='utf-8',
                          errors='ignore') as f:
                    d[attr_format('content')] = f.read()
        return {path.parts[-1]: d}


def dict_2_disk(tree: dict, root_path: pathlib.Path):
    """Writes the directory described by tree to root_path."""
    for name, subtree in tree.items():
        path = root_path / name
        if subtree.keys()[0].startswith(attr_format("")):
            # file
            if attr_format('size') in subtree:
                # 'size' is the only attribute we consider that have something
                # to do with file content
                size = subtree[attr_format('size')]
                if not size.isdigit():
                    unit = size[-1] if size[-2].isdigit() else size[-2:]
                    if unit in ['b', 'B']:
                        size = int(filter(str.isdigit, size))
                    elif unit in ['k', 'K', 'kb', 'kB', 'Kb', 'KB']:
                        size = int(filter(str.isdigit, size)) * 1024
                    elif unit in ['m', 'M', 'mb', 'mB', 'Mb', 'MB']:
                        size = int(filter(str.isdigit, size)) * pow(1024, 2)
                    elif unit in ['g', 'G', 'gb', 'gB', 'Gb', 'GB']:
                        size = int(filter(str.isdigit, size)) * pow(1024, 3)
                    elif unit in ['t', 'T', 'tb', 'tB', 'Tb', 'TB']:
                        size = int(filter(str.isdigit, size)) * pow(1024, 4)
                    else:
                        raise NotImplementedError
                newfile = create_file_by_size(path.as_posix(), size)
            else:
                newfile = path.open(mode='w+')
                newfile.close()
            if attr_format('user') in subtree:
                shutil.chown(path.as_posix(), user=subtree[attr_format('user')])
            if attr_format('group') in subtree:
                shutil.chown(path.as_posix(), group=subtree[attr_format('group')])
            if attr_format('mode') in subtree:
                os.chmod(path.as_posix(), mode=subtree[attr_format('mode')])
            if attr_format('atime') in subtree and attr_format('mtime') in subtree:
                os.utime(path.as_posix(),
                         (subtree[attr_format('atime')], subtree[attr_format('mtime')]))
            else:
                if attr_format('atime') in subtree:
                    os.utime(path.as_posix(),
                         (subtree[attr_format('atime')], subtree[attr_format('atime')]))
                if attr_format('mtime') in subtree:
                    os.utime(path.as_posix(),
                         (subtree[attr_format('mtime')], subtree[attr_format('mtime')]))
            if attr_format('ctime') in subtree:
                raise NotImplementedError
            if attr_format('content') in subtree:
                with path.open(mode='w+') as o_f:
                    o_f.write(subtree[attr_format('content')])
        else:
            # directory
            path.mkdir()
            shutil.chown(path.as_posix(), user=USER, group=GROUP)
            dict_2_disk(subtree, root_path / name)


def create_file_by_size(path, size):
    """Create a file with a particular byte length."""
    with open(path, 'wb') as o_f:
        o_f.truncate(size)