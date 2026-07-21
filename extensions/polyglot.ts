import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

type AmbientPayload = { message?: string };

const pluginRoot = fileURLToPath(new URL("..", import.meta.url));
const scriptPath = fileURLToPath(new URL("../scripts/ambient.py", import.meta.url));

function runPython(args: string[]): string | null {
  const candidates: Array<[string, string[]]> =
    process.platform === "win32"
      ? [["py", ["-3"]], ["python", []]]
      : [["python3", []], ["python", []]];

  for (const [command, prefix] of candidates) {
    const result = spawnSync(
      command,
      [...prefix, ...args],
      {
        cwd: pluginRoot,
        encoding: "utf8",
        timeout: 5000,
        env: { ...process.env, PYTHONUTF8: "1" },
      },
    );
    if (result.error || result.status !== 0 || !result.stdout.trim()) continue;
    return result.stdout.trim();
  }
  return null;
}

function loadPhrase(): string | null {
  const output = runPython([scriptPath, "--host", "pi", "--json"]);
  if (!output) return null;
  try {
    const payload = JSON.parse(output) as AmbientPayload;
    return typeof payload.message === "string" && payload.message.trim()
      ? payload.message.trim()
      : null;
  } catch {
    return null;
  }
}

export default function polyglot(pi: ExtensionAPI) {
  pi.on("agent_end", async (_event, ctx) => {
    try {
      const message = loadPhrase();
      if (message && ctx.hasUI) ctx.ui.notify(message, "info");
    } catch {
      // Ambient learning must never interrupt an agent turn.
    }
  });

  pi.registerCommand("polyglot", {
    description: "Sample a phrase or configure Polyglot ambience",
    handler: async (rawArgs, ctx) => {
      try {
        const tokens = rawArgs.trim().split(/\s+/).filter(Boolean);
        const action = tokens[0]?.toLowerCase() ?? "status";
        let args: string[];
        if (action === "status") {
          args = ["-m", "polyglot", "ambient", "status"];
        } else if (action === "disable") {
          args = ["-m", "polyglot", "ambient", "disable"];
        } else if (action === "sample") {
          args = ["-m", "polyglot", "sample"];
          if (tokens[1]) args.push("--pair", tokens[1]);
        } else if (action === "enable" && tokens[1]) {
          args = ["-m", "polyglot", "ambient", "enable", "--pair", tokens[1]];
          if (tokens[2]) args.push("--cadence", tokens[2]);
        } else {
          ctx.ui.notify(
            "Usage: /polyglot [status|sample [pair]|enable <pair> [cadence]|disable]",
            "warning",
          );
          return;
        }
        const output = runPython(args);
        ctx.ui.notify(output || "Polyglot command failed.", output ? "info" : "warning");
      } catch {
        ctx.ui.notify("Polyglot command failed without affecting the session.", "warning");
      }
    },
  });
}
