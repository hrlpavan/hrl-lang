"""
HRL Abstract Syntax Tree (AST) Node Definitions.
Author: Pavan Kumar Sadashiv (HRL International Pvt. Ltd.)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


@dataclass
class ASTNode:
    line: int = 0
    column: int = 0


# ---------------------------------------------------------
# Expressions
# ---------------------------------------------------------

@dataclass
class ExprNode(ASTNode):
    pass


@dataclass
class LiteralNode(ExprNode):
    value: Any = None
    type_name: str = "Any"


@dataclass
class IdentifierNode(ExprNode):
    name: str = ""


@dataclass
class BinaryOpNode(ExprNode):
    left: ExprNode = field(default_factory=ExprNode)
    op: str = ""
    right: ExprNode = field(default_factory=ExprNode)


@dataclass
class UnaryOpNode(ExprNode):
    op: str = ""
    operand: ExprNode = field(default_factory=ExprNode)


@dataclass
class CallNode(ExprNode):
    callee: ExprNode = field(default_factory=ExprNode)
    args: List[ExprNode] = field(default_factory=list)
    kwargs: Dict[str, ExprNode] = field(default_factory=dict)


@dataclass
class MemberAccessNode(ExprNode):
    target: ExprNode = field(default_factory=ExprNode)
    member: str = ""


@dataclass
class ArrayLiteralNode(ExprNode):
    elements: List[ExprNode] = field(default_factory=list)


@dataclass
class MapLiteralNode(ExprNode):
    entries: List[tuple] = field(default_factory=list)  # (key_expr, val_expr)


@dataclass
class ExecuteExprNode(ExprNode):
    target: ExprNode = field(default_factory=ExprNode)


@dataclass
class SpawnExprNode(ExprNode):
    agent_type: str = ""
    args: List[ExprNode] = field(default_factory=list)


# ---------------------------------------------------------
# Statements
# ---------------------------------------------------------

@dataclass
class StmtNode(ASTNode):
    pass


@dataclass
class LetStmtNode(StmtNode):
    var_name: str = ""
    type_annotation: Optional[str] = None
    value: ExprNode = field(default_factory=ExprNode)


@dataclass
class ReturnStmtNode(StmtNode):
    value: Optional[ExprNode] = None


@dataclass
class IfStmtNode(StmtNode):
    condition: ExprNode = field(default_factory=ExprNode)
    then_branch: List[StmtNode] = field(default_factory=list)
    else_branch: List[StmtNode] = field(default_factory=list)


@dataclass
class WhileStmtNode(StmtNode):
    condition: ExprNode = field(default_factory=ExprNode)
    body: List[StmtNode] = field(default_factory=list)


@dataclass
class VerifyStmtNode(StmtNode):
    condition: ExprNode = field(default_factory=ExprNode)
    error_message: Optional[str] = None


@dataclass
class EmitStmtNode(StmtNode):
    event_name: str = ""
    payload: ExprNode = field(default_factory=ExprNode)


@dataclass
class ExpressionStmtNode(StmtNode):
    expr: ExprNode = field(default_factory=ExprNode)


# ---------------------------------------------------------
# Declarations (Language Primitives)
# ---------------------------------------------------------

@dataclass
class ParamNode(ASTNode):
    name: str = ""
    type_name: str = "Any"
    default_value: Optional[ExprNode] = None


@dataclass
class ToolDefNode(ASTNode):
    name: str = ""
    params: List[ParamNode] = field(default_factory=list)
    return_type: str = "Any"
    guards: List[ExprNode] = field(default_factory=list)
    timeout_ms: Optional[int] = None
    docstring: str = ""


@dataclass
class SubgoalNode(ASTNode):
    name: str = ""
    description: str = ""
    acceptance_criteria: Optional[ExprNode] = None


@dataclass
class GoalDefNode(ASTNode):
    name: str = ""
    params: List[ParamNode] = field(default_factory=list)
    invariants: List[ExprNode] = field(default_factory=list)
    subgoals: List[SubgoalNode] = field(default_factory=list)


@dataclass
class ManagerDefNode(ASTNode):
    name: str = ""
    model_name: str = "GeminiPro"
    dilation: int = 8
    goals: List[GoalDefNode] = field(default_factory=list)


@dataclass
class PolicyHandlerNode(ASTNode):
    subgoal_name: str = ""
    body: List[StmtNode] = field(default_factory=list)


@dataclass
class WorkerDefNode(ASTNode):
    name: str = ""
    manager_name: str = ""
    model_name: str = "GeminiFlash"
    tools: List[str] = field(default_factory=list)
    policy_handlers: List[PolicyHandlerNode] = field(default_factory=list)


@dataclass
class PipelineDefNode(ASTNode):
    name: str = ""
    params: List[ParamNode] = field(default_factory=list)
    return_type: str = "Any"
    body: List[StmtNode] = field(default_factory=list)


@dataclass
class ImportNode(ASTNode):
    module_path: str = ""
    alias: Optional[str] = None


@dataclass
class ModuleNode(ASTNode):
    name: str = "Main"
    imports: List[ImportNode] = field(default_factory=list)
    tools: List[ToolDefNode] = field(default_factory=list)
    managers: List[ManagerDefNode] = field(default_factory=list)
    workers: List[WorkerDefNode] = field(default_factory=list)
    pipelines: List[PipelineDefNode] = field(default_factory=list)
