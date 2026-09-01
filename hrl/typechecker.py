"""
HRL Typechecker & Reachability Safety Analyzer.
Author: Pavan Kumar Sadashiv (HRL International Pvt. Ltd.)
"""

from typing import Dict, Set, List, Optional
from hrl.ast_nodes import (
    ModuleNode, ToolDefNode, ManagerDefNode, WorkerDefNode,
    PipelineDefNode, StmtNode, LetStmtNode, ReturnStmtNode,
    IfStmtNode, WhileStmtNode, VerifyStmtNode, EmitStmtNode,
    ExpressionStmtNode, ExprNode, LiteralNode, IdentifierNode,
    BinaryOpNode, UnaryOpNode, CallNode, MemberAccessNode,
    ArrayLiteralNode, ExecuteExprNode, SpawnExprNode
)


class TypeError(Exception):
    def __init__(self, message: str, line: int = 0, column: int = 0):
        super().__init__(f"TypeError [L{line}:C{column}]: {message}")
        self.message = message
        self.line = line
        self.column = column


class TypeChecker:
    def __init__(self):
        self.tools: Dict[str, ToolDefNode] = {}
        self.managers: Dict[str, ManagerDefNode] = {}
        self.workers: Dict[str, WorkerDefNode] = {}
        self.pipelines: Dict[str, PipelineDefNode] = {}
        self.scopes: List[Dict[str, str]] = []

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        if self.scopes:
            self.scopes.pop()

    def set_var(self, name: str, type_name: str):
        if self.scopes:
            self.scopes[-1][name] = type_name

    def lookup_var(self, name: str) -> Optional[str]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def check(self, module: ModuleNode) -> List[str]:
        """Type checks the HRL module. Returns list of verified diagnostics."""
        diagnostics = []

        # 1. Register all tools
        for tool in module.tools:
            if tool.name in self.tools:
                raise TypeError(f"Duplicate tool declaration '{tool.name}'", tool.line, tool.column)
            self.tools[tool.name] = tool
            diagnostics.append(f"Tool verified: {tool.name}({', '.join(p.name + ': ' + p.type_name for p in tool.params)}) -> {tool.return_type}")

        # 2. Register all managers
        for mgr in module.managers:
            if mgr.name in self.managers:
                raise TypeError(f"Duplicate manager declaration '{mgr.name}'", mgr.line, mgr.column)
            self.managers[mgr.name] = mgr
            
            # Verify goals and subgoals
            for goal in mgr.goals:
                sg_names = set()
                for sg in goal.subgoals:
                    if sg.name in sg_names:
                        raise TypeError(f"Duplicate subgoal '{sg.name}' in goal '{goal.name}'", sg.line, sg.column)
                    sg_names.add(sg.name)
            diagnostics.append(f"Manager verified: {mgr.name} (dilation C={mgr.dilation}, {len(mgr.goals)} goals)")

        # 3. Register and verify workers
        for worker in module.workers:
            if worker.name in self.workers:
                raise TypeError(f"Duplicate worker declaration '{worker.name}'", worker.line, worker.column)
            self.workers[worker.name] = worker

            # If worker is attached to a manager, verify manager exists
            if worker.manager_name:
                if worker.manager_name not in self.managers:
                    raise TypeError(f"Worker '{worker.name}' references undeclared manager '{worker.manager_name}'", worker.line, worker.column)
                target_mgr = self.managers[worker.manager_name]
                
                # Collect all available subgoals from manager
                valid_subgoals = set()
                for goal in target_mgr.goals:
                    for sg in goal.subgoals:
                        valid_subgoals.add(sg.name)

                # Verify policy handlers map to valid subgoals
                for handler in worker.policy_handlers:
                    if handler.subgoal_name not in valid_subgoals:
                        raise TypeError(f"Policy handler references unknown subgoal '{handler.subgoal_name}' on manager '{target_mgr.name}'", handler.line, handler.column)

            # Verify tool bindings
            for t_name in worker.tools:
                if t_name not in self.tools:
                    raise TypeError(f"Worker '{worker.name}' references undeclared tool '{t_name}'", worker.line, worker.column)

            diagnostics.append(f"Worker verified: {worker.name} for {worker.manager_name or 'Independent'} with {len(worker.tools)} tools")

        # 4. Check Pipelines
        for pipe in module.pipelines:
            if pipe.name in self.pipelines:
                raise TypeError(f"Duplicate pipeline declaration '{pipe.name}'", pipe.line, pipe.column)
            self.pipelines[pipe.name] = pipe

            self.push_scope()
            for p in pipe.params:
                self.set_var(p.name, p.type_name)

            for stmt in pipe.body:
                self.check_statement(stmt)
            self.pop_scope()
            diagnostics.append(f"Pipeline verified: {pipe.name}({', '.join(p.name for p in pipe.params)})")

        return diagnostics

    def check_statement(self, stmt: StmtNode):
        if isinstance(stmt, LetStmtNode):
            val_type = self.infer_expr_type(stmt.value)
            declared_type = stmt.type_annotation or val_type
            self.set_var(stmt.var_name, declared_type)

        elif isinstance(stmt, IfStmtNode):
            self.infer_expr_type(stmt.condition)
            self.push_scope()
            for s in stmt.then_branch: self.check_statement(s)
            self.pop_scope()
            if stmt.else_branch:
                self.push_scope()
                for s in stmt.else_branch: self.check_statement(s)
                self.pop_scope()

        elif isinstance(stmt, WhileStmtNode):
            self.infer_expr_type(stmt.condition)
            self.push_scope()
            for s in stmt.body: self.check_statement(s)
            self.pop_scope()

        elif isinstance(stmt, VerifyStmtNode):
            self.infer_expr_type(stmt.condition)

        elif isinstance(stmt, ExpressionStmtNode):
            self.infer_expr_type(stmt.expr)

    def infer_expr_type(self, expr: ExprNode) -> str:
        if isinstance(expr, LiteralNode):
            return expr.type_name
        elif isinstance(expr, IdentifierNode):
            t = self.lookup_var(expr.name)
            return t or "Any"
        elif isinstance(expr, BinaryOpNode):
            lt = self.infer_expr_type(expr.left)
            rt = self.infer_expr_type(expr.right)
            if expr.op in ("==", "!=", "<", "<=", ">", ">=", "and", "or"):
                return "Bool"
            return lt if lt != "Any" else rt
        elif isinstance(expr, UnaryOpNode):
            if expr.op == "not": return "Bool"
            return self.infer_expr_type(expr.operand)
        elif isinstance(expr, ExecuteExprNode):
            return "ExecutionResult"
        elif isinstance(expr, SpawnExprNode):
            return f"Agent<{expr.agent_type}>"
        elif isinstance(expr, ArrayLiteralNode):
            return "Array<Any>"
        elif isinstance(expr, CallNode):
            return "Any"
        return "Any"
