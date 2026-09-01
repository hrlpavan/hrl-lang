// HRL Example 03: Formal Reachability Envelope & Safety Invariants
module SafetyCriticalSystem

tool MotorActuator(torque: Float, angle: Float) -> Bool {
    guard: torque >= -10.0 and torque <= 10.0;
    timeout: 1000ms;
}

manager AutonomousSafetyController {
    model: "gemini-2.5-pro";
    dilation: 8;

    goal StabilizeTrajectory(target_velocity: Float) {
        invariant: target_velocity >= 0.0;
        subgoal CalculatePath -> "Compute collision-free trajectory manifold";
        subgoal VerifyReachability -> "Confirm state space is within Rc(s)";
        subgoal ApplyActuation -> "Execute constrained torque vector";
    }
}

worker SafetyWorker for AutonomousSafetyController {
    model: "gemini-2.5-flash";
    tools: [MotorActuator];

    policy {
        on subgoal(CalculatePath) {
            let path_valid = true;
            verify path_valid, "Trajectory must be collision-free";
            emit path_planned(path_valid);
        }

        on subgoal(VerifyReachability) {
            let feasible = reachability.check_state_bounds(1.5, 0.0, 5.0);
            verify feasible, "State must remain inside reachability invariant envelope";
            emit envelope_checked(feasible);
        }

        on subgoal(ApplyActuation) {
            let status = execute MotorActuator(torque: 4.5, angle: 0.25);
            emit motor_command_applied(status);
        }
    }
}

pipeline ExecuteSafeRollout(speed: Float = 2.5) {
    let controller = spawn AutonomousSafetyController();
    let result = execute controller.StabilizeTrajectory(target_velocity: speed);
    return result;
}
