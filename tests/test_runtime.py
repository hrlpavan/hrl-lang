import unittest
import asyncio
from hrl.lexer import Lexer
from hrl.parser import Parser
from hrl.typechecker import TypeChecker
from hrl.runtime.interpreter import Interpreter


class TestHRLRuntime(unittest.TestCase):
    def test_pipeline_execution(self):
        code = """
        pipeline CalculateMath(a: Int, b: Int) -> Int {
            let sum = a + b;
            let mult = sum * 2;
            verify mult == 20;
            return mult;
        }
        """
        tokens = Lexer(code).tokenize()
        module = Parser(tokens).parse()
        checker = TypeChecker()
        checker.check(module)

        interpreter = Interpreter(module)
        res = asyncio.run(interpreter.run_pipeline("CalculateMath", a=4, b=6))
        self.assertEqual(res, 20)

    def test_hierarchical_manager_worker_execution(self):
        code = """
        manager Planner {
            dilation: 4;
            goal ExecuteTask(topic: String) {
                subgoal StepA -> "Collect facts";
                subgoal StepB -> "Formulate synthesis";
            }
        }

        worker TaskWorker for Planner {
            tools: [];
            policy {
                on subgoal(StepA) {
                    let done = true;
                }
            }
        }

        pipeline RunTask() {
            let p = spawn Planner();
            let res = execute p.ExecuteTask(topic: "AI Architecture");
            return res;
        }
        """
        tokens = Lexer(code).tokenize()
        module = Parser(tokens).parse()
        checker = TypeChecker()
        checker.check(module)

        interpreter = Interpreter(module)
        res = asyncio.run(interpreter.run_pipeline("RunTask"))
        self.assertEqual(res["status"], "completed")
        self.assertEqual(len(res["subgoals"]), 2)
        self.assertEqual(res["telemetry"]["dilation_c"], 4)


if __name__ == "__main__":
    unittest.main()
