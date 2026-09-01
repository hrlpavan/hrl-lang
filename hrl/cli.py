"""
HRL Command Line Interface (Compiler & Runtime CLI).
Author: Pavan Kumar Sadashiv (HRL International Pvt. Ltd.)
"""

import sys
import argparse
import asyncio
import json
from pathlib import Path
from hrl.lexer import Lexer, LexerError
from hrl.parser import Parser, ParserError
from hrl.typechecker import TypeChecker, TypeError
from hrl.runtime.interpreter import Interpreter
from hrl.compiler.python_gen import PythonCodeGenerator


def main():
    parser = argparse.ArgumentParser(
        prog="hrl",
        description="HRL (Hierarchical Reasoning Language) Compiler & Runtime for LLMs"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # hrl run
    run_parser = subparsers.add_parser("run", help="Execute an HRL program directly")
    run_parser.add_argument("file", help="Path to .hrl source file")
    run_parser.add_argument("--pipeline", default=None, help="Name of pipeline to run (default: first pipeline)")
    run_parser.add_argument("--args", default="{}", help="JSON dictionary of pipeline arguments")

    # hrl build
    build_parser = subparsers.add_parser("build", help="Transpile HRL source to Python")
    build_parser.add_argument("file", help="Path to .hrl source file")
    build_parser.add_argument("-o", "--output", help="Output .py file path")

    # hrl check
    check_parser = subparsers.add_parser("check", help="Typecheck and verify safety invariants")
    check_parser.add_argument("file", help="Path to .hrl source file")

    # hrl ast
    ast_parser = subparsers.add_parser("ast", help="Print Abstract Syntax Tree")
    ast_parser.add_argument("file", help="Path to .hrl source file")

    # hrl tokens
    tok_parser = subparsers.add_parser("tokens", help="Print lexical tokens")
    tok_parser.add_argument("file", help="Path to .hrl source file")

    args = parser.parse_args()

    source_path = Path(args.file)
    if not source_path.exists():
        print(f"Error: File '{args.file}' does not exist", file=sys.stderr)
        sys.exit(1)

    source_code = source_path.read_text(encoding="utf-8")

    try:
        # 1. Lexer
        lexer = Lexer(source_code, filename=str(source_path))
        tokens = lexer.tokenize()

        if args.command == "tokens":
            for tok in tokens:
                print(tok)
            return

        # 2. Parser
        hrl_parser = Parser(tokens, filename=str(source_path))
        ast_module = hrl_parser.parse()

        if args.command == "ast":
            print(f"Module: {ast_module.name}")
            print(f"  Imports ({len(ast_module.imports)}): {[i.module_path for i in ast_module.imports]}")
            print(f"  Tools ({len(ast_module.tools)}): {[t.name for t in ast_module.tools]}")
            print(f"  Managers ({len(ast_module.managers)}): {[m.name for m in ast_module.managers]}")
            print(f"  Workers ({len(ast_module.workers)}): {[w.name for w in ast_module.workers]}")
            print(f"  Pipelines ({len(ast_module.pipelines)}): {[p.name for p in ast_module.pipelines]}")
            return

        # 3. Typechecker
        checker = TypeChecker()
        diagnostics = checker.check(ast_module)

        if args.command == "check":
            print(f"[OK] {source_path.name} verified successfully with {len(diagnostics)} rules:")
            for d in diagnostics:
                print(f"  + {d}")
            return

        # 4. Build
        if args.command == "build":
            gen = PythonCodeGenerator(ast_module)
            py_code = gen.generate()
            out_path = args.output or source_path.with_suffix(".py")
            Path(out_path).write_text(py_code, encoding="utf-8")
            print(f"[BUILD SUCCESS] Transpiled {source_path.name} -> {out_path}")
            return

        # 5. Run
        if args.command == "run":
            pipeline_name = args.pipeline
            if not pipeline_name:
                if ast_module.pipelines:
                    pipeline_name = ast_module.pipelines[0].name
                else:
                    print("Error: No pipelines found in module to execute", file=sys.stderr)
                    sys.exit(1)

            kwargs = json.loads(args.args)
            interpreter = Interpreter(ast_module)

            print(f"============================================================")
            print(f" [HRL RUNTIME] Executing Module: {ast_module.name} | Pipeline: {pipeline_name}")
            print(f"============================================================")

            result = asyncio.run(interpreter.run_pipeline(pipeline_name, **kwargs))
            print(f"\n[PIPELINE OUTPUT]:")
            print(json.dumps(result, indent=2, default=str))

    except (LexerError, ParserError, TypeError) as err:
        print(f"\n[COMPILATION ERROR] {err}", file=sys.stderr)
        sys.exit(1)
    except Exception as ex:
        print(f"\n[RUNTIME ERROR] {ex}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
