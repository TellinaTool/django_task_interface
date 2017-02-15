"""
File system serialization and deserialization.

TODO: handle links in a file system properly.

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

The 'filesystem_diff' function returns an annotated JSON representation which
contains one extra "tag" field for each entry. The tag field is a dictionary
with error types as the key and count as the value.

An example tag field is

    "tag": {"ch_missing": 1, "ch_extra": 2, "ch_incorrect": 4}

which indicates that one child of the directory node is missing, two are extra
and four are incorrect.

    tag field: # (1) missing: a file/dir is in the target FS but not in the current FS
               # (2) extra: a file/dir is in current FS but not in target FS
               # (3) incorrect: a file/dir is in current FS but has the wrong attribute
               # (4) ch_tag (directory only): errors in the children of a directory
               # (5) (file attributes only): a file in current FS
                    exists in the target FS, but the attribute value is incorrect,
                    in this case the correct attribute value is added as a suffix
                    to the current value
               # (6) to_select (filesearch tasks only): a node should be selected in the
                    target
               # (7) selected (filesearch tasks only): correctness of a node selection
                    operation, which takes the following three values:
                    -1: a node is in the target but was not selected by the last 
                        executed command
                    0: a node is corrected selected
                    1: a node is not in the target but was selected by the last 
                        executed command
"""

import collections
import datetime
import json
import pathlib
import re
import copy, os, pwd, grp, shutil

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

ERROR_TAGS = ['extra', 'missing', 'incorrect', 'stdout_missing',
              'stdout_extra', 'ch_extra', 'ch_missing', 'ch_incorrect']

directories_in_sample_filesystems = ['backup', 'content', 'css', 'js', 'lib',
    'partials', 'assignments', 'labs', 'lessons', 'review', 'bootstrap3',
    'fonts', 'angular', 'jquery', 'showdown', 'underscore']


class Node(object):
    """
    A node in the filesystem representation. Can be a regular file or a
    directory.

    :member name: The name of the node.
    :member type: The type of the node.
    """
    def __init__(self, name, type):
        self.name = name
        self.type = type

class Directory(Node):
    def __init__(self, name):
        super(Directory, self).__init__(name, 'directory')
        self.children = []

    def to_dict(self):
        children_dict_list = [child.to_dict() for child in
                              sorted(self.children, key=lambda x:x.name)]
        return {
            'name': self.name,
            'type': self.type,
            'children': children_dict_list
        }

class File(Node):
    def __init__(self, name, user=None, group=None, size=None, mode=None,
                 atime=None, ctime=None, mtime=None, content=None):
        super(File, self).__init__(name, 'file')
        # None-value attributes are ignored in a specific task.
        self.attributes = FileAttributes(
            user = user,
            group = group,
            size = size,
            mode = mode,
            atime = atime,
            ctime = ctime,
            mtime = mtime,
            content = content
        )

    def to_dict(self):
        return {
            'name': self.name,
            'type': self.type,
            'attributes': self.attributes.to_dict()
        }

class FileAttributes(object):
    def __init__(self, user=None, group=None, size=None, mode=None,
                 atime=None, ctime=None, mtime=None, content=None):
        self.user = user
        self.group = group
        self.size = size
        self.mode = mode
        self.atime = atime
        self.ctime = ctime
        self.mtime = mtime
        self.content = content

    def to_dict(self):
        # None-value attributes are excluded from the serialization
        d = {}
        for attr in self.__dict__:
            if self.__dict__[attr] is not None:
                d[attr] = str(self.__dict__[attr])
        return d

# --- Read a filesystem to/from the disk --- #

def disk_2_dict(path: pathlib.Path, attrs=[_NAME]) -> dict:
    """
    :param path: location of directory
    :param attrs: list of relevant file attributes

    Returns:
        JSON representation of the directory named by path
    """
    if not path.exists():
        return None

    def create_filesystem(path: pathlib.Path, attrs=[_NAME]) -> Node:
        if path.is_dir():
            node = Directory(path.name)
            for subpath in path.iterdir():
                subtree = create_filesystem(subpath, attrs=attrs)
                node.children.append(subtree)
        else:
            node = File(path.name)
            if len(attrs) > 0:
                file_stat = os.stat(path.as_posix())
            for attr in attrs:
                if attr == _USER:
                    # node.attributes.user = pwd.getpwuid(file_stat.st_uid).pw_name
                    node.attributes.user = 'me'
                if attr == _GROUP:
                    node.attributes.group = grp.getgrgid(file_stat.st_gid).gr_name
                if attr == _SIZE:
                    node.attributes.size = file_stat.st_size
                if attr == _MODE:
                    node.attributes.mode = file_stat.st_mode
                if attr == _ATIME:
                    node.attributes.atime = datetime.date.\
                        fromtimestamp(file_stat.st_atime)
                if attr == _MTIME:
                    node.attributes.mtime = datetime.date.\
                        fromtimestamp(file_stat.st_mtime)
                if attr == _CTIME:
                    node.attributes.ctime = datetime.date.\
                        fromtimestamp(file_stat.st_ctime)
                if attr == _CONTENT:
                    with open(path.as_posix(), encoding='utf-8',
                              errors='ignore') as f:
                        node.attributes.content = f.read()
        return node

    fs = create_filesystem(path, attrs)
    fs_dict = fs.to_dict()

    filesystem_sort(fs_dict)

    return fs_dict


def dict_2_disk(tree: dict, root_path: pathlib.Path, is_root_dir=False):
    """Writes the directory described by tree to root_path."""
    # check if path exists
    if not root_path.exists():
        return 'ROOT_PATH_DOES_NOT_EXIST'

    if not tree:
        return "FILE_SYSTEM_IS_EMPTY"

    path = root_path / tree['name'] if not is_root_dir else root_path

    if tree['type'] == 'file':
        attrs = tree['attributes'] if 'attributes' in tree else []
        if 'size' in attrs:
            # 'size' is the only attribute we consider that have something
            # to do with file content (besides file content itself)
            size = tree['attributes']['size']
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
            else:
                size = int(size)
            create_file_by_size(path.as_posix(), size)
        else:
            try:
                newfile = path.open(mode='w+')
                newfile.close()
            except Exception as err:
                return str(err)
        if 'user' in attrs:
            shutil.chown(path.as_posix(), user=attrs['user'])
        if 'group' in attrs:
            shutil.chown(path.as_posix(), group=attrs['group'])
        if 'mode' in attrs:
            os.chmod(path.as_posix(), mode=attrs['mode'])
        if 'atime' in attrs and 'mtime' in attrs:
            os.utime(path.as_posix(), (attrs['atime'], attrs['mtime']))
        else:
            if 'atime' in attrs:
                os.utime(path.as_posix(), (attrs['atime'], attrs['atime']))
            if 'mtime' in attrs:
                os.utime(path.as_posix(), (attrs['mtime'], attrs['mtime']))
        if 'ctime' in attrs:
            raise NotImplementedError
        if 'content' in attrs:
            with path.open(mode='w+') as o_f:
                o_f.write(attrs['content'])
    elif tree['type'] == 'directory':
        if not path.exists():
            try:
                path.mkdir()
            except FileNotFoundError as err:
                return str(err)
            except FileExistsError as err:
                return str(err)
        for child in tree['children']:
            status = dict_2_disk(child, path)
            if not status == "FILE_SYSTEM_WRITTEN_TO_DISK":
                return status
    else:
        raise AttributeError('Unrecognized node type {}, must be "file" or '
                             '"directory".'.format(tree['type']))

    return "FILE_SYSTEM_WRITTEN_TO_DISK"


def create_file_by_size(path, size):
    """Create a file with a particular byte length."""
    with open(path, 'wb') as o_f:
        o_f.truncate(size)

# --- File system comparison --- #

def is_file(node):
    return node['type'] == 'file'

def attribute_diff(attr1, attr2):
    tag = 'correct'
    for key in attr1:
        # no question demands user to change timestamp
        if not key in ['atime', 'ctime', 'mtime']:
            if attr1[key] != attr2[key]:
                attr1[key] += ':::{}'.format(attr2[key])
                tag = 'incorrect'
    return tag

def filesystem_diff(fs1, fs2):
    """
    Args:
        fs1 & fs2:

    Given the dictionary representations of two file systems fs1 & fs2,
    recursively compute the difference between these two systems and store the
    differences in fs1.

    """

    def __equal__(n1, n2):
        """Determine if two FS nodes are equal."""
        return (n1['type'] == n2['type'] and n1['name'] == n2['name'])

    def __ahead__(n1, n2):
        """Determine if node1 comes ahead of node2 in the filesystem."""
        if n1['type'] == 'file' and n2['type'] == 'directory':
            return True
        if n1['type'] == n2['type'] and n1['name'] < n2['name']:
            return True
        return False

    def mark(node, tag):
        """Mark a node and its descendants with a specific tag."""
        add_tag(node, tag)
        if node['type'] == 'directory':
            for child in node['children']:
                    mark(child, tag)

    def markcopy(node, tag):
        """ Mark a node and its descendants with a specific tag and make a deep
         copy. """
        node2 = copy.deepcopy(node)
        add_tag(node2, tag)
        if node2['type'] == 'directory':
            for child in node2['children']:
                mark(child, tag)
        return node2

    # comparing a file to a directory, shouldn't happen
    if is_file(fs1) and not is_file(fs2):
        raise ValueError('Cannot compare a file to a directory.')
    # comparing a directory to a file, shouldn't happen
    if not is_file(fs1) and is_file(fs2):
        raise ValueError('Cannot compare a directory to a file.')

    annotated_fs1 = Directory(fs1['name']).to_dict()

    errors = collections.defaultdict(int)

    fs1_children = fs1['children']
    fs2_children = fs2['children']
    annotated_children = []

    i = 0
    j = 0
    while (i < len(fs1_children)) and (j < len(fs2_children)):
        child1 = fs1_children[i]
        child2 = fs2_children[j]
        if __equal__(child1, child2):
            if child1['type'] == 'file':
                # comparing two files
                tag = attribute_diff(child1['attributes'],
                                     child2['attributes'])
                if tag_exists(child2, 'to_select'):
                    add_tag(child1, 'to_select')
                annotated_children.append(markcopy(child1, tag))
                if tag != 'correct':
                    errors['ch_incorrect'] += 1
            elif child1['type'] == 'directory':
                # comparing two directories
                annotated_child = filesystem_diff(child1, child2)
                if tag_exists(child2, 'to_select'):
                    add_tag(annotated_child, 'to_select')
                annotated_children.append(annotated_child)
                if contains_error(annotated_child) or \
                        contains_error_in_child(annotated_child):
                    errors['ch_incorrect'] += 1
            else:
                raise AttributeError('Unrecognized node type {}, must be '
                    '"file" or "directory".'.format(child1['type']))
            i += 1
            j += 1
        elif __ahead__(child1, child2):
            annotated_children.append(markcopy(child1, 'extra'))
            errors['ch_extra'] += 1
            i += 1
        else:
            annotated_children.append(markcopy(child2, 'missing'))
            errors['ch_missing'] += 1
            j += 1
    if i < len(fs1_children):
        for child1 in fs1_children[i:]:
            annotated_children.append(markcopy(child1, 'extra'))
            errors['ch_extra'] += 1
    if j < len(fs2_children):
        for child2 in fs2_children[j:]:
            annotated_children.append(markcopy(child2, 'missing'))
            errors['ch_missing'] += 1

    annotated_fs1['children'] = annotated_children
    annotated_fs1['tag'] = errors
    if tag_exists(fs2, 'to_select'):
        add_tag(annotated_fs1, 'to_select')

    return annotated_fs1

def annotate_path_selection(fs, task_type, paths):
    """
    Annotate the files/directories that are printed in the stdout in a file
    system.

    """
    for path in paths:
        steps = path.as_posix().split('/')
        stack = [fs]
        node = fs
        stop_search = False
        for i in range(1, len(steps)):
            step = steps[i]
            for child in node['children']:
                if child['name'] == step:
                    if tag_exists(child, 'missing'):
                        # missing fs nodes cannot be selected
                        stop_search = True
                        break
                    if i == len(steps) - 1:
                        if task_type in ["stdout", 'filesystem_change']:
                            # file search commands does not affect task
                            # completion simply show what is selected
                            add_tag(child, 'selected', 0)
                        else:
                            if tag_exists(child, 'to_select'):
                                add_tag(child, 'selected', 0)
                            else:
                                add_tag(child, 'selected', 1)
                                for ancestor in stack:
                                    inc_tag(ancestor, 'ch_incorrect')
                    else:
                        node = child
                        stack.append(node)
                    break
            if stop_search:
                break

    # mark unselected files at last
    def mark_unselected(node):
        if not tag_exists(node, 'missing'):
            incorrect = False
            if tag_exists(node, 'to_select') and not tag_exists(node, 'selected'):
                add_tag(node, 'selected', -1)
                incorrect = True
            if node['type'] == 'directory':
                for child in node['children']:
                    if mark_unselected(child):
                        inc_tag(node, 'ch_incorrect')
                        incorrect = True
            return incorrect
        else:
            return True

    mark_unselected(fs)

def annotate_node(fs, path, tag, including_self=True, recursive=False,
                  file_only=False, **kwargs):
    """
    Annotate specific node(s) in the filesystem with a specific tag. The
    keyword arguments specify the filtering criteria.

    Args:
        fs: The file system to be annotated.
        path: The location of the node to be annotated in the file system.
        tag: The tag to give to the file system node and its descendants.
        including_self: The node itself shall be tagged.
        recursive: Recursively tag the descendants of the node.
        file_only: Tag only files (excluding sub-directories).
        **kwargs: Filtering criteria on which node to tag.

    """
    def mark(node, tag, including_self=True, file_only=False, **kwargs):
        """Mark a node and its descendants with a specific tag."""
        if including_self:
            # tag the node itself before tagging its descendants
            add_tag(node, tag)
        if node['type'] == 'directory':
            for child in node['children']:
                if child['type'] == 'file':
                    if 'attr' in kwargs:
                        attr = kwargs['attr']
                        attr_value = child['attributes'][attr]
                        attr_lower_bound = kwargs['attr_lower_bound']
                        attr_higher_bound = kwargs['attr_higher_bound']
                        if attr_value >= attr_lower_bound \
                                and attr_value < attr_higher_bound:
                            mark(child, tag)
                else:
                    mark(child, tag, including_self=(not file_only),
                        file_only=file_only, **kwargs)

    steps = path.as_posix().split('/')
    stack = []
    node = fs
    # descend to the target node if the path depth is greater than 1
    if len(steps) > 1:
        for step in steps:
            step_matched = False
            for child in node['children']:
                if child['name'] == step:
                    # missing file system branches cannot be tagged
                    step_matched = True
                    if tag_exists(child, 'missing'):
                        break
                    stack.append(node)
                    node = child
            if not step_matched:
                raise ValueError(
                    'Specified path {} does not exist in the file system'.format(path.as_posix()))

    if recursive:
        mark(fs, tag, including_self=including_self,
             file_only=file_only, **kwargs)
    else:
        add_tag(fs, tag)

    # tag the ancestors accordingly if a node has been given an error tag
    if tag in ERROR_TAGS:
        for ancestor in stack:
            inc_tag(ancestor, 'ch_incorrect')

def contains_error(node):
    return node['tag'] and ('missing' in node['tag'] or
                            'extra' in node['tag'] or
                            'incorrect' in node['tag'])

def contains_error_in_child(node):
    return node['tag'] and ('ch_missing' in node['tag'] or
                            'ch_extra' in node['tag'] or
                            'ch_incorrect' in node['tag'])

def tag_exists(node, tag):
    if 'tag' in node:
       if tag in node['tag']:
           return True
    return False

def add_tag(node, tag, value=1):
    if not 'tag' in node:
        node['tag'] = collections.defaultdict(int)
    node['tag'][tag] = value

def inc_tag(node, tag):
    if not 'tag' in node:
        node['tag'] = collections.defaultdict(int)
        node['tag'][tag] = 1
    else:
        node['tag'][tag] += 1

def annotate_stdout_errors(fs_diff, stdout_diff):
    """
    Given the standard output diff object, annotate the paths with standard
    output errors in the file system diff object.

    Args:
        fs_diff:
        stdout_diff:

    """
    # TODO: the current implementation is inefficient for it look through each
    # standard output diff line linearly; it might be possible to make use of
    # the tree structure of the file system
    for stdout_line in stdout_diff['lines']:
        if stdout_line['tag'] in ['missing', 'extra']:
            path = extract_path(stdout_line['line'])
            if path:
                annotate_node(fs_diff, path, 'stdout_'+stdout_line['tag'])

# --- Other File System Utilities --- #

def extract_path_from_ls_command(input, tokens):
    path_pattern = re.compile(
        r'((([^ ]*\/)+[^ ]*)|([a-zA-Z]+\.[a-zA-Z]+))(\:|$)')
    match = re.search(path_pattern, input.strip())
    if not match:
        if tokens[-1] == 'ls':
            return None
        else:
            partial_path = None
            for i in range(len(tokens)-1, 0, -1):
                if not tokens[i].startswith('-'):
                    partial_path = pathlib.Path(tokens[i])
                    break
            if partial_path is None:
                return None
    else:
        partial_path = pathlib.Path(match.group(0).strip())
    return partial_path

def extract_path(input, current_dir=None, is_ls_command=False):
    """
    Extract file paths from a line of terminal stdout, considering the current
    directory of the user. This function assumes that there is only one file
    path in the input line.

    :param input: a stdout line from which the file path is to be extracted
    :param current_dir: the directory where the user is currenly at, '.' by
        default.
    :param is_ls_command: the user executed an "ls" command

    Return None if there is no path mention in the input line, otherwise the
    path object.
    """
    path_pattern = re.compile(
        r'((([^ ]*\/)+[^ ]*)|([a-zA-Z]+\.[a-zA-Z]+))(\:|$)')

    tokens = input.strip().split()
    if len(tokens) == 1:
        if tokens[-1] in directories_in_sample_filesystems:
            partial_path = pathlib.Path(tokens[-1])
            return current_dir / partial_path
    if is_ls_command and len(tokens) > 0:
        partial_path = pathlib.Path(tokens[-1])
        match = re.search(path_pattern, tokens[-1])
        if not match:
            path = current_dir / partial_path
        else:
            path = partial_path
    else:
        match = re.search(path_pattern, input.strip())
        if not match:
            return None
        path = match.group(0).strip()
        # special path format for "grep"
        if path.endswith(':'):
            path = path[:-1]
        if path == '.':
            path = './'
        if path.startswith('./'):
            path = path[2:]
        path = current_dir / pathlib.Path(path) if current_dir \
            else pathlib.Path(path)
    return path

def filesystem_sort(fs):
    if fs and fs['type'] == 'directory':
        for child in fs['children']:
            filesystem_sort(child)
        fs['children'] = sorted([c for c in fs['children'] if c['type'] == 'file'],
                                key=lambda x:x['name']) + \
                         sorted([c for c in fs['children'] if c['type'] != 'file'],
                                key=lambda x:x['name'])
    return fs

if __name__=="__main__":
    with open('fs1.json') as data_file:    
        fs1 = json.load(data_file)
    with open('fs2.json') as data_file:    
        fs2 = json.load(data_file)
  
    fs = filesystem_diff(fs1, fs2)
    print(json.dumps(fs))
