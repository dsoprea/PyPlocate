"""Read and search plocate.db index files."""

import plocate.database
import plocate.export
import plocate.search


PlocateDatabase = plocate.database.PlocateDatabase
ExportOptions = plocate.export.ExportOptions
SearchOptions = plocate.search.SearchOptions

iter_export_records = plocate.export.iter_export_records
search_database = plocate.search.search_database

__all__ = [
    "ExportOptions",
    "PlocateDatabase",
    "SearchOptions",
    "iter_export_records",
    "search_database",
]
