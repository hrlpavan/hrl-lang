import unittest
from hrl.lexer import Lexer
from hrl.parser import Parser


class TestHRLParser(unittest.TestCase):
    def test_parse_tool(self):
        code = """
        tool SearchEngine(query: String, max_results: Int = 5) -> Array<String> {
            guard: length(query) > 3;
            timeout: 5000ms;
        }
        """
        tokens = Lexer(code).tokenize()
        parser = Parser(tokens)
        module = parser.parse()
        self.assertEqual(len(module.tools), 1)
        tool = module.tools[0]
        self.assertEqual(tool.name, "SearchEngine")
        self.assertEqual(len(tool.params), 2)
        self.assertEqual(tool.return_type, "Array<String>")
        self.assertEqual(tool.timeout_ms, 5000)

    def test_parse_manager_and_worker(self):
        code = """
        manager StrategicPlanner {
            model: "gemini-2.5-pro";
            dilation: 8;
            goal MarketAnalysis(company: String) {
                invariant: company != "";
                subgoal Research -> "Analyze 10-K filings";
            }
        }

        worker TacticalWorker for StrategicPlanner {
            model: "gemini-2.5-flash";
            tools: [];
            policy {
                on subgoal(Research) {
                    let done = true;
                }
            }
        }
        """
        tokens = Lexer(code).tokenize()
        parser = Parser(tokens)
        module = parser.parse()
        self.assertEqual(len(module.managers), 1)
        self.assertEqual(len(module.workers), 1)
        mgr = module.managers[0]
        self.assertEqual(mgr.dilation, 8)
        self.assertEqual(len(mgr.goals[0].subgoals), 1)


if __name__ == "__main__":
    unittest.main()
