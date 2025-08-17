# core/models/enums.py

from enum import Enum

class ProjectFSMStatus(str, Enum):
    """定义项目整体的有限状态机状态"""
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZED = "INITIALIZED"
    EXTRACTED = "EXTRACTED"
    TRANSFORMED = "TRANSFORMED"
    LOADED = "LOADED"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"

class FileStatus(str, Enum):
    """定义单个源文件在其处理流水线中的状态"""
    PENDING = "PENDING"          # 待处理
    EXTRACTED = "EXTRACTED"        # AST 提取成功
    TRANSFORMED = "TRANSFORMED"      # JSON 转换成功
    LOADED = "LOADED"            # 已加载至目标数据库
    FAILED_EXTRACT = "FAILED_EXTRACT" # 提取失败
    FAILED_TRANSFORM = "FAILED_TRANSFORM" # 转换失败
    FAILED_LOAD = "FAILED_LOAD"      # 加载失败