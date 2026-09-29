import { spawn } from "node:child_process";
import { mkdir, mkdtemp, open, rm } from "node:fs/promises";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../../", import.meta.url));
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
let stopServices = async () => {};

export async function teardown() {
  await stopServices();
}

async function reservePort() {
  const server = createServer();
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });

  return { server, port: server.address().port };
}

export default async function setup() {
  const directory = await mkdtemp(join(tmpdir(), "playground-browser-"));
  const artifacts = join(root, ".local/agent-workflow");
  await mkdir(artifacts, { recursive: true });
  const logPath = join(artifacts, `services-${Date.now()}.log`);
  const log = await open(logPath, "w");
  const children = [];
  const reservations = [];
  let stopping = false;
  let stopped;
  const signalChildren = (signal) => {
    for (const { process } of children) {
      if (process.pid) {
        try {
          globalThis.process.kill(-process.pid, signal);
        } catch (error) {
          if (error.code !== "ESRCH") throw error;
        }
      }
    }
  };
  const cleanup = () => {
    stopping = true;
    stopped ??= stop();

    return stopped;
  };
  const onInterrupt = () => {
    stopping = true;
    signalChildren("SIGTERM");
    // Playwright's global teardown awaits cleanup, including during interrupted setup.
  };
  const onTerminate = () => {
    onInterrupt();
    void cleanup().finally(() => process.exit(143));
  };
  const stop = async () => {
    process.removeListener("SIGINT", onInterrupt);
    process.removeListener("SIGTERM", onTerminate);
    for (const { server } of reservations) {
      if (server.listening) server.close();
    }
    signalChildren("SIGTERM");
    await Promise.all(
      children.map(async ({ process, done }) => {
        const exited = await Promise.race([done.then(() => true), delay(5000).then(() => false)]);
        if (!exited && process.pid) {
          try {
            globalThis.process.kill(-process.pid, "SIGKILL");
          } catch (error) {
            if (error.code !== "ESRCH") throw error;
          }
          await done;
        }
      }),
    );
    await log.close();
    await rm(directory, { recursive: true, force: true });
  };
  stopServices = cleanup;
  process.once("SIGINT", onInterrupt);
  process.once("SIGTERM", onTerminate);

  try {
    for (let i = 0; i < 3; i++) {
      const reservation = await reservePort();
      reservations.push(reservation);
      if (stopping) {
        reservation.server.close();

        throw new Error("Browser setup interrupted");
      }
    }
    const [processor, api, web] = reservations;
    const base = `http://127.0.0.1:${web.port}`;
    process.env.PLAYGROUND_BROWSER_URL = base;
    const env = {
      ...process.env,
      PROCESSOR_URL: `http://127.0.0.1:${processor.port}`,
      IMAGE_API_URL: `http://127.0.0.1:${api.port}`,
      BIND_ADDRESS: `127.0.0.1:${api.port}`,
      DATA_DIR: directory,
      PUBLIC_ORIGIN: base,
      NEXT_TELEMETRY_DISABLED: "1",
    };
    const commands = [
      [
        join(root, "python/.venv/bin/python"),
        "-m",
        "uvicorn",
        "image_processor.main:create_app",
        "--factory",
        "--host",
        "127.0.0.1",
        "--port",
        String(processor.port),
      ],
      [join(root, "rust/target/release/image-api")],
      [
        process.execPath,
        join(root, "node/apps/web/node_modules/next/dist/bin/next"),
        "start",
        join(root, "node/apps/web"),
        "--hostname",
        "127.0.0.1",
        "--port",
        String(web.port),
      ],
    ];
    for (const [index, command] of commands.entries()) {
      await new Promise((resolve) => reservations[index].server.close(resolve));
      if (stopping) throw new Error("Browser setup interrupted");
      const child = spawn(command[0], command.slice(1), {
        cwd: root,
        env,
        detached: true,
        stdio: ["ignore", log.fd, log.fd],
      });
      const entry = { process: child, error: null };
      entry.done = new Promise((resolve) => {
        child.once("error", (error) => {
          entry.error = error;
          resolve();
        });
        child.once("exit", resolve);
      });
      children.push(entry);
    }
    for (const { port } of reservations) {
      const deadline = Date.now() + 60_000;
      let ready = false;
      while (Date.now() < deadline) {
        if (stopping) throw new Error("Browser setup interrupted");
        const failed = children.find(
          ({ process, error }) => error || process.exitCode !== null || process.signalCode !== null,
        );
        if (failed)
          throw new Error(
            `Service exited: ${failed.error ?? failed.process.exitCode}; logs: ${logPath}`,
          );
        try {
          const response = await fetch(`http://127.0.0.1:${port}/healthz`, {
            signal: AbortSignal.timeout(1500),
          });
          if (response.ok) {
            ready = true;

            break;
          }
        } catch {
          /* The service may still be starting. */
        }
        await delay(200);
      }
      if (!ready) throw new Error(`Service on port ${port} did not become ready; logs: ${logPath}`);
    }
    console.log(`Disposable browser environment: ${base}; logs: ${logPath}`);
  } catch (error) {
    await cleanup();

    throw error;
  }
}
