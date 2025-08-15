from fparser.two.Fortran2003 import (
    Expr, 
    Data_Ref, 
    Part_Ref, 
    Actual_Arg_Spec, 
    Parenthesis, 
    Level_2_Expr, 
    Add_Operand, 
    Mult_Operand, 
    Call_Stmt, 
    Assignment_Stmt,
    Int_Literal_Constant,
    Real_Literal_Constant,
    Logical_Literal_Constant,
    Complex_Literal_Constant,
    Intrinsic_Function_Reference,
    Level_2_Unary_Expr,
    Name)
from .....data_models.fortran import (
    SymbolReferenceRead,
    SymbolReferenceWrite,
)
from typing import Literal
from ..utils import is_iterable, get_name_from_node, get_line_number
from collections import deque

IGNORED_NODES = (
    str,
    Int_Literal_Constant,
    Real_Literal_Constant,
    Logical_Literal_Constant,
    Complex_Literal_Constant,
    Intrinsic_Function_Reference,
    Level_2_Unary_Expr
)
# ----------------------------------------------------------
# 1. 统一引用类构造器
# ----------------------------------------------------------
def _make_ref(name: str,
              line: int,
              access: Literal["read","write"],
              is_part: bool,
              comps: list[str]):
    kwargs = {
        "name": name,
        "line": line,
        "is_part_ref": is_part,
        "component_name": comps or None     # 空列表 -> None
    }
    if access == "read":
        return SymbolReferenceRead(**kwargs)
    return SymbolReferenceWrite(**kwargs)

# ----------------------------------------------------------
# 2. 公共收集函数
# ----------------------------------------------------------
def _collect(node,
             access: Literal["read","write"],
             is_part: bool,
             comps: list[str],
             line_no: int,
             out: list):
    """
    深度优先展开；通过显式栈避免递归。
    栈元素: (ast_node, access, is_part_ref, component_path[list[str]])
    """
    stack: list[tuple] = [(node, access, is_part, comps)]

    while stack:
        nd, acc, part, path = stack.pop()
        if nd is None:
            continue

        # ----------  Name ----------
        if isinstance(nd, Name):
            out.append(_make_ref(get_name_from_node(nd), line_no, acc, part, path))
            continue

        # ---------- Data_Ref ----------
        if isinstance(nd, Data_Ref):
            left, right = nd.children

            # 取 right 的“名字”
            if isinstance(right, Name):
                comp_id = get_name_from_node(right)
                new_part = part                       # 没数组
                # left 继续写/读，前插 component
                stack.append((left, acc, new_part, [comp_id] + path))

            elif isinstance(right, Part_Ref):
                r_base, r_subs = right.children
                comp_id = get_name_from_node(r_base)
                # left 延续，标记 part_ref
                stack.append((left, acc, True or part, [comp_id] + path))
                # 处理下标，全是 read
                for s in r_subs.items:
                    stack.append((s, "read", False, []))
            else:
                # right 还是 Data_Ref；继续向内展开
                stack.append((right, acc, part, path))
                stack.append((left, acc, part, path))
            continue

        # ---------- Part_Ref （顶层 a(i) 或实参内） ----------
        if isinstance(nd, Part_Ref):
            base, subs = nd.children
            stack.append((base, acc, True or part, path))
            for s in subs.items:
                stack.append((s, "read", False, []))
            continue

        # ---------- 其它节点 ----------
        if isinstance(nd, Parenthesis):
            stack.append((nd.children[1], acc, part, path));
            continue
        if isinstance(nd, (Level_2_Expr, Add_Operand, Mult_Operand)):
            stack.append((nd.children[0], "read", False, []))
            stack.append((nd.children[2], "read", False, []))
            continue
        if isinstance(nd, Actual_Arg_Spec):
            stack.append((nd.children[1], "read", False, []))
            continue
        if is_iterable(nd) and not isinstance(nd, IGNORED_NODES):
            for ch in nd.children[::-1]:
                stack.append((ch, "read", False, []))
            continue
        if isinstance(nd, list):
            for ch in nd[::-1]:
                stack.append((ch, "read", False, []))
            continue
        if isinstance(nd, IGNORED_NODES):
            continue

        raise ValueError(f"Unknown node type: {type(nd)}")

# ----------------------------------------------------------
# 3. API 封装
# ----------------------------------------------------------
def from_expression(expr: Expr, line_no: int,
                    access: Literal["read","write"]="read"):
    refs: list = []
    _collect(expr, access, False, [], line_no, refs)
    return refs


def from_designator(designator: object, line_no: int):
    # 左值整体写；内部下标、成员仍按 READ
    refs: list = []
    # 如果 designator 本身就是 Part_Ref，需要额外处理：
    if isinstance(designator, Part_Ref):
        base, subs = designator.children
        # 基变量 WRITE
        _collect(base, "write", True, [], line_no, refs)
        # 下标 READ
        for s in subs.items:
            _collect(s, "read", False, [], line_no, refs)
    else:
        _collect(designator, "write", False, [], line_no, refs)
    return refs


def from_call_stmt(call_stmt: Call_Stmt):
    if call_stmt is None:
        return []
    _, args = call_stmt.items
    line_no = get_line_number(call_stmt)
    refs: list = []
    if args:
        for a in args.items:
            _collect(a, "read", False, [], line_no, refs)
    return refs


def from_assignment_stmt(stmt: Assignment_Stmt):
    if stmt is None:
        return []
    line_no = get_line_number(stmt)
    lhs, rhs = stmt.items[0], stmt.items[2]

    refs: list = []
    refs.extend(from_designator(lhs, line_no))
    refs.extend(from_expression(rhs, line_no, "read"))
    return refs
