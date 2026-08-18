..
    SPDX-FileCopyrightText: 2025-2026 CERN.
    SPDX-FileCopyrightText: 2026 Graz University of Technology.
    SPDX-FileCopyrightText: 2026 TU Wien.
    SPDX-License-Identifier: MIT

Changes
=======

Version v12.0.1 (released 2026-08-18)

- fix(components): use past check runs to rerun

Version v12.0.0 (released 2026-08-12)

- feat(checks): run checks asynchronously via Celery, with a ``sync`` flag on ``Check`` to keep a check inline. Runs go through PENDING/RUNNING states, are retried on failure, marked ERROR after max retries, and ``cleanup_stale_check_runs`` fails runs whose worker never came back (``CHECKS_RUN_STALE_AFTER``).
- fix(checks): handle concurrent check runs across publish and edit, so a check still running at publish time lands on the published record and records no longer become uneditable.
- feat(checks): support subcommunity checks (``CHECKS_SUBCOMMUNITY_ENABLED``), including a member check component and filtering of check runs by community or parent community.
- feat(checks): allow manual re-runs of a check via ``allow_rerun``, with a per-check ``can_rerun`` permission and ``should_rerun`` to decide whether an existing run can be reused.
- feat(checks): add a ``CheckTarget`` registry and ``target_type``, so checks can run against things other than records.
- feat(rules): allow rules to be skipped when their condition does not hold; skipped results are not displayed.
- feat(checks): add ``hide_parent_checks`` to hide a parent community's checks when only the subcommunity's runs are relevant.
- refactor(ui): show a single icon per check class with the worst severity across its runs, and display async error states.

Version v11.0.2 (released 2026-08-04)

- ci: enable CI for feature branches
- fix(build): include mo files

Version v11.0.1 (released 2026-07-16)

- chore(setup): migrate from setuptools to hatchling
- I18n add translation support for invenio-checks (#49)
- chore(licenses): fix some SPDX license headers

Version v11.0.0 (released 2026-06-18)

- chore(setup): bump dependencies
- fix: don't add None community_id from global check runs to community_ids set
- chore(packaging): exclude .git-blame-ignore-revs from distribution
- chore(git-blame): ignore SPDX license header commit
- chore(licenses): update license headers to use SPDX

Version v10.0.0 (released 2026-06-05)

- chore(setup): bump dependencies

Version v9.0.0 (released 2026-05-29)

- chore(setup): bump dependencies
- fix: migrations for choices
- feat: allow empty community_id for check config

Version v8.2.0 (released 2026-05-05)

- feat(rules): add min/max operators

Version v8.1.0 (released 2026-04-14)

- feat: support metadata check error paths

Version v8.0.1 (released 2026-04-08)

- chore(setup): bump invenio-communities to v26.0.0

Version v8.0.0 (released 2026-04-07)

- chore(setup): bump invenio-drafts-resources to v9.0.0

Version v7.0.0 (released 2026-03-20):

- fix(alembic): add missing revision ID to datetime/UTC migration

Version v6.0.0 (released 2026-03-18)

- installation: bump invenio-communities, invenio-jobs

Version v5.0.0 (released 2026-03-10)

- installation: bump invenio-communities

Version v4.0.0 (released 2026-02-01)

- chore(setup): bump dependencies
- fix(chore): DeprecationWarning stdlib

Version v3.0.0 (released 2025-12-12)

- chore(setup): bump invenio-communities to v22.0.0

Version v2.0.0 (released 2025-09-22)

- installation: bump invenio-communities

Version v1.0.0 (released 2025-08-01)

- setup: bump invenio-communities to v20.0.0

Version v0.6.3 (released 2025-07-17)

- api: fix check run model initialization

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
