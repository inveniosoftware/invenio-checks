..
    Copyright (C) 2025 CERN.

    Invenio-Checks is free software; you can redistribute it and/or modify
    it under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version v0.6.2 (released 2025-07-14)

- chores: replaced importlib_xyz with importlib

Version v0.6.1 (released 2025-06-24)

- fix: components: fix feature flag application to direct methods only

Version v0.6.0 (released 2025-06-23)

- components: handle error-severity results on publish and draft review submit
- components: refactor feature flag application

Version v0.5.0 (released 2025-06-12)

- models: add index on `CheckRun.record_id`
- requests-ui: add warning in checks tab when there is a draft
- requests-ui: fix checks scoping in Jinja templates
- api: refactor checks lifecycle management
    * Hook-in to all draft lifecycle methods (publish, edit, discard, etc.).
    * Check runs now depend on either existing communities the record/drafts
      is included in, or from community requests having properly initialized
      them.

Version v0.4.0 (released 2025-06-05)

- installation: bump communities and draft-resources
- component: fetch parent community for inclusion requests
- component: improve communities fetching
- alembic: recipes
- models: add missing timestamp columns to CheckConfig

Version v0.3.1 (released 2025-05-20)

- requests-ui: handle multiple check runs of same type
    * Handles rendering of multiple check run results for the metadata
      check type.
    * Uses the first instance of file format checks.

Version v0.3.0 (released 2025-05-16)

- contrib: implement file formats check for open and scientific file formats
- global: pass CheckConfig object when running checks
    * Instead of just passing the `CheckConfig.params` when running a check,
      we now pass the entire object, since the check might want to use other
      fields (e.g. the `CheckConfig.severity`).
- global: move metadata checks to "contrib" directory

Version v0.2.2 (released 2025-03-28)

- views: explanation text in checks requests tab

Version v0.2.1 (released 2025-03-26)

- component: fix null constraint on CheckRun.state

Version v0.2.0 (released 2025-03-26)

- views: checks requests tab templates
- views: register blueprint
- component: use datetime.now with timezone.utc
- services: allow HTML links in description (SanitizedHTML)
- models: use JSONB for PostgreSQL
- ci: use `master` branch of PyPI publish

Version 0.1.0 (2025-03-21)

- Initial public release.
