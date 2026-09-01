"""
HRL Programming Language for LLMs (Hierarchical Reasoning Language)
Token definitions and Lexical Specifications.
Author: Pavan Kumar Sadashiv (HRL International Pvt. Ltd.)
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    INT = auto()
    FLOAT = auto()
    BOOLEAN = auto()

    # Keywords - Declarations
    MODULE = auto()
    IMPORT = auto()
    AS = auto()
    TOOL = auto()
    MANAGER = auto()
    WORKER = auto()
    GOAL = auto()
    SUBGOAL = auto()
    POLICY = auto()
    PIPELINE = auto()
    PARALLEL = auto()
    FOR = auto()
    ON = auto()
    
    # Keywords - Execution & Safety
    GUARD = auto()
    REACHABILITY = auto()
    INVARIANT = auto()
    VERIFY = auto()
    EXECUTE = auto()
    SPAWN = auto()
    EMIT = auto()
    LET = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    TIMEOUT = auto()
    DILATION = auto()
    MODEL = auto()
    TOOLS = auto()

    # Types
    TYPE_STRING = auto()
    TYPE_INT = auto()
    TYPE_FLOAT = auto()
    TYPE_BOOL = auto()
    TYPE_ARRAY = auto()
    TYPE_MAP = auto()
    TYPE_ANY = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    ARROW = auto()          # ->
    FAT_ARROW = auto()      # =>

    # Delimiters
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACE = auto()         # {
    RBRACE = auto()         # }
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    COMMA = auto()          # ,
    COLON = auto()          # :
    SEMICOLON = auto()      # ;
    DOT = auto()            # .

    # Special
    EOF = auto()
    UNKNOWN = auto()


KEYWORDS = {
    "module": TokenType.MODULE,
    "import": TokenType.IMPORT,
    "as": TokenType.AS,
    "tool": TokenType.TOOL,
    "manager": TokenType.MANAGER,
    "worker": TokenType.WORKER,
    "goal": TokenType.GOAL,
    "subgoal": TokenType.SUBGOAL,
    "policy": TokenType.POLICY,
    "pipeline": TokenType.PIPELINE,
    "parallel": TokenType.PARALLEL,
    "for": TokenType.FOR,
    "on": TokenType.ON,
    "guard": TokenType.GUARD,
    "reachability": TokenType.REACHABILITY,
    "invariant": TokenType.INVARIANT,
    "verify": TokenType.VERIFY,
    "execute": TokenType.EXECUTE,
    "spawn": TokenType.SPAWN,
    "emit": TokenType.EMIT,
    "let": TokenType.LET,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "timeout": TokenType.TIMEOUT,
    "dilation": TokenType.DILATION,
    "model": TokenType.MODEL,
    "tools": TokenType.TOOLS,
    "true": TokenType.BOOLEAN,
    "false": TokenType.BOOLEAN,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    # Built-in type keywords
    "String": TokenType.TYPE_STRING,
    "Int": TokenType.TYPE_INT,
    "Float": TokenType.TYPE_FLOAT,
    "Bool": TokenType.TYPE_BOOL,
    "Array": TokenType.TYPE_ARRAY,
    "Map": TokenType.TYPE_MAP,
    "Any": TokenType.TYPE_ANY,
}


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int
    length: int = 1

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"
