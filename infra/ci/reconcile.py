"""Deploy verified commits using the chart from the trusted default branch."""

import base64
import json
import os
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path

REPOSITORY = "neoplasmes/env-playground"
ROOT = Path(__file__).resolve().parents[2]
SLOTS = ["preview-1", "preview-2", "preview-3"]
IMAGES = {
    "web": "node/apps/web",
    "api": "rust/apps/image_api",
    "processor": "python/apps/image_processor",
}


def run(*args, content=None, cwd=ROOT, env=None):
    return subprocess.run(
        args,
        input=content,
        text=True,
        capture_output=True,
        check=True,
        cwd=cwd,
        env=env,
    ).stdout


def github(path):
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}/{path}",
        headers={
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def verified(sha):
    statuses = github(f"commits/{sha}/status")["statuses"]
    prefix = os.environ.get("WOODPECKER_STATUS_PREFIX", "ci/woodpecker")
    checks = [
        status
        for status in statuses
        if status["context"]
        in {f"{prefix}/push/checks", f"{prefix}/pull_request/checks"}
    ]

    return bool(checks) and all(check["state"] == "success" for check in checks)


def state(namespace):
    result = run(
        "kubectl",
        "-n",
        namespace,
        "get",
        "configmap",
        "playground-release",
        "--ignore-not-found",
        "-o",
        "json",
    )

    return json.loads(result).get("data", {}) if result.strip() else {}


def deploy(namespace, sha, hostname, pull_request=""):
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("Invalid commit SHA")
    previous = state(namespace)
    if previous.get("sha") == sha and previous.get("pr", "") == pull_request:
        return
    with tempfile.TemporaryDirectory(prefix="playground-build-") as directory:
        source = Path(directory) / "source"
        authorization = base64.b64encode(
            f"x-access-token:{os.environ['GITHUB_TOKEN']}".encode()
        ).decode()
        git_env = dict(
            os.environ,
            GIT_TERMINAL_PROMPT="0",
            GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
            GIT_CONFIG_VALUE_0=f"Authorization: Basic {authorization}",
        )
        run(
            "git",
            "clone",
            "--quiet",
            "--no-checkout",
            f"https://github.com/{REPOSITORY}.git",
            str(source),
            env=git_env,
        )
        run(
            "git",
            "fetch",
            "--quiet",
            "--depth=1",
            "origin",
            sha,
            cwd=source,
            env=git_env,
        )
        run(
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "checkout",
            "--quiet",
            "--detach",
            sha,
            cwd=source,
        )
        images = {}
        for name, app in IMAGES.items():
            if not (source / app / "Dockerfile").resolve().is_relative_to(source):
                raise ValueError(
                    "Dockerfile must stay inside the checked-out repository"
                )
            metadata = Path(directory) / f"{name}.json"
            tag = f"ghcr.io/{REPOSITORY}-{name}:{sha}"
            tls = Path(os.environ["BUILDKIT_TLS_DIR"])
            subprocess.run(
                [
                    "buildctl",
                    "--addr",
                    "tcp://buildkit.platform.svc:1234",
                    "--tlscacert",
                    str(tls / "ca.pem"),
                    "--tlscert",
                    str(tls / "cert.pem"),
                    "--tlskey",
                    str(tls / "key.pem"),
                    "build",
                    "--frontend",
                    "dockerfile.v0",
                    "--local",
                    f"context={source}",
                    "--local",
                    f"dockerfile={source / app}",
                    "--opt",
                    "filename=Dockerfile",
                    "--opt",
                    "BUILDKIT_SYNTAX=docker/dockerfile:1.7",
                    "--output",
                    f"type=image,name={tag},push=true",
                    "--metadata-file",
                    str(metadata),
                ],
                check=True,
            )
            digest = json.loads(metadata.read_text())["containerimage.digest"]
            if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
                raise ValueError("Invalid image digest")
            images[name] = f"ghcr.io/{REPOSITORY}-{name}@{digest}"
        if pull_request:
            current = github(f"pulls/{pull_request}")
            if current["state"] != "open" or current["head"]["sha"] != sha:
                print(
                    f"PR {pull_request} changed during build; skipping stale deployment"
                )

                return
        elif github("commits/master")["sha"] != sha:
            print("Default branch changed during build; skipping stale deployment")

            return
        values = {"images": images, "host": hostname, "revision": sha}
        values_file = Path(directory) / "values.json"
        values_file.write_text(json.dumps(values))
        if not previous:
            pending = {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": "playground-release", "namespace": namespace},
                "data": {"sha": "", "pr": pull_request},
            }
            run("kubectl", "apply", "-f", "-", content=json.dumps(pending))
        subprocess.run(
            [
                "helm",
                "upgrade",
                "--install",
                "image-lab",
                str(ROOT / "infra/charts/image-lab"),
                "--namespace",
                namespace,
                "--values",
                str(values_file),
                "--wait",
                "--timeout",
                "5m",
                "--rollback-on-failure",
                "--history-max",
                "3",
            ],
            check=True,
        )
        record = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "playground-release", "namespace": namespace},
            "data": {"sha": sha, "pr": pull_request, "values": json.dumps(values)},
        }
        run("kubectl", "apply", "-f", "-", content=json.dumps(record))
        print(f"Deployed {sha[:12]} to https://{hostname}")


def main():
    domain = os.environ["PLAYGROUND_DOMAIN"]
    if not re.fullmatch(r"[0-9-]+\.sslip\.io", domain):
        raise ValueError("Unexpected playground domain")
    pulls = []
    page = 1
    while True:
        batch = github(f"pulls?state=open&per_page=100&page={page}")
        pulls.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    active = {
        str(pr["number"]): pr
        for pr in pulls
        if pr["head"].get("repo")
        and pr["head"]["repo"]["full_name"] == REPOSITORY
        and not pr["draft"]
    }
    occupied = {}
    for slot in SLOTS:
        number = state(slot).get("pr")
        if number and number not in active:
            run(
                "helm",
                "uninstall",
                "image-lab",
                "--namespace",
                slot,
                "--ignore-not-found",
                "--wait",
            )
            run(
                "kubectl",
                "-n",
                slot,
                "delete",
                "configmap",
                "playground-release",
                "--ignore-not-found",
            )
            print(f"Removed closed/draft PR {number} from {slot}")
        elif number:
            occupied[slot] = number
    sha = github("commits/master")["sha"]
    if verified(sha):
        deploy("dev", sha, f"dev.{domain}")
    for number, pr in sorted(active.items(), key=lambda item: int(item[0])):
        slot = next(
            (slot for slot, existing in occupied.items() if existing == number), None
        )
        if slot is None:
            slot = next((slot for slot in SLOTS if slot not in occupied), None)
        if slot is None:
            print(f"PR {number} queued: all three preview slots are occupied")

            continue
        if verified(pr["head"]["sha"]):
            deploy(slot, pr["head"]["sha"], f"pr-{number}.{domain}", number)
            occupied[slot] = number


if __name__ == "__main__":
    main()
