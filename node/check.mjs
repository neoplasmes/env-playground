import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const root = fileURLToPath(new URL("../", import.meta.url));
const tooling = `${root}/node`;
const directory = mkdtempSync(join(tmpdir(), "playground-commitlint-"));
try {
  for (const [message, accepted] of [
    ["feat(processor): add image conversion", true],
    ["fix(api)!: change job response\n\nBREAKING CHANGE: clients must send the new field", true],
    ["update stuff", false],
    ["unknown(api): change response", false],
    [`chore(agents): ${"x".repeat(100)}`, false],
  ]) {
    const path = join(directory, "message");
    writeFileSync(path, `${message}\n`);
    const result = spawnSync("bash", [`${root}/.githooks/commit-msg`, path], {
      cwd: root,
      encoding: "utf8",
    });
    if (result.error) throw result.error;
    assert.equal(result.status === 0, accepted, `${message}\n${result.stdout}${result.stderr}`);
  }
  for (const file of ["activate.sh", "run.sh", "install-hooks.sh"]) {
    const result = spawnSync("bash", ["-n", `${tooling}/${file}`], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
  }
  console.log(
    "Node tooling checks passed: commit-msg hook accepts conventional commits and rejects invalid messages.",
  );
} finally {
  rmSync(directory, { recursive: true, force: true });
}
