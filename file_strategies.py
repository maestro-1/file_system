from abc import ABC, abstractmethod
from contextlib import contextmanager
import builtins
import io
import os
import builtins
import hashlib
from pathlib import Path, PosixPath
import zipfile
from zipfile import BadZipFile
from typing import List, Union

from file_operation_enums import (
    file_open_style,
    PlainFileType,
    CompressedFileType,
    OperationModes,
)
from errors import FailedToOpenError
from utility import directory_walk
from utility import manage_pwd
from path_manager import ManagePath


class ReusableFile(ABC):
    @property
    def file_hash(self):
        return hashlib.md5(open(self.path, "rb").read()).hexdigest()

    @property
    def file_name(self) -> str:
        return self.path.stem

    def _set_open_with(self, extension: str):
        if extension is not None:
            openned_as = file_open_style.get(extension, None)
            return openned_as if openned_as is not None else builtins.open

        raise FailedToOpenError()

    def __eq__(self, other):
        """
        Returns a comparison for file hashes
        """
        if isinstance(other, type(self)):
            return self.file_hash == other.file_hash

    @abstractmethod
    def __iter__(self):
        """
        Returns a new iterator over the file using the arguments from the constructor. Each call
        to __iter__ returns a new iterator independent of all others
        :return: iterator over file
        """
        raise NotImplementedError()

    @abstractmethod
    def read(self):
        raise NotImplementedError()


class CompressedFile(ReusableFile):
    @property
    @abstractmethod
    def is_compressed(self):
        raise NotImplementedError()

    @abstractmethod
    def decompress(file):
        """
        Returns a buffer object of the content of the file uncompressed
        """
        raise NotImplementedError()

    @abstractmethod
    def compress(file):
        """
        Returns a buffer object of the content of the file uncompressed
        """
        raise NotImplementedError()


class PlainFile(ReusableFile):
    def __init__(
        self,
        path,
        path_manager: ManagePath,
        mode: OperationModes = OperationModes.READ_MODE,
        open_with: PlainFileType = PlainFileType.TEXT,
        encoding: str = "utf-8",
    ):
        if not os.path.isfile(path) and "w" not in mode:
            raise FileNotFoundError("No such file in this directory")

        self.path = path
        self.mode: OperationModes = OperationModes.READ_MODE
        self.encoding: str = encoding
        self._open_with = open_with

        self.buffering = 1024

    def __iter__(self):
        with self._open_with(
            self.path,
            mode=self.mode,
            buffering=self.buffering,
            encoding=self.encoding,
        ) as file_content:
            for line in file_content:
                yield line

    def read(self):
        with self._open_with(
            self.path,
            mode=self.mode,
            encoding=self.encoding,
        ) as file_content:
            return file_content.read()


class CompressedReusableFile(CompressedFile):
    def __init__(
        self,
        path: str,
        encoding: str,
        path_manager: ManagePath,
        open_with: CompressedFileType = CompressedFileType.GZIP,
        mode: OperationModes = OperationModes.READ_MODE,
        compresslevel: int = 9,
    ):
        if not os.path.isfile(path) and "w" not in mode:
            raise FileNotFoundError("No such file in this directory")

        self.path = path
        self.mode = mode
        self.encoding = encoding
        self.buffering = 1024

        _, extension = os.path.splitext(path)

        self._open_with = self._set_open_with(extension)

        self.compresslevel = compresslevel
        # self.magic_bytes = magic_bytes

    def is_compressed(self):
        with open(self.path) as file_data:
            return file_data.read(1024)

    def __iter__(self):
        with self._open_with(
            self.path,
            mode=self.mode,
            buffering=self.buffering,
            encoding=self.encoding,
        ) as file_content:
            for line in file_content:
                yield line

    def read(self):
        with self._open_with(
            self.path,
            mode=self.mode,
        ) as file_content:
            return file_content.read()

    def decompress(self):
        with self._open_with(self.path, mode=self.mode) as compressed_file:
            with io.TextIOWrapper(
                compressed_file,
                encoding=self.encoding,
            ) as buffered_content:
                return buffered_content

    def compress(self, file_path):
        with open(f"{file_path}", "rb") as uncompressed_file:
            with self._open_with(self.path, "wb") as compressed_file:
                return (compressed_file, uncompressed_file)


class ZippedFile(ReusableFile):
    def __init__(
        self,
        target_file: str,
        path_manager: ManagePath,
        encoding: str = "utf-8",
        pwd: str = None,
        mode: OperationModes = OperationModes.READ_MODE,
        compresslevel: int = 1,
    ):
        self.path_manager = path_manager

        self.path = Path(self.path_manager.base_path / target_file)
        if not os.path.isfile(self.path) and zipfile.is_zipfile(self.path) and "w" not in mode:
            raise BadZipFile("No such file in this directory")

        self.mode = str(mode)
        self.encoding = encoding

        if pwd and isinstance(pwd, str):
            self.pwd = bytes(pwd, "utf-8")
        else:
            self.pwd = pwd

        self._open_with = self._set_open_with()

        if compresslevel > 0 and compresslevel < 10:
            self.compresslevel = zipfile.ZIP_DEFLATED
        elif compresslevel > 10:
            self.compresslevel = zipfile.LZMA
        else:
            self.compresslevel = zipfile.ZIP_STORED

        self.buffering = 1024

    def __iter__(self):
        with self._open_with(self.path) as archive:
            for file in archive.namelist():
                yield file

    def read_compressed(self, filename: str) -> Union[None, bytes]:
        if(filename not in self.items_in_zip):
            return None
    
        with self._open_with(
            self.path,
            mode=self.mode,
        ) as file_content:
            return file_content.read(filename)

    @property
    def is_encrypted(self) -> bool:
        return bool(self._open_with(self.path).testzip())

    @property
    def base_path(self):
        self.path_manager.base_path

    @property
    def items_in_zip(self) -> List[str]:
        with self._open_with(self.path) as archive:
            return archive.namelist()

    @contextmanager
    def _manage_archive(self, file_name: PosixPath, mode: OperationModes):
        try:
            archive = self._open_with(file_name, mode=str(mode))
            yield archive

        except Exception as err:
            print(err)
        finally:
            try:
                archive.close()
            except UnboundLocalError:
                pass

    def _set_open_with(self):
        return zipfile.ZipFile

    def read(self):
        pass

    def extract(self, folder_name: str, specific_file: str = None):
        # consider changing working directory before extracting. Use the manager_pwd function from utitlity module

        if specific_file is not None and specific_file in self.items_in_zip:
            with self._manage_archive(self.path, OperationModes.READ_MODE) as archive:
                return archive.extract(
                    specific_file, folder_name, pwd=self.pwd if not self.pwd else None
                )

        with self._manage_archive(self.path, OperationModes.READ_MODE) as archive:
            return [
                archive.extract(
                    member, folder_name, pwd=self.pwd if not self.pwd else None
                ) for member in self.items_in_zip
            ]

    def archive_folder(self, directory_path: str = None, skip_files: List[str] = None):
        """
        directory directs the path to the folder to be archived, 
        skip files determines files in the folder to be ignored in archiving
        The archive name/path passed into Zipped class handles the path and 
        all relating items
        """
        if skip_files is None:
            skip_files = []

        directory_path = Path(directory_path).resolve()
        zipfile_name = self.path_manager.name_folder(str(directory_path).split('/')[-1], self.path_manager.all_names_in_path)
        zipfile_path = directory_path.parent.resolve() / f"{zipfile_name}.zip"

        path_gen = directory_walk(directory_path)
        # over writes on each write. Consider changing to append instead of write
        with self._manage_archive(zipfile_path, OperationModes.WRITE_MODE) as archive:
            return [
                archive.write(file_item, compress_type=self.compresslevel) for file_item in path_gen 
                if file_item not in skip_files
            ]