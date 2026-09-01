"""
HRL Lexer (Tokenizer) for Hierarchical Reasoning Language.
Author: Pavan Kumar Sadashiv (HRL International Pvt. Ltd.)
"""

from typing import List
from hrl.tokens import Token, TokenType, KEYWORDS


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"LexerError [L{line}:C{column}]: {message}")
        self.message = message
        self.line = line
        self.column = column


class Lexer:
    def __init__(self, source: str, filename: str = "<source>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(source)
        self.tokens: List[Token] = []

    def peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx >= self.length:
            return ""
        return self.source[idx]

    def advance(self) -> str:
        if self.pos >= self.length:
            return ""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.peek() == expected:
            self.advance()
            return True
        return False

    def skip_whitespace_and_comments(self) -> None:
        while self.pos < self.length:
            ch = self.peek()
            if ch in " \t\r\n":
                self.advance()
            elif ch == "/" and self.peek(1) == "/":
                # Single-line comment
                while self.pos < self.length and self.peek() != "\n":
                    self.advance()
            elif ch == "/" and self.peek(1) == "*":
                # Block comment
                self.advance() # /
                self.advance() # *
                while self.pos < self.length:
                    if self.peek() == "*" and self.peek(1) == "/":
                        self.advance()
                        self.advance()
                        break
                    self.advance()
                else:
                    raise LexerError("Unterminated block comment", self.line, self.column)
            else:
                break

    def read_string(self) -> Token:
        start_line = self.line
        start_col = self.column
        quote_char = self.advance() # " or '
        chars = []

        while self.pos < self.length:
            ch = self.peek()
            if ch == quote_char:
                self.advance()
                val = "".join(chars)
                return Token(TokenType.STRING, val, start_line, start_col, len(val) + 2)
            elif ch == "\\":
                self.advance()
                esc = self.advance()
                if esc == "n": chars.append("\n")
                elif esc == "t": chars.append("\t")
                elif esc == "r": chars.append("\r")
                elif esc == "\\": chars.append("\\")
                elif esc == '"': chars.append('"')
                elif esc == "'": chars.append("'")
                else: chars.append(esc)
            elif ch == "\n":
                raise LexerError("Unterminated string literal across newline", start_line, start_col)
            else:
                chars.append(self.advance())

        raise LexerError("Unterminated string literal at EOF", start_line, start_col)

    def read_number(self) -> Token:
        start_line = self.line
        start_col = self.column
        start_pos = self.pos
        is_float = False

        while self.pos < self.length and (self.peek().isdigit() or self.peek() == "_"):
            self.advance()

        if self.peek() == "." and self.peek(1).isdigit():
            is_float = True
            self.advance() # .
            while self.pos < self.length and (self.peek().isdigit() or self.peek() == "_"):
                self.advance()

        num_str = self.source[start_pos:self.pos].replace("_", "")

        # Check for duration suffixes (e.g., 5000ms, 10s, 2m)
        if self.peek().isalpha():
            suffix = ""
            while self.pos < self.length and self.peek().isalpha():
                suffix += self.advance()
            if suffix == "ms":
                val = float(num_str) if is_float else int(num_str)
                return Token(TokenType.INT, int(val), start_line, start_col, self.pos - start_pos)
            elif suffix == "s":
                val = (float(num_str) if is_float else int(num_str)) * 1000
                return Token(TokenType.INT, int(val), start_line, start_col, self.pos - start_pos)
            else:
                raise LexerError(f"Invalid duration suffix '{suffix}'", start_line, start_col)

        if is_float:
            return Token(TokenType.FLOAT, float(num_str), start_line, start_col, self.pos - start_pos)
        return Token(TokenType.INT, int(num_str), start_line, start_col, self.pos - start_pos)

    def read_identifier_or_keyword(self) -> Token:
        start_line = self.line
        start_col = self.column
        start_pos = self.pos

        while self.pos < self.length and (self.peek().isalnum() or self.peek() == "_"):
            self.advance()

        text = self.source[start_pos:self.pos]
        length = self.pos - start_pos

        if text in KEYWORDS:
            tok_type = KEYWORDS[text]
            if tok_type == TokenType.BOOLEAN:
                return Token(TokenType.BOOLEAN, text == "true", start_line, start_col, length)
            return Token(tok_type, text, start_line, start_col, length)

        return Token(TokenType.IDENTIFIER, text, start_line, start_col, length)

    def tokenize(self) -> List[Token]:
        while self.pos < self.length:
            self.skip_whitespace_and_comments()
            if self.pos >= self.length:
                break

            line = self.line
            col = self.column
            ch = self.peek()

            if ch in ('"', "'"):
                self.tokens.append(self.read_string())
            elif ch.isdigit():
                self.tokens.append(self.read_number())
            elif ch.isalpha() or ch == "_":
                self.tokens.append(self.read_identifier_or_keyword())
            elif ch == "-":
                self.advance()
                if self.match(">"):
                    self.tokens.append(Token(TokenType.ARROW, "->", line, col, 2))
                else:
                    self.tokens.append(Token(TokenType.MINUS, "-", line, col, 1))
            elif ch == "=":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.EQ, "==", line, col, 2))
                elif self.match(">"):
                    self.tokens.append(Token(TokenType.FAT_ARROW, "=>", line, col, 2))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, "=", line, col, 1))
            elif ch == "!":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.NEQ, "!=", line, col, 2))
                else:
                    self.tokens.append(Token(TokenType.NOT, "!", line, col, 1))
            elif ch == "<":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.LTE, "<=", line, col, 2))
                else:
                    self.tokens.append(Token(TokenType.LT, "<", line, col, 1))
            elif ch == ">":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.GTE, ">=", line, col, 2))
                else:
                    self.tokens.append(Token(TokenType.GT, ">", line, col, 1))
            elif ch == "+":
                self.advance(); self.tokens.append(Token(TokenType.PLUS, "+", line, col, 1))
            elif ch == "*":
                self.advance(); self.tokens.append(Token(TokenType.STAR, "*", line, col, 1))
            elif ch == "/":
                self.advance(); self.tokens.append(Token(TokenType.SLASH, "/", line, col, 1))
            elif ch == "%":
                self.advance(); self.tokens.append(Token(TokenType.PERCENT, "%", line, col, 1))
            elif ch == "(":
                self.advance(); self.tokens.append(Token(TokenType.LPAREN, "(", line, col, 1))
            elif ch == ")":
                self.advance(); self.tokens.append(Token(TokenType.RPAREN, ")", line, col, 1))
            elif ch == "{":
                self.advance(); self.tokens.append(Token(TokenType.LBRACE, "{", line, col, 1))
            elif ch == "}":
                self.advance(); self.tokens.append(Token(TokenType.RBRACE, "}", line, col, 1))
            elif ch == "[":
                self.advance(); self.tokens.append(Token(TokenType.LBRACKET, "[", line, col, 1))
            elif ch == "]":
                self.advance(); self.tokens.append(Token(TokenType.RBRACKET, "]", line, col, 1))
            elif ch == ",":
                self.advance(); self.tokens.append(Token(TokenType.COMMA, ",", line, col, 1))
            elif ch == ":":
                self.advance(); self.tokens.append(Token(TokenType.COLON, ":", line, col, 1))
            elif ch == ";":
                self.advance(); self.tokens.append(Token(TokenType.SEMICOLON, ";", line, col, 1))
            elif ch == ".":
                self.advance(); self.tokens.append(Token(TokenType.DOT, ".", line, col, 1))
            else:
                bad_char = self.advance()
                raise LexerError(f"Unexpected character '{bad_char}'", line, col)

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column, 0))
        return self.tokens
