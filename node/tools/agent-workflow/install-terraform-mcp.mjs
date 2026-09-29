import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { chmod, mkdir, mkdtemp, readFile, rename, rm, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../../", import.meta.url));
const release = JSON.parse(
  await readFile(new URL("./terraform-mcp.json", import.meta.url), "utf8"),
);
const target = `${process.platform}_${process.arch === "x64" ? "amd64" : process.arch}`;
const checksum = release.sha256[target];
if (!checksum) throw new Error(`No verified Terraform MCP archive configured for ${target}`);
const filename = `terraform-mcp-server_${release.version}_${target}.zip`;
const url = `https://releases.hashicorp.com/terraform-mcp-server/${release.version}/${filename}`;
const response = await fetch(url, { signal: AbortSignal.timeout(120_000) });
if (!response.ok) throw new Error(`Terraform MCP download failed: HTTP ${response.status}`);
const archive = Buffer.from(await response.arrayBuffer());
if (createHash("sha256").update(archive).digest("hex") !== checksum) {
  throw new Error("Terraform MCP archive checksum mismatch; nothing installed");
}
const destination = `${root}/.cache/agent-workflow/bin`;
await mkdir(destination, { recursive: true });
const temporary = await mkdtemp(`${destination}/terraform-install-`);
try {
  const zip = `${temporary}/archive.zip`;
  await writeFile(zip, archive);
  // Extract only the expected binary, never archive-controlled paths.
  const result = spawnSync("unzip", ["-p", zip, "terraform-mcp-server"], {
    maxBuffer: 128 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  if (result.status !== 0 || result.stdout.length === 0)
    throw new Error("Cannot extract Terraform MCP; install unzip and retry");
  const binary = `${temporary}/terraform-mcp-server`;
  await writeFile(binary, result.stdout);
  await chmod(binary, 0o755);
  await rename(binary, `${destination}/terraform-mcp-server`);
  console.log(`Installed Terraform MCP ${release.version} (${target}); SHA-256 verified`);
} finally {
  await rm(temporary, { recursive: true, force: true });
}
