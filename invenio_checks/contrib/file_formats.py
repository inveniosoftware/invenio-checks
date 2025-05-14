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

import yaml
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
    title: str
    description: str
    errors: list[dict] = field(default_factory=list)
    sync: bool = True
    success: bool = True

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

    default_messages = {
        "closed_format_message": ".{ext} is not a known open or scientific file format.",
        "closed_format_description": "Using closed or proprietary formats hinders reusability and preservation of published files.",
        "title": "All files should be in open or scientific formats",
    }

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
            if data_path.suffix == ".yaml":
                data = yaml.safe_load(f)
            elif data_path.suffix == ".json":
                data = json.load(f)
            else:
                raise ValueError(
                    f"Unsupported file format for known formats data file: {data_path}"
                )
            return FileFormatDatabase.load(data)

    def run(self, record, config: CheckConfig):
        """Run the check against the record's files."""
        params = config.params
        title = params.get("title", self.default_messages["title"])
        closed_format_msg = params.get(
            "closed_format_message",
            self.default_messages["closed_format_message"],
        )
        closed_format_description = params.get(
            "closed_format_description",
            self.default_messages["closed_format_description"],
        )

        result = CheckResult(
            id=self.id,
            title=title,
            # NOTE: We default to this description for now
            description=closed_format_description,
        )
        for file in record.files.values():
            file_ext = Path(file.key).suffix[1:]
            if not file_ext:
                continue

            # TODO: This doesn't handle cases with multi-part extensions (e.g. .tar.gz)
            found_format_ids = self.known_formats.get_by_extension(file_ext)

            # NOTE: For now if we don't have information about the file format, we
            # assume it is a closed format. Later on we can explicitly handle known
            # closed formats and suggest alternatives.
            if not found_format_ids:
                result.errors.append(
                    {
                        "field": f"files.entries.{file.key}",
                        "messages": [closed_format_msg.format(ext=file_ext)],
                        "description": closed_format_description,
                        "severity": config.severity.error_value,
                    }
                )
                continue

        return result
