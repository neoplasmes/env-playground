"""Exercise Next.js/BFF -> Rust -> Python with real HTTP and disposable data."""

import io
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))

        return listener.getsockname()[1]


def request(url, data=None, headers=None):
    with urllib.request.urlopen(
        urllib.request.Request(url, data=data, headers=headers or {}), timeout=5
    ) as response:
        return response.read()


def main():
    processes = []
    with tempfile.TemporaryDirectory(prefix="playground-smoke-") as directory:
        processor_port, api_port, web_port = port(), port(), port()
        base = f"http://127.0.0.1:{web_port}"
        env = dict(
            os.environ,
            PROCESSOR_URL=f"http://127.0.0.1:{processor_port}",
            IMAGE_API_URL=f"http://127.0.0.1:{api_port}",
            BIND_ADDRESS=f"127.0.0.1:{api_port}",
            DATA_DIR=directory,
            PUBLIC_ORIGIN=base,
            NEXT_TELEMETRY_DISABLED="1",
        )
        log = Path(directory) / "services.log"
        with log.open("w") as output:
            try:
                for command in [
                    [
                        str(ROOT / "python/.venv/bin/python"),
                        "-m",
                        "uvicorn",
                        "image_processor.main:create_app",
                        "--factory",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(processor_port),
                    ],
                    [str(ROOT / "rust/target/release/image-api")],
                    [
                        "pnpm",
                        "--dir",
                        "node/apps/web",
                        "start",
                        "--hostname",
                        "127.0.0.1",
                        "--port",
                        str(web_port),
                    ],
                ]:
                    processes.append(
                        subprocess.Popen(
                            command,
                            env=env,
                            cwd=ROOT,
                            stdout=output,
                            stderr=subprocess.STDOUT,
                            start_new_session=True,
                        )
                    )
                for service_port in [processor_port, api_port, web_port]:
                    for _ in range(120):
                        try:
                            request(f"http://127.0.0.1:{service_port}/healthz")

                            break
                        except (urllib.error.URLError, TimeoutError):
                            time.sleep(0.25)
                    else:
                        raise AssertionError(f"Service {service_port} did not start")
                source = io.BytesIO()
                Image.new("RGB", (40, 20), "green").save(source, "PNG")
                for format_name in ["png", "jpeg", "webp"]:
                    url = f"{base}/api/jobs?width=20&height=20&format={format_name}"
                    headers = {
                        "Content-Type": "application/octet-stream",
                        "Idempotency-Key": format_name,
                        "Origin": base,
                    }
                    job = json.loads(request(url, source.getvalue(), headers))
                    duplicate = json.loads(request(url, source.getvalue(), headers))
                    assert duplicate["id"] == job["id"]
                    for _ in range(100):
                        result = json.loads(request(f"{base}/api/jobs/{job['id']}"))
                        if result["status"] in {"succeeded", "failed"}:
                            break
                        time.sleep(0.1)
                    assert result["status"] == "succeeded", result
                    image = Image.open(
                        io.BytesIO(request(f"{base}/api/jobs/{job['id']}/result"))
                    )
                    assert (
                        image.size == (20, 10) and image.format == format_name.upper()
                    )
                assert len(json.loads(request(f"{base}/api/jobs"))) == 3
                print(
                    "HTTP smoke passed: upload, idempotency, polling, resize and PNG/JPEG/WebP download"
                )
            except Exception:
                print(log.read_text())

                raise
            finally:
                import signal

                for process in processes:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGTERM)
                for process in processes:
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()


if __name__ == "__main__":
    main()
