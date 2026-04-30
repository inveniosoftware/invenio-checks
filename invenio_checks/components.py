# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record service component."""

import functools

from flask import current_app
from invenio_db.uow import ModelCommitOp, ModelDeleteOp
from invenio_drafts_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.errors import ValidationErrorGroup
from invenio_requests.records.api import Request
from invenio_requests.records.models import RequestMetadata

from .api import ChecksAPI
from .models import CheckConfig, CheckRun


def toggle_on_feature_flag(config_key):
    """Class decorator to apply to all direct public methods."""

    def decorator(cls):
        def _wrap(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not current_app.config.get(config_key, False):
                    return
                return func(*args, **kwargs)

            return wrapper

        # Using `vars` instead of `dir` to get direct methods from this class only (and not the base class ones).
        for attr_name in vars(cls):
            attr_value = getattr(cls, attr_name)
            if callable(attr_value) and not attr_name.startswith("_"):
                setattr(cls, attr_name, _wrap(attr_value))
        return cls

    return decorator


@toggle_on_feature_flag("CHECKS_ENABLED")
class ChecksComponent(ServiceComponent):
    """Checks component."""

    def read_draft(self, identity, draft=None, errors=None, **kwargs):
        """Fetch checks on draft read."""
        errors = errors or []
        runs = ChecksAPI.get_runs(draft)
        errors.extend(ChecksAPI.extract_run_errors(runs))

    def update_draft(self, identity, data=None, record=None, errors=None, **kwargs):
        """Run checks on draft update."""
        draft = record  # rename for clarity

        # Take into account already included communities
        community_ids = self._get_record_communities(draft)

        # Take into account configs from past check runs (could be inclusion requests)
        past_runs = ChecksAPI.get_runs(draft)
        for run in past_runs:
            community_ids.add(str(run.config.community_id))

        updated_runs = []
        configs = ChecksAPI.get_configs(community_ids, target_type="record")
        for config in configs:
            run = ChecksAPI.run_check(config, draft, self.uow)
            if run:
                updated_runs.append(run)

        errors.extend(ChecksAPI.extract_run_errors(updated_runs))

    def new_version(self, identity, draft=None, record=None, **kwargs):
        """Initialize checks on new version creation."""
        # Take into account already included communities
        community_ids = self._get_record_communities(draft)

        # Take into account configs from past check runs (could be inclusion requests)
        # from the latest published record version
        record_runs = ChecksAPI.get_runs(record)
        for run in record_runs:
            community_ids.add(str(run.config.community_id))

        configs = ChecksAPI.get_configs(community_ids, target_type="record")
        for config in configs:
            # Run checks on the new version draft
            ChecksAPI.run_check(config, draft, self.uow)

    def edit(self, identity, draft=None, record=None, **kwargs):
        """Run checks on draft edit."""
        # Take into account already included communities
        community_ids = self._get_record_communities(draft)

        # Take into account configs from past check runs (could be inclusion requests).
        # NOTE: we want both draft and record runs here, since we just care about
        # getting all the involved community IDs.
        past_runs = CheckRun.query.filter_by(record_id=record.id).all()
        for run in past_runs:
            community_ids.add(str(run.config.community_id))

        # Run checks for all relevant communities
        configs = ChecksAPI.get_configs(community_ids, target_type="record")
        for config in configs:
            # Run checks on the draft
            ChecksAPI.run_check(config, draft, self.uow)

    def publish(self, identity, draft=None, record=None, **kwargs):
        """Create or update record runs based on draft runs."""
        draft_runs = ChecksAPI.get_runs(draft)

        # Check if there are any check runs with errors
        run_errors = ChecksAPI.extract_run_errors(draft_runs)
        error_severity_errors = [e for e in run_errors if e.get("severity") == "error"]
        if error_severity_errors:
            raise ValidationErrorGroup(errors=error_severity_errors)

        # If no errors, we clean up and convert the draft runs to record runs.
        for draft_run in draft_runs:
            record_run = CheckRun.query.filter_by(
                config_id=draft_run.config_id,
                record_id=record.id,
                is_draft=False,
            ).one_or_none()

            if record_run:  # If the run already exists, update it
                record_run.start_time = draft_run.start_time
                record_run.end_time = draft_run.end_time

                record_run.status = draft_run.status
                record_run.state = draft_run.state
                record_run.result = draft_run.result

                # Delete the draft run
                self.uow.register(ModelDeleteOp(draft_run))
            else:  # Otherwise, "convert" the draft run to a record run
                draft_run.is_draft = False
                record_run = draft_run

            record_run.revision_id = record.revision_id
            self.uow.register(ModelCommitOp(record_run))

    def delete_draft(self, identity, draft=None, record=None, force=False, **kwargs):
        """Delete all draft runs."""
        draft_runs = ChecksAPI.get_runs(draft)
        for draft_run in draft_runs:
            self.uow.register(ModelDeleteOp(draft_run))

    def submit_record(self, identity, data=None, record=None, **kwargs):
        """Check for run errors in draft review submission."""
        draft = record  # rename for clarity

        draft_runs = ChecksAPI.get_runs(draft)
        run_errors = ChecksAPI.extract_run_errors(draft_runs)
        error_severity_errors = [e for e in run_errors if e.get("severity") == "error"]
        if error_severity_errors:
            raise ValidationErrorGroup(errors=error_severity_errors)

    def _get_record_communities(self, record_or_draft):
        """Get community IDs from the record or draft."""
        community_ids = set()
        for community in record_or_draft.parent.communities:
            community_ids.add(str(community.id))
            if community.parent:
                community_ids.add(str(community.parent.id))
        return community_ids


@toggle_on_feature_flag(config_key="CHECKS_SUBCOMMUNITY_ENABLED")
class SubcommunityChecksComponent(ServiceComponent):
    """Subcommunity checks component."""

    def update(self, identity, data=None, record=None, **kwargs):
        """Rerun checks if this community is a subcommunity."""
        open_requests = RequestMetadata.query.filter(
            RequestMetadata.json.op('->>')('type') == "subcommunity",
            RequestMetadata.json.op('->>')('status') == "submitted",
            RequestMetadata.json['topic'].op('->>')('community') == str(record.id),
        ).all()
        if not open_requests:
            return

        for req_model in open_requests:
            request = Request.get_record(req_model.id)
            parent = request.receiver.resolve()

            configs = ChecksAPI.get_configs([parent.id], "community")

            for config in configs:
                if config.params.get("sync", True):
                    ChecksAPI.run_check(config, record, self.uow)


@toggle_on_feature_flag(config_key="CHECKS_SUBCOMMUNITY_ENABLED")
class CommunityMemberChecksComponent(ServiceComponent):
    """Reruns membership checks when community members change."""

    def _rerun_membership_checks(self, member, uow):
        community_id = member.community_id
        if not community_id:
            return

        open_requests = RequestMetadata.query.filter(
            RequestMetadata.json.op('->>')('type') == "subcommunity",
            RequestMetadata.json.op('->>')('status') == "submitted",
            RequestMetadata.json['topic'].op('->>')('community') == str(community_id),
        ).all()
        if not open_requests:
            return

        for req_model in open_requests:
            request = Request.get_record(req_model.id)
            parent = request.receiver.resolve()
            subcommunity = request.topic.resolve()

            config = CheckConfig.query.filter(
                CheckConfig.community_id == parent.id,
                CheckConfig.enabled.is_(True),
                CheckConfig.check_id == "subcommunity_member",
                CheckConfig.params["scope"].as_string() == "community",
            ).one_or_none()

            ChecksAPI.run_check(config, subcommunity, uow)

    def accept_invite(self, identity, record=None, **kwargs):
        """Rerun on invitation accepted."""
        self._rerun_membership_checks(record, self.uow)

    def members_update(self, identity, record=None, **kwargs):
        """Rerun on role change."""
        self._rerun_membership_checks(record, self.uow)

    def members_delete(self, identity, record=None, **kwargs):
        """Rerun on member removal."""
        self._rerun_membership_checks(record, self.uow)
