"""Promote the exact image digests currently deployed in dev to prod."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    os.environ.setdefault("KUBECONFIG", str(ROOT / ".secrets/kubeconfig"))
    record = json.loads(
        subprocess.check_output(
            [
                "kubectl",
                "-n",
                "dev",
                "get",
                "configmap",
                "playground-release",
                "-o",
                "json",
            ],
            text=True,
        )
    )
    values = json.loads(record["data"]["values"])
    values["host"] = values["host"].replace("dev.", "prod.", 1)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as file:
        json.dump(values, file)
        file.flush()
        subprocess.run(
            [
                "helm",
                "upgrade",
                "--install",
                "image-lab",
                str(ROOT / "infra/charts/image-lab"),
                "--namespace",
                "prod",
                "--values",
                file.name,
                "--wait",
                "--timeout",
                "5m",
                "--rollback-on-failure",
                "--history-max",
                "3",
            ],
            check=True,
        )
    print(f"Promoted {values['revision']} to https://{values['host']}")


if __name__ == "__main__":
    main()
