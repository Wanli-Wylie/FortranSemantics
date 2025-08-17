from __future__ import annotations
import re

MODULE_NAME_PATTERN = r"[A-Za-z_]\w*"
MODULE_DECL_ID_PATTERN = r"[A-Za-z_]\w*"
MODULE_DECL_ID_REGEX = re.compile(
    rf"^\(module\)(?P<module_name>{MODULE_NAME_PATTERN})"
    rf"->\(declaration\)(?P<declaration_name>{MODULE_DECL_ID_PATTERN})$"
)


MODULE_ID_REGEX = re.compile(rf"^\(module\)(?P<module_name>{MODULE_NAME_PATTERN})$")

REFERENCE_TYPE_PATTERN = r"(?:read|write|call|part_ref)"
REFERENCE_NAME_PATTERN = r"[A-Za-z_]\w*"
MODULE_SYMBOL_REF_ID_REGEX = re.compile(
    rf"^\(module\)(?P<module_name>{MODULE_NAME_PATTERN})"
    rf"->\((?P<reference_type>{REFERENCE_TYPE_PATTERN})\)"
    rf"(?P<reference_name>{REFERENCE_NAME_PATTERN})$"
)
SUBPROGRAM_TYPE_PATTERN = r"(?:subroutine|function)"
SUBPROGRAM_NAME_PATTERN = r"[A-Za-z_]\w*"
SUBPROGRAM_DECL_NAME_PATTERN = r"[A-Za-z_]\w*"

SUBPROGRAM_ID_REGEX = re.compile(
    rf"^\(module\)(?P<module_name>{MODULE_NAME_PATTERN})"
    rf"->\((?P<subprogram_type>{SUBPROGRAM_TYPE_PATTERN})\)"
    rf"(?P<subprogram_name>{SUBPROGRAM_NAME_PATTERN})$"
)

SUBPROGRAM_DECL_ID_REGEX = re.compile(
    rf"^\(module\)(?P<module_name>{MODULE_NAME_PATTERN})"
    rf"->\((?P<subprogram_type>{SUBPROGRAM_TYPE_PATTERN})\)"
    rf"(?P<subprogram_name>{SUBPROGRAM_NAME_PATTERN})"
    rf"->\(declaration\)(?P<declaration_name>{SUBPROGRAM_DECL_NAME_PATTERN})$"
)

SUBPROGRAM_SYMBOL_REF_ID_REGEX = re.compile(
    rf"^\(module\)(?P<module_name>{MODULE_NAME_PATTERN})"
    rf"->\((?P<subprogram_type>{SUBPROGRAM_TYPE_PATTERN})\)"
    rf"(?P<subprogram_name>{SUBPROGRAM_NAME_PATTERN})"
    rf"->\((?P<reference_type>{REFERENCE_TYPE_PATTERN})\)"
    rf"(?P<reference_name>{REFERENCE_NAME_PATTERN})$"
)