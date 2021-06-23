"""This module is used to get files that are related to changed or deleted files.  Since the bilara-data-integrity tests
are now only run on a per file basis, we need to make sure that when an html file is modified the tests are run on both
the html and root file.  This module will also make sure that if an hmtl file is deleted, it's related root file is also
deleted.

This is the list of the relationships between tests and files in bilara-data-integrity:
Test                     ->  Files
------------------------------------------------
bilara_check_comment     ->  comment and root
bilara_check_html        ->  html and root
bilara_check_reference   ->  only reference
bilara_check_root        ->  only root
bilara_check_translation ->  translation and html
bilara_check_variant     ->  variant and root
"""

import argparse
import os
import sys
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import List

# Set up argparse to get changed or deleted files passed to the module
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-f', '--files', required=True, type=Path, nargs='*')
args = arg_parser.parse_args()

DIRECTORY_MAPPINGS = {'comment': ['root'], 'html': ['root'], 'reference': [],
                      'root': ['html', 'translation', 'variant'], 'translation': ['html'], 'variant': ['root']}


def _get_related_directories(files: List[Path]) -> dict:
    """Based on the changed or deleted files provided by the Action,
    find the directories that hold the related files."""
    # Will create a dictionary where the key is the file ID, and the value is a list of directories,
    # like {'an1.616-627': ['html'], 'mn1': ['html', 'translation']}
    file_dir_mappings = defaultdict(list)

    for file in files:
        # Like html, root, translation, etc.
        bilara_data_dir = file.parts[0]
        # Like an1.1-10_reference
        bilara_data_file = file.stem
        # Like an1.1-10
        bilara_file_id = bilara_data_file.split('_')[0]
        file_dir_mappings[bilara_file_id].append(bilara_data_dir)

    for bilara_file_id, bilara_data_dirs in file_dir_mappings.items():
        # Make a deepcopy to avoid any weirdness
        existing_dirs = deepcopy(bilara_data_dirs)
        # Will hold the list of directories that we need to get the related files from
        related_dirs = []
        for existing_dir in existing_dirs:
            # Get the directories where the related files live
            mapped_dirs = DIRECTORY_MAPPINGS.get(existing_dir)
            for mapped_dir in mapped_dirs:
                if mapped_dir not in bilara_data_dirs and mapped_dir not in related_dirs:
                    related_dirs.append(mapped_dir)

        # Overwrite the original list since we only want to get the missing related files, and not the supplied files
        file_dir_mappings[bilara_file_id] = related_dirs

    return file_dir_mappings


def get_related_files(files: List[Path]) -> str:
    """Get the paths to the related files provided by the Action after getting the directories they live in."""
    file_dir_mappings = _get_related_directories(files=files)
    related_files = []
    for file_id, related_dirs in file_dir_mappings.items():
        for related_dir in related_dirs:
            for root, sub_dirs, files in os.walk(related_dir):
                for file in files:
                    if file_id == file.split('_')[0]:
                        related_files.append(os.path.join(root, file))

    # Convert from Path objects to strings since I don't know
    # how they will be converted when I return the values.
    all_files = [str(f) for f in files]
    all_files.extend(related_files)
    print(' '.join(all_files))
    # return ' '.join(all_files)


if __name__ == '__main__':
    get_related_files(files=args.files)
