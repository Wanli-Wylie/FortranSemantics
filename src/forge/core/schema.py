import datetime
import enum
from pathlib import Path
import sqlite3

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Enum as SQLAlchemyEnum,
    Text,
    ForeignKey,
    UniqueConstraint,
    event,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy.engine import Engine

# Enable PRAGMA foreign_keys=ON for SQLite
# This is crucial for enforcing foreign key constraints in SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: sqlite3.Connection, connection_record):
    """Enable foreign key constraints on connection"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# ==============================================================================
# 1. Enums (consistent with Pydantic models)
# ==============================================================================

class ProjectFSMStatus(str, enum.Enum):
    """Define the finite state machine status for the overall project"""
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZED = "INITIALIZED"
    EXTRACTED = "EXTRACTED"
    TRANSFORMED = "TRANSFORMED"
    LOADED = "LOADED"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"

class FileStatus(str, enum.Enum):
    """Define the status of a single source file in its processing pipeline"""
    PENDING = "PENDING"
    EXTRACTED = "EXTRACTED"
    TRANSFORMED = "TRANSFORMED"
    LOADED = "LOADED"
    FAILED_EXTRACT = "FAILED_EXTRACT"
    FAILED_TRANSFORM = "FAILED_TRANSFORM"
    FAILED_LOAD = "FAILED_LOAD"

# ==============================================================================
# 2. SQLAlchemy Schema Definition
# ==============================================================================

# Create base class for all declarative models
class Base(DeclarativeBase):
    pass

class ProjectState(Base):
    """
    SQLAlchemy model: Persist the overall state of a project.
    This table typically has only one row in the database, representing the current project state.
    """
    __tablename__ = 'project_state'

    id = Column(Integer, primary_key=True)
    project_name = Column(String(255), nullable=False, unique=True, doc="Project name")
    fsm_status = Column(
        SQLAlchemyEnum(ProjectFSMStatus, name="project_fsm_status_enum", native_enum=False),
        nullable=False,
        default=ProjectFSMStatus.INITIALIZED,
        doc="Project FSM status"
    )
    forge_version = Column(String(50), nullable=False, doc="Forge version that created this state")
    last_updated = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        doc="Last update time of the state"
    )

    # Relationship: One project state corresponds to multiple file records
    files = relationship(
        "FileRecord",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    def __repr__(self):
        return f"<ProjectState(name='{self.project_name}', status='{self.fsm_status.value}')>"


class FileRecord(Base):
    """
    SQLAlchemy model: Persist the state and metadata of a single source file.
    """
    __tablename__ = 'file_records'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project_state.id'), nullable=False)

    source_path = Column(Text, nullable=False, doc="Source file relative path")
    file_hash = Column(String(64), nullable=False, doc="SHA256 hash value of file content")
    status = Column(
        SQLAlchemyEnum(FileStatus, name="file_status_enum", native_enum=False),
        nullable=False,
        default=FileStatus.PENDING,
        doc="Current processing status of this file"
    )
    ast_path = Column(Text, nullable=True, doc="Relative path of persisted AST artifact")
    json_path = Column(Text, nullable=True, doc="Relative path of persisted JSON artifact")
    last_modified = Column(DateTime, nullable=False, doc="Last modification time in file system")
    last_processed = Column(DateTime, nullable=True, doc="Last time Forge successfully processed this file")
    error_message = Column(Text, nullable=True, doc="Error message when processing fails")

    # Relationship: Multiple file records belong to the same project state
    project = relationship("ProjectState", back_populates="files")

    __table_args__ = (
        # Ensure source file path is unique within the same project
        UniqueConstraint('project_id', 'source_path', name='_project_source_path_uc'),
        # Add indexes for commonly queried fields to improve performance
        Index('ix_file_records_status', 'status'),
        Index('ix_file_records_file_hash', 'file_hash'),
    )

    def __repr__(self):
        return f"<FileRecord(path='{self.source_path}', status='{self.status.value}')>"