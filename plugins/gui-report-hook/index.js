const { execSync } = require("child_process");
const { existsSync, readFileSync } = require("fs");
const { join } = require("path");

const HOME = process.env.HOME || process.env.USERPROFILE || "~";
const SKILL_DIR = join(HOME, ".openclaw/workspace/skills/gui-agent");
const TRACKER_STATE = join(SKILL_DIR, "skills/gui-report/scripts/.tracker_state.json");
const TRACKER_SCRIPT = join(SKILL_DIR, "skills/gui-report/scripts/tracker.py");
const PYTHON = join(HOME, "gui-actor-env/bin/python3");

const COUNTERS = [
  "screenshots", "clicks", "learns", "transitions",
  "image_calls", "ocr_calls", "detector_calls",
  "workflow_level0", "workflow_level1", "workflow_level2",
  "workflow_auto_steps", "workflow_explore_steps",
];

module.exports = function register(api) {
  api.on("agent_end", (_event, _ctx) => {
    if (!existsSync(TRACKER_STATE)) {
      return;
    }

    try {
      const state = JSON.parse(readFileSync(TRACKER_STATE, "utf-8"));
      const hasActivity = COUNTERS.some((k) => (state[k] || 0) > 0);

      if (!hasActivity) {
        // No GUI activity this turn — just clean up
        require("fs").unlinkSync(TRACKER_STATE);
        return;
      }

      // Run report (saves to log + cleans state)
      const pythonBin = existsSync(PYTHON) ? PYTHON : "python3";
      execSync(`${pythonBin} "${TRACKER_SCRIPT}" report`, {
        timeout: 10000,
        stdio: "ignore",
      });
    } catch (_e) {
      // Best-effort — never break the agent
      try {
        // If report failed, at least clean up stale state
        if (existsSync(TRACKER_STATE)) {
          require("fs").unlinkSync(TRACKER_STATE);
        }
      } catch (_) {}
    }
  });
};
