import unittest
from hrl.lexer import Lexer
from hrl.parser import Parser
from hrl.typechecker import TypeChecker, TypeError


class TestHRLTypeChecker(unittest.TestCase):
    def test_valid_module_typecheck(self):
        code = """
        manager StrategicPlanner {
            model: "gemini-2.5-pro";
            dilation: 8;
            goal MarketAnalysis(company: String) {
                invariant: company != "";
                subgoal StepOne -> "First step";
            }
        }

        worker TacticalWorker for StrategicPlanner {
            model: "gemini-2.5-flash";
            tools: [];
            policy {
                on subgoal(StepOne) {
                    let x = 10;
                }
            }
        }
        """
        tokens = Lexer(code).tokenize()
        module = Parser(tokens).parse()
        checker = TypeChecker()
        diagnostics = checker.check(module)
        self.assertTrue(len(diagnostics) > 0)

    def test_invalid_subgoal_rejected(self):
        code = """
        manager StrategicPlanner {
            model: "gemini-2.5-pro";
            dilation: 8;
            goal MarketAnalysis(company: String) {
                subgoal ValidStep -> "Valid";
            }
        }

        worker TacticalWorker for StrategicPlanner {
            model: "gemini-2.5-flash";
            tools: [];
            policy {
                on subgoal(NonExistentStep) {
                    let x = 10;
                }
            }
        }
        """
        tokens = Lexer(code).tokenize()
        module = Parser(tokens).parse()
        checker = TypeChecker()
        with self.assertRaises(TypeError):
            checker.check(module)


if __name__ == "__main__":
    unittest.main()
