from datetime import datetime

from flask import current_app, g
from invenio_communities.proxies import current_communities
from invenio_db import db
from invenio_rdm_records.requests import CommunityInclusion, CommunitySubmission
from invenio_requests.proxies import current_requests_service
from invenio_search.engine import dsl
from sqlalchemy import case

from .models import CheckConfig, CheckRun, CheckRunStatus
from .proxies import current_checks_registry


class CheckRunAPI:
    """Class for managing check runs."""

    @classmethod
    def delete_check_run(cls, record_uuid, is_draft):
        """Delete all draft check runs for the record."""
        CheckRun.query.filter_by(record_id=record_uuid, is_draft=is_draft).delete()
        try:
            db.session.commit()
        except Exception:
            current_app.logger.exception(
                "Failed to delete draft run for record %s", record_uuid
            )
            db.session.rollback()
            raise

    @classmethod
    def resolve_checks(cls, record_uuid, record, request, community=None):
        """Resolve the checks for this draft/record related to the community and the request."""
        enabled = current_app.config.get("CHECKS_ENABLED", False)
        if not enabled:
            return None

        request_type = request.get("type")
        is_draft_submission = request_type == CommunitySubmission.type_id
        is_record_inclusion = request_type == CommunityInclusion.type_id

        if not is_draft_submission and not is_record_inclusion:
            return None

        if not record_uuid:
            return None

        if not community:
            community_uuid = request.get("receiver", {}).get("community")
            if not community_uuid:
                return None
            community = current_communities.service.read(
                id_=community_uuid, identity=g.identity
            )

        communities = []
        community_parent_id = community.to_dict().get("parent", {}).get("id")
        if community_parent_id:
            communities.append(community_parent_id)
        communities.append(community.id)

        check_configs = (
            CheckConfig.query.filter(CheckConfig.community_id.in_(communities))
            .order_by(
                case((CheckConfig.community_id == communities[0], 0), else_=1),
                CheckConfig.check_id,
            )
            .all()
        )
        if not check_configs:
            return None

        has_draft_run = record.data["is_draft"] or record._record.has_draft

        check_config_ids = [cfg.id for cfg in check_configs]
        check_runs = CheckRun.query.filter(
            CheckRun.config_id.in_(check_config_ids),
            CheckRun.record_id == record_uuid,
            CheckRun.is_draft == has_draft_run,
        ).all()

        latest_checks = {}
        for run in check_runs:
            latest_checks.setdefault(run.config_id, run)

        return [latest_checks[cid] for cid in check_config_ids if cid in latest_checks]

    @classmethod
    def get_community_ids(cls , record, identity):
        """Extract all relevant community IDs related to the record."""
        community_ids = set()

        # Check draft review request
        if record.parent.review:
            community = record.parent.review.receiver.resolve()
            community_ids.add(str(community.id))
            community_parent_id = community.get("parent", {}).get("id")
            if community_parent_id:
                community_ids.add(community_parent_id)

        # Check inclusion requests
        results = current_requests_service.search(
            identity,
            extra_filter=dsl.query.Bool(
                "must",
                must=[
                    dsl.Q("term", **{"type": "community-inclusion"}),
                    dsl.Q("term", **{"topic.record": record.pid.pid_value}),
                    dsl.Q("term", **{"is_open": True}),
                ],
            ),
        )
        for result in results:
            community_id = result.get("receiver", {}).get("community")
            if community_id:
                community_ids.add(community_id)
                community = current_communities.service.read(
                    id_=community_id, identity=identity
                )
                community_parent_id = community.to_dict().get("parent", {}).get("id")
                if community_parent_id:
                    community_ids.add(community_parent_id)

        # Check already included communities
        for community in record.parent.communities:
            community_ids.add(str(community.id))
            community_parent_id = community.get("parent", {}).get("id")
            if community_parent_id:
                community_ids.add(community_parent_id)

        return community_ids

    @classmethod
    def get_check_configs_from_communities(cls, community_ids):
        """Retrieve check configurations for the given community IDs."""
        return CheckConfig.query.filter(
            CheckConfig.community_id.in_(community_ids)
        ).all()

    @classmethod
    def run_checks(cls, identity, is_draft, record=None, errors=None, **kwargs):
        """Handler to run checks.

        Args:
            identity: The identity of the user or system running the checks.
            record: The record to run checks against.
            errors: A list to append any errors found.
            community_ids: A set of community IDs to consider for running checks.
        """
        if not current_app.config.get("CHECKS_ENABLED", False):
            return

        community_ids = CheckRunAPI.get_community_ids(record, identity)

        all_check_configs = CheckRunAPI.get_check_configs_from_communities(community_ids)

        for check_config in all_check_configs:
            try:
                check_cls = current_checks_registry.get(check_config.check_id)
                start_time = datetime.utcnow()
                res = check_cls().run(record, check_config)
                if not res.sync:
                    continue

                check_errors = [
                    {
                        **error,
                        "context": {"community": check_config.community_id},
                    }
                    for error in res.errors
                ]
                errors.extend(check_errors)

                latest_check = (
                    CheckRun.query.filter(
                        CheckRun.config_id == check_config.id,
                        CheckRun.record_id == record.id,
                        CheckRun.is_draft.is_(is_draft),
                    )
                    .first()
                )

                if not latest_check:
                    latest_check = CheckRun(
                        config_id=check_config.id,
                        record_id=record.id,
                        is_draft=is_draft,
                        revision_id=record.revision_id,
                        start_time=start_time,
                        end_time=datetime.utcnow(),
                        status=CheckRunStatus.COMPLETED,
                        state="",
                        result=res.to_dict(),
                    )
                else:
                    latest_check.is_draft = is_draft
                    latest_check.revision_id = record.revision_id
                    latest_check.start_time = start_time
                    latest_check.end_time = datetime.utcnow()
                    latest_check.result = res.to_dict()

                db.session.add(latest_check)
                db.session.commit()

            except Exception:
                current_app.logger.exception(
                    "Error running check on record",
                    extra={
                        "record_id": str(record.id),
                        "check_config_id": str(check_config.id),
                    },
                )
