"""Read and search plocate.db index files."""

import plocate.constants
import plocate.database
import plocate.export
import plocate.search


DEFAULT_DATABASE_PATH = plocate.constants.DEFAULT_DATABASE_PATH
PlocateDatabase = plocate.database.PlocateDatabase
ExportOptions = plocate.export.ExportOptions
SearchOptions = plocate.search.SearchOptions

iter_export_records = plocate.export.iter_export_records
search_database = plocate.search.search_database

__all__ = [
    "DEFAULT_DATABASE_PATH",
    "ExportOptions",
    "PlocateDatabase",
    "SearchOptions",
    "iter_export_records",
    "search_database",
]
