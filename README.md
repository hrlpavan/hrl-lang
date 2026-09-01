# HRL Programming Language for LLMs (`hrl-lang`)

**Hierarchical Reasoning Language (HRL)** is a domain-specific, verifiable programming language engineered specifically for **Large Language Models (LLMs), Autonomous Multi-Agent Orchestration, and Antigravity Systems**.

> **Designed by Pavan Kumar Sadashiv**  
> *Founder & Managing Director, HRL International Private Limited™*

---

## 🚀 Key Language Primitives

1. **Dual-Timescale Reasoning (FeUdal Networks Macro/Micro)**:
   - `manager`: High-level reasoning orchestrator generating sub-goals over dilated horizons ($C=8$).
   - `worker`: Low-level tool execution agent operating within manager's sub-goal safety envelope.
2. **Formal Reachability & Safety Envelopes**:
   - `guard`: Pre-execution validation invariants bounding tool parameters.
   - `reachability`: Symbolic reachability invariant verification ($R_c(s)$) ensuring zero out-of-distribution execution.
3. **Structured Goal Hierarchies**:
   - `goal` & `subgoal`: Declarative intent definitions with formal acceptance criteria.
4. **Tool & Agent Contracts**:
   - `tool`: First-class typed tool contracts with timeouts and safety guards.
   - `pipeline`: Async workflows orchestrating agents and deterministic pipelines.

---

## 💻 Code Example (`.hrl`)

```hrl
// Enterprise Deep Research in HRL
module EnterpriseResearchOrchestrator

tool SearchEngine(query: String, max_results: Int = 5) -> Array<String> {
    guard: length(query) > 3;
    timeout: 5000ms;
}

manager StrategicResearchPlanner {
    model: "gemini-2.5-pro";
    dilation: 8;

    goal MarketAnalysis(company: String) {
        invariant: company != "";
        subgoal BackgroundResearch   -> "Retrieve official enterprise filings and structure";
        subgoal CompetitorBenchmarking -> "Analyze top industry rivals and pricing models";
        subgoal ValuationSynthesis     -> "Synthesize growth trajectory and revenue multiples";
    }
}

worker TacticalResearcher for StrategicResearchPlanner {
    model: "gemini-2.5-flash";
    tools: [SearchEngine];

    policy {
        on subgoal(BackgroundResearch) {
            let docs = execute SearchEngine(query: "Company 10-K SEC filings", max_results: 5);
            verify reachability.contains_verified_sources(docs);
            emit research_stage_done(docs);
        }
    }
}

pipeline RunResearch(company_name: String = "HRL International Pvt. Ltd.") {
    let planner = spawn StrategicResearchPlanner();
    let result = execute planner.MarketAnalysis(company: company_name);
    return result;
}
```

---

## 🛠️ Toolchain & CLI Usage

### Check & Verify Safety Invariants
```bash
python3 -m hrl.cli check examples/02_hierarchical_researcher.hrl
```

### Run Directly in HRL Async Runtime
```bash
python3 -m hrl.cli run examples/02_hierarchical_researcher.hrl
```

### Compile to Production Python 3.11+ Async Code
```bash
python3 -m hrl.cli build examples/02_hierarchical_researcher.hrl -o researcher.py
```

### Run Test Suite
```bash
PYTHONPATH=. python3 -m unittest discover -s tests -p "test_*.py" -v
```
