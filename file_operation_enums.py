import gzip
import bz2
import builtins
from typing import Optional
import zipfile
from enum import Enum


class BasicEnum(Enum):
    __hash__ = Enum.__hash__

    def __eq__(self, __o: object) -> bool:
        return super().__eq__(__o)

    @classmethod
    def list_values(cls) -> list:
        return list(map(lambda c: c.value, cls))

    @classmethod
    def list_names(cls) -> list:
        return list(map(lambda c: c.name, cls))

    @classmethod
    def get(cls, member: str) -> Optional[Enum]:
        member = member.upper().replace(" ", "_")
        try:
            return cls.__members__[member]
        except KeyError:
            return None


class BasicStringEnum(BasicEnum):
    def __str__(self) -> str:
        return self.value


class OperationModes(BasicStringEnum):
    READ_MODE = "r"
    READ_WRITE_MODE = "r+"
    WRITE_MODE = "w"
    APPEND_MODE = "a"
    CREATE_MODE = "x"
    READ_BINARY_MODE = "rb"
    WRITE_BINARY_MODE = "wb"
    APPEND_BINARY_MODE = "r+b"


class CompressedFileType(BasicStringEnum):
    ZIP = "zip"
    GZIP = "gz"
    BZ2 = "bz2"
    TAR = 'tar'


class PlainFileType(BasicStringEnum):
    TEXT = "txt"


file_open_style = {
    CompressedFileType.ZIP: zipfile.ZipFile,
    CompressedFileType.GZIP: gzip.open,
    CompressedFileType.BZ2: bz2.BZ2File,
    CompressedFileType.TAR: gzip.open,
    PlainFileType.TEXT: builtins.open,
}
