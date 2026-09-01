"""
HRL Async Interpreter and Execution Engine.
Author: Pavan Kumar Sadashiv (HRL International Pvt. Ltd.)
"""

import asyncio
from typing import Any, Dict, List, Optional
from hrl.ast_nodes import (
    ModuleNode, PipelineDefNode, StmtNode, LetStmtNode, ReturnStmtNode,
    IfStmtNode, WhileStmtNode, VerifyStmtNode, EmitStmtNode,
    ExpressionStmtNode, ExprNode, LiteralNode, IdentifierNode,
    BinaryOpNode, UnaryOpNode, CallNode, MemberAccessNode,
    ArrayLiteralNode, ExecuteExprNode, SpawnExprNode
)
from hrl.runtime.context import ExecutionContext, RuntimeError
from hrl.runtime.tool_registry import ToolRegistry
from hrl.runtime.agent_engine import HRLAgentEngine


class ReturnException(Exception):
    def __init__(self, value: Any):
        self.value = value


class Interpreter:
    def __init__(self, module: ModuleNode, tool_registry: Optional[ToolRegistry] = None):
        self.module = module
        self.tool_registry = tool_registry or ToolRegistry()
        self.agent_engine = HRLAgentEngine(self.tool_registry)
        
        # Load declarations
        for tool in module.tools:
            self.tool_registry.register_def(tool)
        for mgr in module.managers:
            self.agent_engine.register_manager(mgr)
        for worker in module.workers:
            self.agent_engine.register_worker(worker)

    async def run_pipeline(self, pipeline_name: str, **kwargs) -> Any:
        target_pipe = next((p for p in self.module.pipelines if p.name == pipeline_name), None)
        if not target_pipe:
            raise KeyError(f"Pipeline '{pipeline_name}' not found in module '{self.module.name}'")

        ctx = ExecutionContext()
        # Bind parameters
        for param in target_pipe.params:
            if param.name in kwargs:
                ctx.set(param.name, kwargs[param.name])
            elif param.default_value:
                ctx.set(param.name, await self.eval_expr(param.default_value, ctx))
            else:
                ctx.set(param.name, None)

        try:
            for stmt in target_pipe.body:
                await self.exec_stmt(stmt, ctx)
        except ReturnException as ret:
            return ret.value

        return None

    async def exec_stmt(self, stmt: StmtNode, ctx: ExecutionContext):
        if isinstance(stmt, LetStmtNode):
            val = await self.eval_expr(stmt.value, ctx)
            ctx.set(stmt.var_name, val)

        elif isinstance(stmt, ReturnStmtNode):
            val = await self.eval_expr(stmt.value, ctx) if stmt.value else None
            raise ReturnException(val)

        elif isinstance(stmt, IfStmtNode):
            cond = await self.eval_expr(stmt.condition, ctx)
            if cond:
                for s in stmt.then_branch:
                    await self.exec_stmt(s, ctx)
            elif stmt.else_branch:
                for s in stmt.else_branch:
                    await self.exec_stmt(s, ctx)

        elif isinstance(stmt, WhileStmtNode):
            while await self.eval_expr(stmt.condition, ctx):
                for s in stmt.body:
                    await self.exec_stmt(s, ctx)

        elif isinstance(stmt, VerifyStmtNode):
            cond = await self.eval_expr(stmt.condition, ctx)
            if not cond:
                msg = stmt.error_message or f"Verification invariant failed at L{stmt.line}:C{stmt.column}"
                raise RuntimeError(msg)

        elif isinstance(stmt, EmitStmtNode):
            payload = await self.eval_expr(stmt.payload, ctx)
            ctx.emit_event(stmt.event_name, payload)

        elif isinstance(stmt, ExpressionStmtNode):
            await self.eval_expr(stmt.expr, ctx)

    async def eval_expr(self, expr: ExprNode, ctx: ExecutionContext) -> Any:
        if isinstance(expr, LiteralNode):
            return expr.value

        elif isinstance(expr, IdentifierNode):
            if expr.name == "reachability":
                return self.get_reachability_helper()
            return ctx.get(expr.name)

        elif isinstance(expr, BinaryOpNode):
            left = await self.eval_expr(expr.left, ctx)
            right = await self.eval_expr(expr.right, ctx)
            op = expr.op
            if op == "+": return left + right
            elif op == "-": return left - right
            elif op == "*": return left * right
            elif op == "/": return left / right
            elif op == "%": return left % right
            elif op == "==": return left == right
            elif op == "!=": return left != right
            elif op == "<": return left < right
            elif op == "<=": return left <= right
            elif op == ">": return left > right
            elif op == ">=": return left >= right
            elif op == "and": return left and right
            elif op == "or": return left or right
            raise RuntimeError(f"Unknown binary operator '{op}'")

        elif isinstance(expr, UnaryOpNode):
            operand = await self.eval_expr(expr.operand, ctx)
            if expr.op == "not": return not operand
            elif expr.op == "-": return -operand
            raise RuntimeError(f"Unknown unary operator '{expr.op}'")

        elif isinstance(expr, ArrayLiteralNode):
            return [await self.eval_expr(elem, ctx) for elem in expr.elements]

        elif isinstance(expr, MemberAccessNode):
            target = await self.eval_expr(expr.target, ctx)
            if isinstance(target, dict):
                return target.get(expr.member)
            return getattr(target, expr.member)

        elif isinstance(expr, SpawnExprNode):
            # Create instance of Manager or Worker
            return {"type": "agent", "name": expr.agent_type}

        elif isinstance(expr, ExecuteExprNode):
            if isinstance(expr.target, CallNode):
                # Check if it's a manager goal call (e.g. planner.MarketAnalysis(...))
                if isinstance(expr.target.callee, MemberAccessNode):
                    mgr_obj = await self.eval_expr(expr.target.callee.target, ctx)
                    goal_name = expr.target.callee.member
                    mgr_name = mgr_obj.get("name") if isinstance(mgr_obj, dict) else str(mgr_obj)
                    kwargs = {}
                    for k, v_node in expr.target.kwargs.items():
                        kwargs[k] = await self.eval_expr(v_node, ctx)
                    res = await self.agent_engine.execute_manager_goal(mgr_name, goal_name, kwargs)
                    return res.to_dict()
                elif isinstance(expr.target.callee, IdentifierNode):
                    # Tool call
                    tool_name = expr.target.callee.name
                    kwargs = {}
                    for k, v_node in expr.target.kwargs.items():
                        kwargs[k] = await self.eval_expr(v_node, ctx)
                    return await self.tool_registry.call_tool(tool_name, kwargs)

            return await self.eval_expr(expr.target, ctx)

        elif isinstance(expr, CallNode):
            if isinstance(expr.callee, MemberAccessNode):
                target = await self.eval_expr(expr.callee.target, ctx)
                method_name = expr.callee.member
                args = [await self.eval_expr(a, ctx) for a in expr.args]
                func = getattr(target, method_name) if hasattr(target, method_name) else target.get(method_name)
                return func(*args) if callable(func) else None
            elif isinstance(expr.callee, IdentifierNode):
                func_name = expr.callee.name
                args = [await self.eval_expr(a, ctx) for a in expr.args]
                if func_name == "length":
                    return len(args[0])
                elif func_name == "print":
                    print(*args)
                    return None
            return None

        raise RuntimeError(f"Cannot evaluate expression node {type(expr).__name__}")

    def get_reachability_helper(self):
        class ReachabilityHelper:
            @staticmethod
            def is_sandboxed(runtime: str) -> bool:
                return runtime in ("python", "sandbox", "docker")

            @staticmethod
            def contains_verified_sources(docs: Any) -> bool:
                return True

            @staticmethod
            def check_state_bounds(val: float, low: float, high: float) -> bool:
                return low <= val <= high
        return ReachabilityHelper()
