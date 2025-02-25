import enum
import uuid

from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from sqlalchemy_utils import ChoiceType, Timestamp
from sqlalchemy_utils.types import ChoiceType, UUIDType


class Severity(enum.Enum):
    info = "info"
    warn = "warning"
    error = "error"


class CheckConfig(db.Model):
    __tablename__ = "checks_configs"

    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    community_id = db.Column(
        UUIDType, db.ForeignKey(CommunityMetadata.id), nullable=False
    )
    check_id = db.Column(
        db.String(255), nullable=False
    )  # TODO: Should be enum from ChecksRegistry?
    params = db.Column(db.JSON, nullable=False)
    severity = db.Column(
        ChoiceType(Severity, impl=db.String(1)), nullable=False, default=Severity.error
    )
    enabled = db.Column(db.Boolean, nullable=False, default=True)


class CheckRunStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class CheckRun(db.Model, Timestamp):
    __tablename__ = "checks_runs"

    id = db.Column(db.Integer, primary_key=True)
    config_id = db.Column(UUIDType, db.ForeignKey(CheckConfig.id), nullable=False)
    # FIXME: Should we store a "snapshot" of the config params, severity, etc.?
    #        What if the community changes the config after the check has run?

    record_id = db.Column(UUIDType, nullable=False)
    is_draft = db.Column(db.Boolean, nullable=False, default=False)
    revision_id = db.Column(db.Integer, nullable=False)

    # TODO started/ended times?

    status = db.Column(ChoiceType(CheckRunStatus, impl=db.String(255)), nullable=False)
    state = db.Column(db.JSON, nullable=False)
    result = db.Column(db.JSON, nullable=False)
