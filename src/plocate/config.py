"""Configuration block parsing."""

import dataclasses
import logging

_LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, slots=True)
class ConfigurationEntry:
    """One updatedb configuration variable and its ordered values."""

    name: str
    values: list[str]


def parse_configuration_block(block_bytes: bytes) -> list[ConfigurationEntry]:
    """Parse the NUL-delimited configuration block from a plocate database."""

    entries: list[ConfigurationEntry] = []
    current_name: str | None = None
    current_values: list[str] = []
    index = 0

    # Walk NUL-terminated strings: name, values..., empty string ends each entry.
    while index < len(block_bytes):
        end = block_bytes.find(b"\0", index)
        if end == -1:
            break
        value = block_bytes[index:end].decode("utf-8")
        index = end + 1

        if current_name is None:
            current_name = value
            current_values = []
            continue

        if value == "":
            entries.append(ConfigurationEntry(name=current_name, values=current_values))
            current_name = None
            continue

        current_values.append(value)

    return entries


def configuration_entries_to_mapping(entries: list[ConfigurationEntry]) -> dict[str, list[str]]:
    """Convert parsed configuration entries to a name-to-values mapping."""

    mapping: dict[str, list[str]] = {}
    for entry in entries:
        mapping[entry.name] = entry.values

    return mapping
