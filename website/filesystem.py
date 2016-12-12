import pathlib
import json

def normalize_JSON(JSON_string: str):
	return json.dumps(json.loads(JSON_string), sort_keys=True, indent=2)

def merge_dictionaries(a: dict, b: dict) -> dict:
	return {**a, **b}

def disk_2_dict(path: pathlib.Path) -> dict:
	if path.is_dir():
		subtrees = {}
		for subpath in path.iterdir():
			subtrees = merge_dictionaries(subtrees, disk_2_dict(subpath))
		return {path.parts[-1]: subtrees}
	else:
		return {path.parts[-1]: None}

def dict_2_JSON(tree: dict) -> str:
	return normalize_JSON(json.dumps(tree))

def dict_2_disk(tree: dict, root_path: pathlib.Path):
	print(tree)
	for name, subtree in tree.items():
		if subtree is None:
			# file
			newfile = (root_path / name).open(mode='w+')
			newfile.close()
		else:
			# directory
			(root_path / name).mkdir()
			dict_2_disk(subtree, root_path / name)
