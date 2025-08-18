"""Construct :class:`IOCall` domain objects from AST nodes."""

from typing import List
from fparser.two.Fortran2003 import (
    Open_Stmt,
    Close_Stmt,
    Read_Stmt,
    Write_Stmt,
    Print_Stmt,
    Call_Stmt,
    Format,
)
from fpyevolve_core.models.fortran import IOCall, SymbolReferenceRead, SymbolReferenceWrite
from .reference_entry import from_expression, from_designator
from ..utils import get_line_number, is_iterable, get_name_from_node


def from_open_stmt(stmt: Open_Stmt) -> IOCall:
    line_no = get_line_number(stmt)
    refs: List[SymbolReferenceRead] = []
    if stmt is not None:
        spec_list = stmt.items[1]
        if spec_list:
            for spec in spec_list.items:
                kw, expr = spec.items
                if kw and str(kw).upper() == "FMT":
                    continue
                if isinstance(expr, Format):
                    continue
                if expr is not None:
                    expr_refs = from_expression(expr, line_no, access="read")
                    for r in expr_refs or []:
                        if isinstance(r, SymbolReferenceRead):
                            refs.append(r)
    return IOCall(operation="open", line=line_no, args=refs)


def from_close_stmt(stmt: Close_Stmt) -> IOCall:
    line_no = get_line_number(stmt)
    refs: List[SymbolReferenceRead] = []
    if stmt is not None:
        spec_list = stmt.items[1]
        if spec_list:
            for spec in spec_list.items:
                _, expr = spec.items
                if expr is not None:
                    expr_refs = from_expression(expr, line_no, access="read")
                    for r in expr_refs or []:
                        if isinstance(r, SymbolReferenceRead):
                            refs.append(r)
    return IOCall(operation="close", line=line_no, args=refs)


def from_read_stmt(stmt: Read_Stmt) -> IOCall:
    line_no = get_line_number(stmt)
    refs: List[SymbolReferenceWrite] = []
    if stmt is not None:
        ctrl_list = stmt.items[0]
        if ctrl_list:
            for spec in ctrl_list.items:
                kw, expr = spec.items
                if kw and str(kw).upper() == "FMT":
                    continue
                if isinstance(expr, Format):
                    continue
                if expr is not None:
                    # control expressions are read
                    expr_refs = from_expression(expr, line_no, access="read")
        item_list = stmt.items[2]
        if item_list:
            for item in item_list.items:
                refs.extend(from_designator(item, line_no))
    return IOCall(operation="read", line=line_no, args=refs)


def from_write_stmt(stmt: Write_Stmt) -> IOCall:
    line_no = get_line_number(stmt)
    refs: List[SymbolReferenceRead] = []
    if stmt is not None:
        ctrl_list = stmt.items[0]
        if ctrl_list:
            for spec in ctrl_list.items:
                kw, expr = spec.items
                if kw and str(kw).upper() == "FMT":
                    continue
                if isinstance(expr, Format):
                    continue
                if expr is not None:
                    expr_refs = from_expression(expr, line_no, access="read")
                    for r in expr_refs or []:
                        if isinstance(r, SymbolReferenceRead):
                            refs.append(r)
        item_list = stmt.items[1]
        if item_list:
            for item in item_list.items:
                expr_refs = from_expression(item, line_no, access="read")
                for r in expr_refs or []:
                    if isinstance(r, SymbolReferenceRead):
                        refs.append(r)
    return IOCall(operation="write", line=line_no, args=refs)


def from_print_stmt(stmt: Print_Stmt) -> IOCall:
    line_no = get_line_number(stmt)
    refs: List[SymbolReferenceRead] = []
    if stmt is not None:
        item_list = stmt.items[1]
        if item_list:
            for item in item_list.items:
                expr_refs = from_expression(item, line_no, access="read")
                for r in expr_refs or []:
                    if isinstance(r, SymbolReferenceRead):
                        refs.append(r)
    return IOCall(operation="print", line=line_no, args=refs)


def from_mpi_call_stmt(stmt: Call_Stmt) -> IOCall | None:
    name = get_name_from_node(stmt.items[0])
    if not name.upper().startswith("MPI_"):
        return None
    line_no = get_line_number(stmt)
    refs: List[SymbolReferenceRead] = []
    arg_list = stmt.items[1]
    if arg_list:
        for arg in arg_list.items:
            expr_refs = from_expression(arg, line_no, access="read")
            for r in expr_refs or []:
                if isinstance(r, SymbolReferenceRead):
                    refs.append(r)
    return IOCall(operation=name.lower(), line=line_no, args=refs)
