"""Binary file access for plocate databases."""

from __future__ import annotations

import mmap
import os
from typing import BinaryIO

from plocate_db.errors import PlocateFormatError


class BinaryReader:
    """Read byte ranges from an open database file, optionally via mmap."""

    def __init__(self, file_object: BinaryIO) -> None:
        self._file_object = file_object
        file_object.seek(0, os.SEEK_END)
        self.file_size = file_object.tell()
        file_object.seek(0)
        self._mmap: mmap.mmap | None = None
        if hasattr(file_object, "fileno"):
            try:
                self._mmap = mmap.mmap(file_object.fileno(), 0, access=mmap.ACCESS_READ)
            except (OSError, ValueError, BufferError):
                self._mmap = None

    def close(self) -> None:
        if self._mmap is not None:
            self._mmap.close()
            self._mmap = None
        self._file_object.close()

    def read_bytes(self, offset: int, length: int) -> bytes:
        if length == 0:
            return b""

        if self._mmap is not None:
            return self._mmap[offset : offset + length]

        self._file_object.seek(offset)
        data = self._file_object.read(length)
        if len(data) != length:
            raise PlocateFormatError(
                f"unexpected end of file while reading {length} bytes at offset {offset}"
            )
        return data
