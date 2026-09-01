import unittest
from hrl.tokens import TokenType
from hrl.lexer import Lexer, LexerError


class TestHRLLexer(unittest.TestCase):
    def test_keywords_and_identifiers(self):
        code = "module ManagerDemo manager StrategicPlanner worker TacticalWorker for StrategicPlanner"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]] # exclude EOF
        self.assertEqual(types, [
            TokenType.MODULE,
            TokenType.IDENTIFIER,
            TokenType.MANAGER,
            TokenType.IDENTIFIER,
            TokenType.WORKER,
            TokenType.IDENTIFIER,
            TokenType.FOR,
            TokenType.IDENTIFIER
        ])

    def test_numbers_and_durations(self):
        code = "100 3.14 5000ms 10s"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].value, 100)
        self.assertEqual(tokens[1].value, 3.14)
        self.assertEqual(tokens[2].value, 5000)
        self.assertEqual(tokens[3].value, 10000)

    def test_operators_and_delimiters(self):
        code = "-> => == != <= >= {"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        self.assertEqual(types, [
            TokenType.ARROW,
            TokenType.FAT_ARROW,
            TokenType.EQ,
            TokenType.NEQ,
            TokenType.LTE,
            TokenType.GTE,
            TokenType.LBRACE
        ])

    def test_comments(self):
        code = """
        // Single line comment
        let x = 42; /* Block comment */
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, TokenType.LET)
        self.assertEqual(tokens[1].value, "x")
        self.assertEqual(tokens[2].type, TokenType.ASSIGN)
        self.assertEqual(tokens[3].value, 42)


if __name__ == "__main__":
    unittest.main()
