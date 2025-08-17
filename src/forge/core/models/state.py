# core/models/state.py

from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import datetime

from .enums import FileStatus, ProjectFSMStatus

class FileRecord(BaseModel):
    """记录单个源文件的完整状态信息"""
    source_path: Path = Field(..., description="相对于项目根目录的源文件路径")
    file_hash: str = Field(..., description="文件内容的SHA256哈希值")
    status: FileStatus = Field(default=FileStatus.PENDING, description="该文件的当前处理状态")
    
    # 产物路径 (Artifact Paths)
    ast_path: Optional[Path] = Field(None, description="持久化的AST产物相对路径")
    json_path: Optional[Path] = Field(None, description="持久化的JSON产物相对路径")
    
    # 元数据 (Metadata)
    last_modified: datetime.datetime = Field(..., description="文件系统中的最后修改时间")
    last_processed: Optional[datetime.datetime] = Field(None, description="Forge最后一次成功处理该文件的时间")
    error_message: Optional[str] = Field(None, description="处理失败时的错误信息")
    
class ProjectState(BaseModel):
    """代表整个项目的当前状态，是状态管理的核心对象"""
    project_name: str = Field(..., description="项目名称，通常是目录名")
    fsm_status: ProjectFSMStatus = Field(default=ProjectFSMStatus.INITIALIZED, description="项目的FSM状态")
    
    # 核心数据：以源文件路径为键，文件记录为值
    files: dict[Path, FileRecord] = Field(default_factory=dict, description="项目中所有被追踪的文件记录")
    
    # 工具元数据
    forge_version: str = Field(..., description="创建或最后更新此状态的Forge版本")
    last_updated: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, description="状态对象最后一次更新的时间")