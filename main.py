import pdb
import os
from pathlib import Path
from file_strategies import CompressedReusableFile, PlainFile, ZippedFile
from path_manager import ManagePath


def compress(path: str):
    managed_path = ManagePath(path)
    all_dir_items = managed_path.all_names_in_path()
    input_name = input("file name")
    for name in all_dir_items:
        if name == input_name:
            file_obj = PlainFile(os.path.join(path, name))

    CompressedReusableFile(f"{file_obj.file_name}.txt.gz", "w").compress()

def main(path: str, target_file):
    path = Path(path).resolve()
    managed_path = ManagePath(path)

    all_dir_items = managed_path.all_names_in_path

    if target_file not in all_dir_items:
        return None

    # zip doesn't need a created folder on our end to extract(or compress) does this by default
    file_obj = ZippedFile(target_file, managed_path, "utf-8")
    
    # file_path = file_obj.extract("test-folder")
    file_archive = file_obj.archive_folder(file_obj.base_path / "../invoices yassir")

    return file_archive
    


if "__main__" == __name__:
    base_path_name = input("enter folder path: ")
    target_file = input("enter target file name: ")

    main(base_path_name, target_file)