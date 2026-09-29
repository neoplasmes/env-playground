"""Provision the isolated builder and namespace-scoped deployment credentials."""

import base64
import json
import os
import subprocess
import time
from pathlib import Path

from platform_config import STAGES, apply, resource, run

ROOT = Path(__file__).resolve().parents[2]


def certificates():
    directory = ROOT / ".secrets/buildkit"
    directory.mkdir(exist_ok=True)
    if (directory / "server.pem").exists():
        return directory

    def openssl(*args):
        subprocess.run(
            ["openssl", *args], cwd=directory, check=True, capture_output=True
        )

    openssl(
        "req",
        "-x509",
        "-newkey",
        "rsa:3072",
        "-nodes",
        "-days",
        "365",
        "-subj",
        "/CN=playground-buildkit-ca",
        "-keyout",
        "ca.key",
        "-out",
        "ca.pem",
    )
    for name, purpose in [("server", "serverAuth"), ("client", "clientAuth")]:
        openssl(
            "req",
            "-newkey",
            "rsa:3072",
            "-nodes",
            "-subj",
            f"/CN=buildkit-{name}",
            "-keyout",
            f"{name}.key",
            "-out",
            f"{name}.csr",
        )
        extensions = f"extendedKeyUsage={purpose}\n"
        if name == "server":
            extensions += "subjectAltName=DNS:buildkit.platform.svc\n"
        (directory / "extensions.cnf").write_text(extensions)
        openssl(
            "x509",
            "-req",
            "-days",
            "365",
            "-in",
            f"{name}.csr",
            "-CA",
            "ca.pem",
            "-CAkey",
            "ca.key",
            "-CAcreateserial",
            "-extfile",
            "extensions.cnf",
            "-out",
            f"{name}.pem",
        )

    return directory


def main():
    os.umask(0o077)
    certs = certificates()
    apply(
        resource(
            "Secret",
            "buildkit-tls",
            "platform",
            stringData={
                "ca.pem": (certs / "ca.pem").read_text(),
                "server.pem": (certs / "server.pem").read_text(),
                "server.key": (certs / "server.key").read_text(),
            },
        )
    )
    apply(
        resource(
            "Deployment",
            "buildkit",
            "platform",
            "apps/v1",
            spec={
                "replicas": 1,
                "strategy": {"type": "Recreate"},
                "selector": {"matchLabels": {"app": "buildkit"}},
                "template": {
                    "metadata": {"labels": {"app": "buildkit"}},
                    "spec": {
                        "automountServiceAccountToken": False,
                        "securityContext": {
                            "runAsUser": 1000,
                            "runAsGroup": 1000,
                            "fsGroup": 1000,
                        },
                        "containers": [
                            {
                                "name": "buildkit",
                                "image": "moby/buildkit:v0.33.0-rootless",
                                "args": [
                                    "--addr=tcp://0.0.0.0:1234",
                                    "--oci-worker-no-process-sandbox",
                                    "--tlscacert=/tls/ca.pem",
                                    "--tlscert=/tls/server.pem",
                                    "--tlskey=/tls/server.key",
                                ],
                                "ports": [{"containerPort": 1234}],
                                "securityContext": {
                                    "seccompProfile": {"type": "Unconfined"},
                                    "appArmorProfile": {"type": "Unconfined"},
                                },
                                "resources": {
                                    "requests": {"cpu": "500m", "memory": "512Mi"},
                                    "limits": {"cpu": "2", "memory": "3Gi"},
                                },
                                "volumeMounts": [
                                    {
                                        "name": "tls",
                                        "mountPath": "/tls",
                                        "readOnly": True,
                                    },
                                    {
                                        "name": "cache",
                                        "mountPath": "/home/user/.local/share/buildkit",
                                    },
                                ],
                            }
                        ],
                        "volumes": [
                            {
                                "name": "tls",
                                "secret": {
                                    "secretName": "buildkit-tls",
                                    "defaultMode": 0o440,
                                },
                            },
                            {"name": "cache", "emptyDir": {"sizeLimit": "12Gi"}},
                        ],
                    },
                },
            },
        ),
        resource(
            "Service",
            "buildkit",
            "platform",
            spec={"selector": {"app": "buildkit"}, "ports": [{"port": 1234}]},
        ),
        resource("ServiceAccount", "deployer", "platform"),
    )
    for namespace in STAGES:
        run(
            "kubectl",
            "label",
            "namespace",
            namespace,
            "pod-security.kubernetes.io/enforce=baseline",
            "--overwrite",
        )
        apply(
            resource(
                "Role",
                "deployer",
                namespace,
                "rbac.authorization.k8s.io/v1",
                rules=[
                    {
                        "apiGroups": [""],
                        "resources": [
                            "services",
                            "configmaps",
                            "secrets",
                            "persistentvolumeclaims",
                        ],
                        "verbs": [
                            "get",
                            "list",
                            "watch",
                            "create",
                            "update",
                            "patch",
                            "delete",
                        ],
                    },
                    {
                        "apiGroups": [""],
                        "resources": ["pods", "events"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["apps"],
                        "resources": ["deployments", "replicasets"],
                        "verbs": [
                            "get",
                            "list",
                            "watch",
                            "create",
                            "update",
                            "patch",
                            "delete",
                        ],
                    },
                    {
                        "apiGroups": ["networking.k8s.io"],
                        "resources": ["ingresses", "networkpolicies"],
                        "verbs": [
                            "get",
                            "list",
                            "watch",
                            "create",
                            "update",
                            "patch",
                            "delete",
                        ],
                    },
                    {
                        "apiGroups": ["traefik.io"],
                        "resources": ["middlewares"],
                        "verbs": [
                            "get",
                            "list",
                            "watch",
                            "create",
                            "update",
                            "patch",
                            "delete",
                        ],
                    },
                ],
            ),
            resource(
                "RoleBinding",
                "deployer",
                namespace,
                "rbac.authorization.k8s.io/v1",
                roleRef={
                    "apiGroup": "rbac.authorization.k8s.io",
                    "kind": "Role",
                    "name": "deployer",
                },
                subjects=[
                    {
                        "kind": "ServiceAccount",
                        "name": "deployer",
                        "namespace": "platform",
                    }
                ],
            ),
        )
    secret = resource(
        "Secret",
        "deployer-token",
        "platform",
        type="kubernetes.io/service-account-token",
    )
    secret["metadata"]["annotations"] = {
        "kubernetes.io/service-account.name": "deployer"
    }
    apply(secret)
    for _ in range(20):
        result = json.loads(
            run(
                "kubectl",
                "-n",
                "platform",
                "get",
                "secret",
                "deployer-token",
                "-o",
                "json",
            )
        )
        if "token" in result.get("data", {}):
            break
        time.sleep(1)
    else:
        raise RuntimeError("Service account token was not generated")
    config = {
        "apiVersion": "v1",
        "kind": "Config",
        "current-context": "playground",
        "clusters": [
            {
                "name": "playground",
                "cluster": {
                    "server": "https://kubernetes.default.svc",
                    "certificate-authority-data": result["data"]["ca.crt"],
                },
            }
        ],
        "users": [
            {
                "name": "deployer",
                "user": {"token": base64.b64decode(result["data"]["token"]).decode()},
            }
        ],
        "contexts": [
            {
                "name": "playground",
                "context": {"cluster": "playground", "user": "deployer"},
            }
        ],
    }
    (ROOT / ".secrets/deploy-kubeconfig.json").write_text(json.dumps(config))
    run(
        "kubectl",
        "-n",
        "platform",
        "rollout",
        "status",
        "deployment/buildkit",
        "--timeout=300s",
    )
    print(
        "Builder ready. Add the restricted CI secrets described in README.md; never enable them for PR events."
    )


if __name__ == "__main__":
    main()
