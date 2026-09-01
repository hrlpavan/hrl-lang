// HRL Example 01: Hello Agent Orchestrator
module HelloAgentDemo

import "antigravity/core" as agy

tool GreeterTool(name: String) -> String {
    guard: length(name) > 0;
    timeout: 3000ms;
}

manager GreetingManager {
    model: "gemini-2.5-pro";
    dilation: 4;

    goal SayHello(target_name: String) {
        invariant: target_name != "";
        subgoal PrepareGreeting -> "Generate polite personalized greeting";
        subgoal DeliverGreeting -> "Deliver greeting via communication tool";
    }
}

worker GreetingWorker for GreetingManager {
    model: "gemini-2.5-flash";
    tools: [GreeterTool];

    policy {
        on subgoal(PrepareGreeting) {
            let msg = "Hello from HRL Language for LLMs!";
            emit greeting_ready(msg);
        }

        on subgoal(DeliverGreeting) {
            let res = execute GreeterTool(name: "Pavan Kumar Sadashiv");
            verify reachability.is_sandboxed("python");
            emit greeting_dispatched(res);
        }
    }
}

pipeline Main(target: String = "Antigravity Engineer") {
    let mgr = spawn GreetingManager();
    let result = execute mgr.SayHello(target_name: target);
    return result;
}
