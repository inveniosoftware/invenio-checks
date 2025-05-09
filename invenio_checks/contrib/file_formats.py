# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""File formats check."""

import functools
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from flask import current_app

from invenio_checks.base import Check
from invenio_checks.models import CheckConfig
from invenio_checks.utils import classproperty


@dataclass
class FileFormatSpec:
    """Specification for a file format."""

    id: str
    name: str
    extensions: list[str]
    classifiers: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)


class FileFormatDatabase(dict):
    """Database of file formats."""

    def __init__(self, *args, **kwargs):
        """Initialize the database."""
        super().__init__(*args, **kwargs)
        self._ext_lookup = defaultdict(set)

    def get_by_extension(self, ext: str) -> set[str]:
        """Get file format IDs by extension."""
        return self._ext_lookup.get(ext, set())

    @classmethod
    def load(cls, data: dict[str, dict]) -> "FileFormatDatabase":
        """Load file formats from a dictionary."""
        res = cls()
        if not isinstance(data, dict):
            raise ValueError("Invalid data structure in known formats file")
        for ff_id, ff_data in data.items():
            try:
                ff_spec = FileFormatSpec(id=ff_id, **ff_data)
            except TypeError as e:
                raise ValueError(f"Invalid data for file format {ff_id}: {e}")
            res[ff_spec.id] = ff_spec

            # Update the reverse lookup for extensions
            for ext in ff_spec.extensions:
                res._ext_lookup[ext].add(ff_spec.id)
        return res


@dataclass
class CheckResult:
    """Result of a check."""

    id: str
    errors: list[dict] = field(default_factory=list)
    sync: bool = True

    def to_dict(self):
        """Convert the result to a dictionary."""
        return asdict(self)


class FileFormatsCheck(Check):
    """Check for open and scientific file formats.

    This check validates that the files in a record are in open and scientific formats,
    and optionally suggests alternatives for non-compliant formats. It uses a globally
    configurable "master" data file that contains all the known file formats and their
    suggested alternatives.

    Configured instances of this check allow to include or exclude which formats are
    taken into account. By default all formats from the "master" file are included.
    """

    id = "file_formats"
    title = "File formats check"
    description = (
        "Validates that record files are in open and scientific formats, "
        "optionally suggesting alternatives."
    )
    sort_order = 20

    _known_formats_cfg = "CHECKS_FILE_FORMATS_KNOWN_FORMATS_PATH"

    _default_suggest_missing_text = (
        "If you know the format to be open and/or scientific, please contact us to "
        "add it to our database."
    )
    _default_suggest_alternatives_text = (
        "Consider using one of the following formats: {alternatives}."
    )
    _default_closed_format_text = (
        "{key} ({file_format.name}) is not open or scientific."
    )

    @classproperty
    @functools.cache
    def known_formats(cls) -> FileFormatDatabase:
        """Get the known file formats from the data file."""
        data_path = current_app.config.get(cls._known_formats_cfg)
        if data_path is None:
            return FileFormatDatabase()

        data_path = Path(data_path)
        if not data_path.is_absolute():
            # TODO: Maybe we should make "current_app.app_data_path" a thing?
            data_path = Path(current_app.instance_path) / "app_data" / data_path

        if not data_path.exists():
            raise FileNotFoundError(f"Known formats data file not found: {data_path}")

        with data_path.open("r") as f:
            data = json.load(f)
            return FileFormatDatabase.load(data)

    def run(self, record, config: CheckConfig):
        """Run the check against the record's files."""
        # Load config
        params = config.params
        included_formats = set(params.get("include", []))
        excluded_formats = set(params.get("exclude", []))
        suggest_alternatives = params.get("suggest_alternatives", False)
        suggest_alternatives_text = params.get(
            "suggest_alternatives_text",
            self._default_suggest_alternatives_text,
        )
        suggest_missing = params.get("suggest_missing", False)
        suggest_missing_text = params.get(
            "suggest_missing_text",
            self._default_suggest_missing_text,
        )
        closed_format_text = params.get(
            "closed_format_text",
            self._default_closed_format_text,
        )

        result = CheckResult(id=self.id)
        for file in record.files.values():
            file_ext = Path(file.key).suffix[1:]
            if not file_ext:
                continue

            ff_ids: set[str] = self.known_formats.get_by_extension(file_ext)

            # Filter out included/excluded formats based on the configuration
            if included_formats:
                ff_ids &= included_formats
            if excluded_formats:
                ff_ids -= excluded_formats

            if not ff_ids:
                continue

            # Resolve the file format specs
            file_formats = [self.known_formats[ff_id] for ff_id in ff_ids]
            for file_format in file_formats:
                if "closed" in file_format.classifiers:
                    message_lines = []
                    message_lines.append(
                        closed_format_text.format(key=file.key, file_format=file_format)
                    )
                    if suggest_alternatives and file_format.alternatives:
                        alternatives = [
                            self.known_formats[alt_id].name
                            for alt_id in file_format.alternatives
                        ]
                        message_lines.append(
                            suggest_alternatives_text.format(
                                alternatives=", ".join(alternatives)
                            )
                        )

                        # It might be that the file format is not closed, but not in
                        # our database. In that case, we can suggest to add it.
                        if suggest_missing:
                            message_lines.append(suggest_missing_text)

                    result.errors.append(
                        {
                            "field": f"files.entries.{file.key}",
                            "messages": ["\n".join(message_lines)],
                            # TODO: What goes here?
                            # "description": "???",
                            # TODO: Get from config?
                            "severity": config.severity.error_value,
                        },
                    )
        return result
