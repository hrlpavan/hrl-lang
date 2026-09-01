"""
HRL Parser (Recursive Descent AST Builder).
Author: Pavan Kumar Sadashiv (HRL International Pvt. Ltd.)
"""

from typing import List, Optional, Dict, Any
from hrl.tokens import Token, TokenType
from hrl.ast_nodes import (
    ModuleNode, ImportNode, ToolDefNode, ParamNode, ManagerDefNode,
    GoalDefNode, SubgoalNode, WorkerDefNode, PolicyHandlerNode,
    PipelineDefNode, StmtNode, LetStmtNode, ReturnStmtNode,
    IfStmtNode, WhileStmtNode, VerifyStmtNode, EmitStmtNode,
    ExpressionStmtNode, ExprNode, LiteralNode, IdentifierNode,
    BinaryOpNode, UnaryOpNode, CallNode, MemberAccessNode,
    ArrayLiteralNode, MapLiteralNode, ExecuteExprNode, SpawnExprNode
)


class ParserError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(f"ParserError [L{token.line}:C{token.column}]: {message} (got {token.type.name} {token.value!r})")
        self.token = token
        self.message = message


class Parser:
    def __init__(self, tokens: List[Token], filename: str = "<source>"):
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    def current(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def advance(self) -> Token:
        tok = self.current()
        if self.pos < len(self.tokens):
            self.pos += 1
        return tok

    def check(self, tok_type: TokenType) -> bool:
        return self.current().type == tok_type

    def match(self, *types: TokenType) -> bool:
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False

    def expect(self, tok_type: TokenType, err_msg: str) -> Token:
        if self.check(tok_type):
            return self.advance()
        raise ParserError(err_msg, self.current())

    # ---------------------------------------------------------
    # Entry Point
    # ---------------------------------------------------------

    def parse(self) -> ModuleNode:
        module = ModuleNode(name="Main")
        
        # Optional module declaration: module Foo
        if self.match(TokenType.MODULE):
            name_tok = self.expect(TokenType.IDENTIFIER, "Expected module name identifier")
            module.name = name_tok.value
            module.line = name_tok.line
            module.column = name_tok.column

        while not self.check(TokenType.EOF):
            if self.match(TokenType.IMPORT):
                module.imports.append(self.parse_import())
            elif self.match(TokenType.TOOL):
                module.tools.append(self.parse_tool())
            elif self.match(TokenType.MANAGER):
                module.managers.append(self.parse_manager())
            elif self.match(TokenType.WORKER):
                module.workers.append(self.parse_worker())
            elif self.match(TokenType.PIPELINE):
                module.pipelines.append(self.parse_pipeline())
            elif self.match(TokenType.SEMICOLON):
                continue
            else:
                raise ParserError(f"Unexpected top-level declaration", self.current())

        return module

    # ---------------------------------------------------------
    # Top-Level Declarations
    # ---------------------------------------------------------

    def parse_import(self) -> ImportNode:
        path_tok = self.expect(TokenType.STRING, "Expected string literal for import path")
        alias = None
        if self.match(TokenType.AS):
            alias_tok = self.expect(TokenType.IDENTIFIER, "Expected identifier for import alias")
            alias = alias_tok.value
        self.match(TokenType.SEMICOLON)
        return ImportNode(module_path=path_tok.value, alias=alias, line=path_tok.line, column=path_tok.column)

    def parse_tool(self) -> ToolDefNode:
        name_tok = self.expect(TokenType.IDENTIFIER, "Expected tool name")
        tool = ToolDefNode(name=name_tok.value, line=name_tok.line, column=name_tok.column)

        self.expect(TokenType.LPAREN, "Expected '(' after tool name")
        tool.params = self.parse_params()
        self.expect(TokenType.RPAREN, "Expected ')' after tool parameters")

        if self.match(TokenType.ARROW):
            tool.return_type = self.parse_type_name()

        self.expect(TokenType.LBRACE, "Expected '{' for tool body")
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            if self.match(TokenType.GUARD):
                self.expect(TokenType.COLON, "Expected ':' after 'guard'")
                tool.guards.append(self.parse_expression())
                self.match(TokenType.SEMICOLON)
            elif self.match(TokenType.TIMEOUT):
                self.expect(TokenType.COLON, "Expected ':' after 'timeout'")
                t_tok = self.expect(TokenType.INT, "Expected integer milliseconds for timeout")
                tool.timeout_ms = t_tok.value
                self.match(TokenType.SEMICOLON)
            else:
                raise ParserError(f"Unexpected statement inside tool declaration", self.current())
        self.expect(TokenType.RBRACE, "Expected '}' closing tool body")
        return tool

    def parse_manager(self) -> ManagerDefNode:
        name_tok = self.expect(TokenType.IDENTIFIER, "Expected manager name")
        mgr = ManagerDefNode(name=name_tok.value, line=name_tok.line, column=name_tok.column)

        self.expect(TokenType.LBRACE, "Expected '{' for manager body")
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            if self.match(TokenType.MODEL):
                self.expect(TokenType.COLON, "Expected ':' after 'model'")
                mgr.model_name = self.parse_expression_str()
                self.match(TokenType.SEMICOLON)
            elif self.match(TokenType.DILATION):
                self.expect(TokenType.COLON, "Expected ':' after 'dilation'")
                d_tok = self.expect(TokenType.INT, "Expected integer for macro dilation horizon")
                mgr.dilation = d_tok.value
                self.match(TokenType.SEMICOLON)
            elif self.match(TokenType.GOAL):
                mgr.goals.append(self.parse_goal())
            else:
                raise ParserError("Unexpected statement inside manager body", self.current())
        self.expect(TokenType.RBRACE, "Expected '}' closing manager body")
        return mgr

    def parse_goal(self) -> GoalDefNode:
        name_tok = self.expect(TokenType.IDENTIFIER, "Expected goal name")
        goal = GoalDefNode(name=name_tok.value, line=name_tok.line, column=name_tok.column)

        if self.match(TokenType.LPAREN):
            goal.params = self.parse_params()
            self.expect(TokenType.RPAREN, "Expected ')' after goal parameters")

        self.expect(TokenType.LBRACE, "Expected '{' for goal body")
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            if self.match(TokenType.INVARIANT):
                self.expect(TokenType.COLON, "Expected ':' after 'invariant'")
                goal.invariants.append(self.parse_expression())
                self.match(TokenType.SEMICOLON)
            elif self.match(TokenType.SUBGOAL):
                sg_name = self.expect(TokenType.IDENTIFIER, "Expected subgoal identifier")
                desc = ""
                if self.match(TokenType.ARROW):
                    desc_tok = self.expect(TokenType.STRING, "Expected string description for subgoal")
                    desc = desc_tok.value
                goal.subgoals.append(SubgoalNode(name=sg_name.value, description=desc, line=sg_name.line, column=sg_name.column))
                self.match(TokenType.SEMICOLON)
            else:
                raise ParserError("Unexpected statement inside goal body", self.current())
        self.expect(TokenType.RBRACE, "Expected '}' closing goal body")
        return goal

    def parse_worker(self) -> WorkerDefNode:
        name_tok = self.expect(TokenType.IDENTIFIER, "Expected worker name")
        worker = WorkerDefNode(name=name_tok.value, line=name_tok.line, column=name_tok.column)

        if self.match(TokenType.FOR):
            mgr_tok = self.expect(TokenType.IDENTIFIER, "Expected manager name after 'for'")
            worker.manager_name = mgr_tok.value

        self.expect(TokenType.LBRACE, "Expected '{' for worker body")
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            if self.match(TokenType.MODEL):
                self.expect(TokenType.COLON, "Expected ':' after 'model'")
                worker.model_name = self.parse_expression_str()
                self.match(TokenType.SEMICOLON)
            elif self.match(TokenType.TOOLS):
                self.expect(TokenType.COLON, "Expected ':' after 'tools'")
                self.expect(TokenType.LBRACKET, "Expected '[' for tools list")
                while not self.check(TokenType.RBRACKET) and not self.check(TokenType.EOF):
                    t_tok = self.expect(TokenType.IDENTIFIER, "Expected tool name")
                    worker.tools.append(t_tok.value)
                    if not self.match(TokenType.COMMA):
                        break
                self.expect(TokenType.RBRACKET, "Expected ']' closing tools list")
                self.match(TokenType.SEMICOLON)
            elif self.match(TokenType.POLICY):
                self.expect(TokenType.LBRACE, "Expected '{' for worker policy body")
                while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
                    if self.match(TokenType.ON):
                        self.expect(TokenType.SUBGOAL, "Expected 'subgoal' after 'on'")
                        self.expect(TokenType.LPAREN, "Expected '('")
                        sg_name = self.expect(TokenType.IDENTIFIER, "Expected subgoal name")
                        self.expect(TokenType.RPAREN, "Expected ')'")
                        body = self.parse_block()
                        worker.policy_handlers.append(PolicyHandlerNode(subgoal_name=sg_name.value, body=body, line=sg_name.line, column=sg_name.column))
                    else:
                        raise ParserError("Expected 'on subgoal(...)' inside policy", self.current())
                self.expect(TokenType.RBRACE, "Expected '}' closing policy body")
            else:
                raise ParserError("Unexpected statement inside worker body", self.current())
        self.expect(TokenType.RBRACE, "Expected '}' closing worker body")
        return worker

    def parse_pipeline(self) -> PipelineDefNode:
        name_tok = self.expect(TokenType.IDENTIFIER, "Expected pipeline name")
        pipe = PipelineDefNode(name=name_tok.value, line=name_tok.line, column=name_tok.column)

        self.expect(TokenType.LPAREN, "Expected '(' after pipeline name")
        pipe.params = self.parse_params()
        self.expect(TokenType.RPAREN, "Expected ')'")

        if self.match(TokenType.ARROW):
            pipe.return_type = self.parse_type_name()

        pipe.body = self.parse_block()
        return pipe

    # ---------------------------------------------------------
    # Parameter and Type Parsing
    # ---------------------------------------------------------

    def parse_params(self) -> List[ParamNode]:
        params = []
        while not self.check(TokenType.RPAREN) and not self.check(TokenType.EOF):
            p_name = self.expect(TokenType.IDENTIFIER, "Expected parameter name")
            type_name = "Any"
            if self.match(TokenType.COLON):
                type_name = self.parse_type_name()
            default_val = None
            if self.match(TokenType.ASSIGN):
                default_val = self.parse_expression()
            params.append(ParamNode(name=p_name.value, type_name=type_name, default_value=default_val, line=p_name.line, column=p_name.column))
            if not self.match(TokenType.COMMA):
                break
        return params

    def parse_type_name(self) -> str:
        tok = self.current()
        if tok.type in (TokenType.TYPE_STRING, TokenType.TYPE_INT, TokenType.TYPE_FLOAT,
                         TokenType.TYPE_BOOL, TokenType.TYPE_ARRAY, TokenType.TYPE_MAP,
                         TokenType.TYPE_ANY, TokenType.IDENTIFIER):
            self.advance()
            base_type = str(tok.value)
            if self.match(TokenType.LT):
                inner_type = self.parse_type_name()
                self.expect(TokenType.GT, "Expected '>' closing generic type")
                return f"{base_type}<{inner_type}>"
            return base_type
        raise ParserError(f"Expected type name", tok)

    def parse_expression_str(self) -> str:
        expr = self.parse_expression()
        if isinstance(expr, IdentifierNode):
            return expr.name
        elif isinstance(expr, MemberAccessNode):
            parts = []
            curr = expr
            while isinstance(curr, MemberAccessNode):
                parts.append(curr.member)
                curr = curr.target
            if isinstance(curr, IdentifierNode):
                parts.append(curr.name)
            return ".".join(reversed(parts))
        elif isinstance(expr, LiteralNode):
            return str(expr.value)
        return "Unknown"

    # ---------------------------------------------------------
    # Statements & Blocks
    # ---------------------------------------------------------

    def parse_block(self) -> List[StmtNode]:
        self.expect(TokenType.LBRACE, "Expected '{' to begin block")
        stmts = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
        self.expect(TokenType.RBRACE, "Expected '}' to end block")
        return stmts

    def parse_statement(self) -> StmtNode:
        tok = self.current()
        if self.match(TokenType.LET):
            var_tok = self.expect(TokenType.IDENTIFIER, "Expected variable name")
            type_ann = None
            if self.match(TokenType.COLON):
                type_ann = self.parse_type_name()
            self.expect(TokenType.ASSIGN, "Expected '=' in variable assignment")
            val = self.parse_expression()
            self.match(TokenType.SEMICOLON)
            return LetStmtNode(var_name=var_tok.value, type_annotation=type_ann, value=val, line=var_tok.line, column=var_tok.column)

        elif self.match(TokenType.RETURN):
            val = None
            if not self.check(TokenType.SEMICOLON) and not self.check(TokenType.RBRACE):
                val = self.parse_expression()
            self.match(TokenType.SEMICOLON)
            return ReturnStmtNode(value=val, line=tok.line, column=tok.column)

        elif self.match(TokenType.IF):
            cond = self.parse_expression()
            then_branch = self.parse_block()
            else_branch = []
            if self.match(TokenType.ELSE):
                if self.check(TokenType.IF):
                    else_branch = [self.parse_statement()]
                else:
                    else_branch = self.parse_block()
            return IfStmtNode(condition=cond, then_branch=then_branch, else_branch=else_branch, line=tok.line, column=tok.column)

        elif self.match(TokenType.WHILE):
            cond = self.parse_expression()
            body = self.parse_block()
            return WhileStmtNode(condition=cond, body=body, line=tok.line, column=tok.column)

        elif self.match(TokenType.VERIFY):
            cond = self.parse_expression()
            msg = None
            if self.match(TokenType.COMMA):
                msg_tok = self.expect(TokenType.STRING, "Expected string error message for verify")
                msg = msg_tok.value
            self.match(TokenType.SEMICOLON)
            return VerifyStmtNode(condition=cond, error_message=msg, line=tok.line, column=tok.column)

        elif self.match(TokenType.EMIT):
            event_tok = self.expect(TokenType.IDENTIFIER, "Expected event name identifier for emit")
            self.expect(TokenType.LPAREN, "Expected '(' after emit event name")
            payload = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' closing emit payload")
            self.match(TokenType.SEMICOLON)
            return EmitStmtNode(event_name=event_tok.value, payload=payload, line=event_tok.line, column=event_tok.column)

        else:
            expr = self.parse_expression()
            self.match(TokenType.SEMICOLON)
            return ExpressionStmtNode(expr=expr, line=expr.line, column=expr.column)

    # ---------------------------------------------------------
    # Expressions (Pratt Operator Precedence)
    # ---------------------------------------------------------

    def parse_expression(self) -> ExprNode:
        return self.parse_logical_or()

    def parse_logical_or(self) -> ExprNode:
        left = self.parse_logical_and()
        while self.match(TokenType.OR):
            op = "or"
            right = self.parse_logical_and()
            left = BinaryOpNode(left=left, op=op, right=right, line=left.line, column=left.column)
        return left

    def parse_logical_and(self) -> ExprNode:
        left = self.parse_equality()
        while self.match(TokenType.AND):
            op = "and"
            right = self.parse_equality()
            left = BinaryOpNode(left=left, op=op, right=right, line=left.line, column=left.column)
        return left

    def parse_equality(self) -> ExprNode:
        left = self.parse_comparison()
        while True:
            if self.match(TokenType.EQ):
                right = self.parse_comparison()
                left = BinaryOpNode(left=left, op="==", right=right, line=left.line, column=left.column)
            elif self.match(TokenType.NEQ):
                right = self.parse_comparison()
                left = BinaryOpNode(left=left, op="!=", right=right, line=left.line, column=left.column)
            else:
                break
        return left

    def parse_comparison(self) -> ExprNode:
        left = self.parse_term()
        while True:
            if self.match(TokenType.LT):
                right = self.parse_term()
                left = BinaryOpNode(left=left, op="<", right=right, line=left.line, column=left.column)
            elif self.match(TokenType.LTE):
                right = self.parse_term()
                left = BinaryOpNode(left=left, op="<=", right=right, line=left.line, column=left.column)
            elif self.match(TokenType.GT):
                right = self.parse_term()
                left = BinaryOpNode(left=left, op=">", right=right, line=left.line, column=left.column)
            elif self.match(TokenType.GTE):
                right = self.parse_term()
                left = BinaryOpNode(left=left, op=">=", right=right, line=left.line, column=left.column)
            else:
                break
        return left

    def parse_term(self) -> ExprNode:
        left = self.parse_factor()
        while True:
            if self.match(TokenType.PLUS):
                right = self.parse_factor()
                left = BinaryOpNode(left=left, op="+", right=right, line=left.line, column=left.column)
            elif self.match(TokenType.MINUS):
                right = self.parse_factor()
                left = BinaryOpNode(left=left, op="-", right=right, line=left.line, column=left.column)
            else:
                break
        return left

    def parse_factor(self) -> ExprNode:
        left = self.parse_unary()
        while True:
            if self.match(TokenType.STAR):
                right = self.parse_unary()
                left = BinaryOpNode(left=left, op="*", right=right, line=left.line, column=left.column)
            elif self.match(TokenType.SLASH):
                right = self.parse_unary()
                left = BinaryOpNode(left=left, op="/", right=right, line=left.line, column=left.column)
            elif self.match(TokenType.PERCENT):
                right = self.parse_unary()
                left = BinaryOpNode(left=left, op="%", right=right, line=left.line, column=left.column)
            else:
                break
        return left

    def parse_unary(self) -> ExprNode:
        if self.match(TokenType.NOT):
            operand = self.parse_unary()
            return UnaryOpNode(op="not", operand=operand, line=operand.line, column=operand.column)
        elif self.match(TokenType.MINUS):
            operand = self.parse_unary()
            return UnaryOpNode(op="-", operand=operand, line=operand.line, column=operand.column)
        elif self.match(TokenType.EXECUTE):
            target = self.parse_call_or_member()
            return ExecuteExprNode(target=target, line=target.line, column=target.column)
        elif self.match(TokenType.SPAWN):
            type_tok = self.expect(TokenType.IDENTIFIER, "Expected agent type identifier after 'spawn'")
            self.expect(TokenType.LPAREN, "Expected '(' after agent type")
            args = []
            while not self.check(TokenType.RPAREN) and not self.check(TokenType.EOF):
                args.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
            self.expect(TokenType.RPAREN, "Expected ')'")
            return SpawnExprNode(agent_type=type_tok.value, args=args, line=type_tok.line, column=type_tok.column)
        return self.parse_call_or_member()

    def parse_call_or_member(self) -> ExprNode:
        expr = self.parse_primary()
        while True:
            if self.match(TokenType.DOT):
                member_tok = self.expect(TokenType.IDENTIFIER, "Expected member name after '.'")
                expr = MemberAccessNode(target=expr, member=member_tok.value, line=member_tok.line, column=member_tok.column)
            elif self.match(TokenType.LPAREN):
                args = []
                kwargs = {}
                while not self.check(TokenType.RPAREN) and not self.check(TokenType.EOF):
                    if self.check(TokenType.IDENTIFIER) and self.peek().type in (TokenType.ASSIGN, TokenType.COLON):
                        k_tok = self.advance()
                        self.advance() # = or :
                        v_expr = self.parse_expression()
                        kwargs[k_tok.value] = v_expr
                    else:
                        args.append(self.parse_expression())
                    if not self.match(TokenType.COMMA):
                        break
                self.expect(TokenType.RPAREN, "Expected ')' closing argument list")
                expr = CallNode(callee=expr, args=args, kwargs=kwargs, line=expr.line, column=expr.column)
            else:
                break
        return expr

    def parse_primary(self) -> ExprNode:
        tok = self.current()
        if self.match(TokenType.STRING):
            return LiteralNode(value=tok.value, type_name="String", line=tok.line, column=tok.column)
        elif self.match(TokenType.INT):
            return LiteralNode(value=tok.value, type_name="Int", line=tok.line, column=tok.column)
        elif self.match(TokenType.FLOAT):
            return LiteralNode(value=tok.value, type_name="Float", line=tok.line, column=tok.column)
        elif self.match(TokenType.BOOLEAN):
            return LiteralNode(value=tok.value, type_name="Bool", line=tok.line, column=tok.column)
        elif self.match(TokenType.IDENTIFIER, TokenType.REACHABILITY):
            return IdentifierNode(name=tok.value, line=tok.line, column=tok.column)
        elif self.match(TokenType.LBRACKET):
            elements = []
            while not self.check(TokenType.RBRACKET) and not self.check(TokenType.EOF):
                elements.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
            self.expect(TokenType.RBRACKET, "Expected ']' closing array")
            return ArrayLiteralNode(elements=elements, line=tok.line, column=tok.column)
        elif self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' closing parenthesis")
            return expr

        raise ParserError(f"Unexpected token in primary expression", tok)
