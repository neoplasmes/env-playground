"""Bootstrap k3s from Terraform outputs without storing cluster tokens in Terraform."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
K3S_VERSION = "v1.37.0+k3s1"


def run(args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def remote(ip, command, content=None, capture=False):
    return run(
        [
            "ssh",
            "-i",
            str(ROOT / ".secrets/id_ed25519"),
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            f"UserKnownHostsFile={ROOT / '.local/known_hosts'}",
            f"ubuntu@{ip}",
            command,
        ],
        input=content,
        capture_output=capture,
    )


def main():
    os.umask(0o077)
    output = json.loads(
        run(
            ["terraform", "-chdir=infra/terraform", "output", "-json"],
            cwd=ROOT,
            capture_output=True,
        ).stdout
    )
    nodes = output["nodes"]["value"]
    control = nodes["control"]
    for node in nodes.values():
        remote(node["public_ip"], "sudo cloud-init status --wait")
    domain = output["base_domain"]["value"]
    config = {
        "node-name": "env-playground-control",
        "node-ip": control["private_ip"],
        "tls-san": [control["public_ip"], f"ci.{domain}"],
        "write-kubeconfig-mode": "0600",
        "secrets-encryption": True,
    }
    remote(
        control["public_ip"],
        "sudo mkdir -p /etc/rancher/k3s && sudo tee /etc/rancher/k3s/config.yaml >/dev/null",
        json.dumps(config),
    )
    remote(
        control["public_ip"],
        f"curl -sfL https://get.k3s.io -o /tmp/install-k3s.sh && sudo env INSTALL_K3S_VERSION='{K3S_VERSION}' sh /tmp/install-k3s.sh server",
    )
    token = remote(
        control["public_ip"],
        "sudo cat /var/lib/rancher/k3s/server/node-token",
        capture=True,
    ).stdout.strip()
    for name, node in nodes.items():
        if name == "control":
            continue
        config = {
            "node-name": f"env-playground-{name}",
            "node-ip": node["private_ip"],
            "server": f"https://{control['private_ip']}:6443",
            "token": token,
        }
        remote(
            node["public_ip"],
            "sudo mkdir -p /etc/rancher/k3s && sudo sh -c 'umask 077; cat > /etc/rancher/k3s/config.yaml'",
            json.dumps(config),
        )
        remote(
            node["public_ip"],
            f"curl -sfL https://get.k3s.io -o /tmp/install-k3s.sh && sudo env INSTALL_K3S_VERSION='{K3S_VERSION}' sh /tmp/install-k3s.sh agent",
        )
    kubeconfig = remote(
        control["public_ip"], "sudo cat /etc/rancher/k3s/k3s.yaml", capture=True
    ).stdout
    (ROOT / ".secrets/kubeconfig").write_text(
        kubeconfig.replace("127.0.0.1", control["public_ip"])
    )
    env = dict(os.environ, KUBECONFIG=str(ROOT / ".secrets/kubeconfig"))
    run(
        [
            "kubectl",
            "wait",
            "--for=condition=Ready",
            "nodes",
            "--all",
            "--timeout=300s",
        ],
        env=env,
    )
    print(f"Кластер готов. Следующий шаг: OAuth App для https://ci.{domain}/authorize")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError:
        sys.exit("Bootstrap failed; fix the reported command and rerun.")
