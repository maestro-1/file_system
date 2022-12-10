from typing import List, Union, Generator
import uuid
import fnmatch
import os
from pathlib import Path, PosixPath
from file_operation_enums import CompressedFileType, PlainFileType

from utility import manage_pwd


class ManagePath:
    def __init__(self, base_path: Union[str, PosixPath]) -> None:
        if not isinstance(base_path, str) and not isinstance(base_path, PosixPath):
            raise TypeError("base_path must be str or PosixPath object(from Pathlib)")

        if isinstance(base_path, str):
            self.base_path = Path(base_path).resolve()

        elif isinstance(base_path, PosixPath):
            self.base_path = base_path.resolve()

    @property
    def all_names_in_path(self) -> List[str]:
        return [item_name for item_name in os.listdir(self.base_path)]

    def get_files_of_type_in_path(
        self,
        file_type: Union[PlainFileType, CompressedFileType],
        dir_path: str = None,
        multi_level: bool = False,
    ) -> Generator:
        """
        return paths to all files with specified extention in path
        """
        if dir_path is None:
            dir_path = self.base_path

        with manage_pwd(self.base_path):
            for file_obj in os.listdir(dir_path):

                if os.path.isdir(file_obj) and multi_level:
                    file_obj = self.get_files_of_type_in_path(
                        file_type, multi_level, file_obj
                    )

                # fix this
                if not fnmatch.fnmatch(file_obj, file_type):
                    continue

                yield file_obj

    def name_folder(self, name: str, names_in_path: List[str]) -> str:
        """
        Generate new name for folder using shortuuid if folder name
        already exists in the folder
        """
        if len(names_in_path) and name in names_in_path:
            return f"{name}_{uuid.uuid4()}"
        return name

    def create_folder(self, folder_name: str) -> str:
        with manage_pwd(self.base_path):
            final_folder_name = self.name_folder(folder_name, self.all_names_in_path)
            os.mkdir(final_folder_name)
        return final_folder_name
