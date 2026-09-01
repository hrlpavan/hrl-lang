import unittest
from hrl.lexer import Lexer
from hrl.parser import Parser
from hrl.compiler.python_gen import PythonCodeGenerator


class TestHRLCompiler(unittest.TestCase):
    def test_python_code_generation(self):
        code = """
        module TestGen

        tool SearchTool(q: String) -> String {
            guard: length(q) > 2;
        }

        manager Planner {
            dilation: 8;
            goal PlanGoal(target: String) {
                subgoal SubA -> "First action";
            }
        }

        pipeline Run(target: String) {
            let p = spawn Planner();
            let res = execute p.PlanGoal(target: target);
            return res;
        }
        """
        tokens = Lexer(code).tokenize()
        module = Parser(tokens).parse()
        gen = PythonCodeGenerator(module)
        py_code = gen.generate()
        self.assertIn("async def tool_SearchTool", py_code)
        self.assertIn("class Manager_Planner", py_code)
        self.assertIn("async def Run(target: str)", py_code)


if __name__ == "__main__":
    unittest.main()
