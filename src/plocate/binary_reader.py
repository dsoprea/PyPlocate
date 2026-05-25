"""Binary file access for plocate databases."""

import logging
import mmap
import os
import typing

import plocate.errors

_LOGGER = logging.getLogger(__name__)


class BinaryReader:
    """Read byte ranges from an open database file, optionally via mmap."""

    def __init__(self, file_object: typing.BinaryIO) -> None:
        """Attach to an open binary file and optionally map it read-only."""

        self._file_object = file_object

        # Measure file size and rewind to the start.
        file_object.seek(0, os.SEEK_END)
        self.file_size = file_object.tell()
        file_object.seek(0)
        self._mmap: mmap.mmap | None = None

        # Prefer mmap when the file object supports fileno().
        if hasattr(file_object, "fileno"):
            try:
                self._mmap = mmap.mmap(file_object.fileno(), 0, access=mmap.ACCESS_READ)
            except (OSError, ValueError, BufferError):
                self._mmap = None

    def close(self) -> None:
        """Release mmap and close the underlying file object."""

        if self._mmap is not None:
            self._mmap.close()
            self._mmap = None
        self._file_object.close()

    def read_bytes(self, offset: int, length: int) -> bytes:
        """Read length bytes starting at offset, using mmap when available."""

        if length == 0:
            return b""

        if self._mmap is not None:
            return self._mmap[offset : offset + length]

        self._file_object.seek(offset)
        data = self._file_object.read(length)
        if len(data) != length:
            message = "unexpected end of file while reading {length} bytes at offset {offset}".format(
                length=length,
                offset=offset,
            )
            raise plocate.errors.PlocateFormatError(message)

        return data
