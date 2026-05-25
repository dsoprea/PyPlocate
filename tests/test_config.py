from plocate_db.config import configuration_entries_to_mapping, parse_configuration_block


def test_parse_configuration_block():
    block = b"prune_bind_mounts\0" + b"0\0\0" + b"prunepaths\0/tmp\0/var/cache\0\0"
    entries = parse_configuration_block(block)

    assert len(entries) == 2
    assert entries[0].name == "prune_bind_mounts"
    assert entries[0].values == ["0"]
    assert entries[1].name == "prunepaths"
    assert entries[1].values == ["/tmp", "/var/cache"]


def test_configuration_entries_to_mapping():
    block = b"prunefs\009P\00NFS\00\00"
    mapping = configuration_entries_to_mapping(parse_configuration_block(block))
    assert mapping == {"prunefs": ["9P", "NFS"]}
