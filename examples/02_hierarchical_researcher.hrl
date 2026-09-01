// HRL Example 02: Enterprise Hierarchical Deep Researcher
module EnterpriseResearchOrchestrator

import "antigravity/tools" as agy

tool SearchEngine(query: String, max_results: Int = 5) -> Array<String> {
    guard: length(query) > 3;
    timeout: 5000ms;
}

tool DataExtractor(url: String) -> String {
    guard: length(url) > 8;
    timeout: 8000ms;
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
    tools: [SearchEngine, DataExtractor];

    policy {
        on subgoal(BackgroundResearch) {
            let docs = execute SearchEngine(query: "Company Overview SEC 10K", max_results: 5);
            verify reachability.contains_verified_sources(docs);
            emit research_stage_done(docs);
        }

        on subgoal(CompetitorBenchmarking) {
            let rivals = execute SearchEngine(query: "Top 5 industry competitors", max_results: 3);
            emit benchmark_ready(rivals);
        }

        on subgoal(ValuationSynthesis) {
            let report = execute SearchEngine(query: "Financial multiples valuation", max_results: 3);
            emit final_synthesis(report);
        }
    }
}

pipeline RunResearch(company_name: String = "HRL International Pvt. Ltd.") {
    let planner = spawn StrategicResearchPlanner();
    let result = execute planner.MarketAnalysis(company: company_name);
    return result;
}
