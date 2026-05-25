"""TurboPFor posting list decoding for plocate databases."""

import logging
import struct

import plocate.errors

_LOGGER = logging.getLogger(__name__)

BLOCK_SIZE = 128

BLOCK_TYPE_FOR = 0
BLOCK_TYPE_PFOR_VB = 1
BLOCK_TYPE_PFOR_BITMAP = 2
BLOCK_TYPE_CONSTANT = 3


def div_round_up(value: int, divisor: int) -> int:
    """Return value divided by divisor, rounded up."""

    return (value + divisor - 1) // divisor


def mask_for_bits(bit_width: int) -> int:
    """Return a bitmask for the given bit width."""

    if bit_width == 32:
        return 0xFFFFFFFF

    return (1 << bit_width) - 1


def bytes_for_packed_bits(count: int, bit_width: int) -> int:
    """Return packed byte length for count values at bit_width bits each."""

    return div_round_up(count * bit_width, 8)


def read_le_uint32(data: bytes, offset: int) -> int:
    """Read one little-endian uint32 from data at offset."""

    value = struct.unpack_from("<I", data, offset)[0]

    return value


def read_le_uint64(data: bytes, offset: int) -> int:
    """Read one little-endian uint64 from data at offset."""

    value = struct.unpack_from("<Q", data, offset)[0]

    return value


def read_baseval(data: bytes, offset: int) -> tuple[int, int]:
    """Decode the first docid prefix value and return it with the new offset."""

    first_byte = data[offset]
    if first_byte < 128:
        return first_byte, offset + 1
    if first_byte < 192:
        value = ((data[offset] << 8) | data[offset + 1]) & 0x3FFF
        return value, offset + 2
    if first_byte < 224:
        value = (
            (data[offset] << 16)
            | (data[offset + 2] << 8)
            | data[offset + 1]
        ) & 0x1FFFFF
        return value, offset + 3
    if first_byte < 240:
        value = (
            (data[offset] << 24)
            | (data[offset + 1] << 16)
            | (data[offset + 2] << 8)
            | data[offset + 3]
        ) & 0x0FFFFFFF
        return value, offset + 4

    message = "unsupported posting list base value prefix {prefix}".format(prefix=first_byte)
    raise plocate.errors.PlocateFormatError(message)


def read_varbyte(data: bytes, offset: int) -> tuple[int, int]:
    """Decode one TurboPFor varbyte exception value."""

    first_byte = data[offset]
    if first_byte <= 176:
        return first_byte, offset + 1
    if first_byte <= 240:
        value = ((first_byte - 177) << 8) | data[offset + 1]
        value += 177
        return value, offset + 2
    if first_byte <= 248:
        value = ((first_byte - 241) << 16) | read_le_uint32(data, offset + 1) & 0xFFFF
        value += 16561
        return value, offset + 3
    if first_byte == 249:
        value = data[offset + 1] | (data[offset + 2] << 8) | (data[offset + 3] << 16)
        return value, offset + 4
    if first_byte == 250:
        value = read_le_uint32(data, offset + 1)
        return value, offset + 5

    message = "unsupported posting list varbyte prefix {prefix}".format(prefix=first_byte)
    raise plocate.errors.PlocateFormatError(message)


class BitReader:
    """Sequential bit reader over packed posting list bytes."""

    def __init__(self, data: bytes, offset: int, bit_width: int) -> None:
        """Initialize a reader at offset over data using bit_width bits per value."""

        self._data = data
        self._offset = offset
        self._bit_width = bit_width
        self._mask = mask_for_bits(bit_width)
        self._bits_used = 0

    def read(self) -> int:
        """Read the next packed value."""

        value = (read_le_uint32(self._data, self._offset) >> self._bits_used) & self._mask
        self._bits_used += self._bit_width
        self._offset += self._bits_used // 8
        self._bits_used %= 8

        return value


class InterleavedBitReader:
    """Four-stream interleaved bit reader used by 128-value blocks."""

    def __init__(self, data: bytes, offset: int, stream_index: int, bit_width: int) -> None:
        """Initialize one stream of an interleaved bit reader."""

        self._data = data
        self._offset = offset + stream_index * 4
        self._bit_width = bit_width
        self._mask = mask_for_bits(bit_width)
        self._bits_used = 0
        self._stride = 16

    def read(self) -> int:
        """Read the next value from this interleaved stream."""

        if self._bits_used + self._bit_width > 32:
            lower = read_le_uint32(self._data, self._offset) >> self._bits_used
            upper = read_le_uint32(self._data, self._offset + self._stride) << (32 - self._bits_used)
            value = (lower | upper) & self._mask
        else:
            value = (read_le_uint32(self._data, self._offset) >> self._bits_used) & self._mask

        self._bits_used += self._bit_width
        self._offset += self._stride * (self._bits_used // 32)
        self._bits_used %= 32

        return value


def decode_constant(data: bytes, offset: int, count: int, previous_value: int) -> tuple[int, list[int]]:
    """Decode a constant TurboPFor block."""

    header = data[offset]
    offset += 1
    bit_width = header & 0x3F
    raw_value = read_le_uint32(data, offset)
    if bit_width < 32:
        raw_value &= mask_for_bits(bit_width)
    offset += div_round_up(bit_width, 8)

    values: list[int] = []
    current_value = previous_value
    for _index in range(count):
        current_value = raw_value + current_value + 1
        values.append(current_value)

    return offset, values


def decode_for(data: bytes, offset: int, count: int, previous_value: int) -> tuple[int, list[int]]:
    """Decode a frame-of-reference TurboPFor block."""

    header = data[offset]
    offset += 1
    bit_width = header & 0x3F
    bit_reader = BitReader(data, offset, bit_width)

    values: list[int] = []
    current_value = previous_value
    for _index in range(count):
        current_value = bit_reader.read() + current_value + 1
        values.append(current_value)

    offset += bytes_for_packed_bits(count, bit_width)

    return offset, values


def decode_for_interleaved(data: bytes, offset: int, previous_value: int) -> tuple[int, list[int]]:
    """Decode one interleaved 128-value FOR block."""

    header = data[offset]
    offset += 1
    bit_width = header & 0x3F
    stream_readers = [
        InterleavedBitReader(data, offset, stream_index, bit_width)
        for stream_index in range(4)
    ]

    raw_values: list[int] = []
    for block_index in range(BLOCK_SIZE // 4):
        raw_values.append(stream_readers[0].read())
        raw_values.append(stream_readers[1].read())
        raw_values.append(stream_readers[2].read())
        raw_values.append(stream_readers[3].read())

    offset += bytes_for_packed_bits(BLOCK_SIZE, bit_width)

    values: list[int] = []
    current_value = previous_value
    for raw_value in raw_values:
        current_value = raw_value + current_value + 1
        values.append(current_value)

    return offset, values


def decode_pfor_bitmap_exceptions(data: bytes, offset: int, count: int) -> tuple[int, list[int]]:
    """Decode bitmap exception values for one PFor block."""

    exception_bit_width = data[offset]
    offset += 1
    bitmap_length = div_round_up(count, 8)
    exception_values = [0] * count
    exception_count = 0
    bit_reader = BitReader(data, offset + bitmap_length, exception_bit_width)

    bitmap_index = 0
    while bitmap_index < count:
        chunk_size = min(64, count - bitmap_index)
        exception_bits = read_le_uint64(data, offset + (bitmap_index // 8))
        if chunk_size < 64:
            exception_bits &= (1 << chunk_size) - 1
        while exception_bits != 0:
            lowest_bit = exception_bits & -exception_bits
            bit_index = (lowest_bit.bit_length() - 1) + bitmap_index
            exception_values[bit_index] = bit_reader.read()
            exception_count += 1
            exception_bits ^= lowest_bit
        bitmap_index += 64

    offset += bitmap_length
    offset += bytes_for_packed_bits(exception_count, exception_bit_width)

    return offset, exception_values


def decode_pfor_bitmap(data: bytes, offset: int, count: int, previous_value: int) -> tuple[int, list[int]]:
    """Decode one non-interleaved PFor bitmap block."""

    header = data[offset]
    offset += 1
    bit_width = header & 0x3F
    offset, exception_values = decode_pfor_bitmap_exceptions(data, offset, count)

    bit_reader = BitReader(data, offset, bit_width)
    values: list[int] = []
    current_value = previous_value
    for index in range(count):
        packed_value = (exception_values[index] << bit_width) | bit_reader.read()
        current_value = packed_value + current_value + 1
        values.append(current_value)

    offset += bytes_for_packed_bits(count, bit_width)

    return offset, values


def decode_pfor_bitmap_interleaved(data: bytes, offset: int, previous_value: int) -> tuple[int, list[int]]:
    """Decode one interleaved 128-value PFor bitmap block."""

    header = data[offset]
    offset += 1
    bit_width = header & 0x3F
    offset, exception_values = decode_pfor_bitmap_exceptions(data, offset, BLOCK_SIZE)

    stream_readers = [
        InterleavedBitReader(data, offset, stream_index, bit_width)
        for stream_index in range(4)
    ]
    raw_values = [0] * BLOCK_SIZE
    for block_index in range(BLOCK_SIZE // 4):
        raw_values[block_index * 4 + 0] = stream_readers[0].read() | (exception_values[block_index * 4 + 0] << bit_width)
        raw_values[block_index * 4 + 1] = stream_readers[1].read() | (exception_values[block_index * 4 + 1] << bit_width)
        raw_values[block_index * 4 + 2] = stream_readers[2].read() | (exception_values[block_index * 4 + 2] << bit_width)
        raw_values[block_index * 4 + 3] = stream_readers[3].read() | (exception_values[block_index * 4 + 3] << bit_width)

    offset += bytes_for_packed_bits(BLOCK_SIZE, bit_width)

    values: list[int] = []
    current_value = previous_value
    for raw_value in raw_values:
        current_value = raw_value + current_value + 1
        values.append(current_value)

    return offset, values


def decode_pfor_vb(data: bytes, offset: int, count: int, previous_value: int) -> tuple[int, list[int]]:
    """Decode one non-interleaved PFor varbyte block."""

    header = data[offset]
    offset += 1
    bit_width = header & 0x3F
    exception_count = data[offset]
    offset += 1

    bit_reader = BitReader(data, offset, bit_width)
    raw_values = [bit_reader.read() for _index in range(count)]
    offset += bytes_for_packed_bits(count, bit_width)

    exceptions: list[int] = []
    if offset < len(data) and data[offset] == 255:
        offset += 1
        for _index in range(exception_count):
            exceptions.append(read_le_uint32(data, offset))
            offset += 4
    else:
        for _index in range(exception_count):
            exception_value, offset = read_varbyte(data, offset)
            exceptions.append(exception_value)

    for exception_index in range(exception_count):
        raw_index = data[offset]
        offset += 1
        raw_values[raw_index] |= exceptions[exception_index] << bit_width

    values: list[int] = []
    current_value = previous_value
    for raw_value in raw_values:
        current_value = raw_value + current_value + 1
        values.append(current_value)

    return offset, values


def decode_pfor_vb_interleaved(data: bytes, offset: int, previous_value: int) -> tuple[int, list[int]]:
    """Decode one interleaved 128-value PFor varbyte block."""

    header = data[offset]
    offset += 1
    bit_width = header & 0x3F
    exception_count = data[offset]
    offset += 1

    stream_readers = [
        InterleavedBitReader(data, offset, stream_index, bit_width)
        for stream_index in range(4)
    ]
    raw_values: list[int] = []
    for block_index in range(BLOCK_SIZE // 4):
        raw_values.append(stream_readers[0].read())
        raw_values.append(stream_readers[1].read())
        raw_values.append(stream_readers[2].read())
        raw_values.append(stream_readers[3].read())
    offset += bytes_for_packed_bits(BLOCK_SIZE, bit_width)

    exceptions: list[int] = []
    if data[offset] == 255:
        offset += 1
        for _index in range(exception_count):
            exceptions.append(read_le_uint32(data, offset))
            offset += 4
    else:
        for _index in range(exception_count):
            exception_value, offset = read_varbyte(data, offset)
            exceptions.append(exception_value)

    for exception_index in range(exception_count):
        raw_index = data[offset]
        offset += 1
        raw_values[raw_index] |= exceptions[exception_index] << bit_width

    values: list[int] = []
    current_value = previous_value
    for raw_value in raw_values:
        current_value = raw_value + current_value + 1
        values.append(current_value)

    return offset, values


def decode_posting_list_docids(data: bytes, num_docids: int) -> tuple[int, ...]:
    """Decode one posting list byte string into sorted docid values."""

    if num_docids == 0:
        return tuple()

    # Read the first absolute docid, then delta-decode the remainder in blocks.
    first_docid, offset = read_baseval(data, 0)
    docids = [first_docid]
    previous_value = first_docid
    index = 1
    while index < num_docids:
        block_count = min(BLOCK_SIZE, num_docids - index)
        header = data[offset]
        block_type = header >> 6
        interleaved = block_count == BLOCK_SIZE

        if block_type == BLOCK_TYPE_FOR:
            if interleaved:
                offset, block_values = decode_for_interleaved(data, offset, previous_value)
            else:
                offset, block_values = decode_for(data, offset, block_count, previous_value)
        elif block_type == BLOCK_TYPE_PFOR_VB:
            if interleaved:
                offset, block_values = decode_pfor_vb_interleaved(data, offset, previous_value)
            else:
                offset, block_values = decode_pfor_vb(data, offset, block_count, previous_value)
        elif block_type == BLOCK_TYPE_PFOR_BITMAP:
            if interleaved:
                offset, block_values = decode_pfor_bitmap_interleaved(data, offset, previous_value)
            else:
                offset, block_values = decode_pfor_bitmap(data, offset, block_count, previous_value)
        elif block_type == BLOCK_TYPE_CONSTANT:
            offset, block_values = decode_constant(data, offset, block_count, previous_value)
        else:
            message = "unsupported posting list block type {block_type}".format(block_type=block_type)
            raise plocate.errors.PlocateFormatError(message)

        docids.extend(block_values)
        previous_value = block_values[-1]
        index += block_count

    return tuple(docids)
