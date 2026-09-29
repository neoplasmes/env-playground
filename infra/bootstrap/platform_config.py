"""Create the shared platform from local credentials; never print secret values."""

import base64
import json
import os
import secrets
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGES = ["dev", "prod", "preview-1", "preview-2", "preview-3"]


def run(*args, content=None):
    return subprocess.run(
        args, input=content, text=True, check=True, capture_output=True
    ).stdout


def resource(kind, name, namespace=None, api="v1", **fields):
    metadata = {"name": name}
    if namespace:
        metadata["namespace"] = namespace

    return {"apiVersion": api, "kind": kind, "metadata": metadata, **fields}


def apply(*items):
    run(
        "kubectl",
        "apply",
        "-f",
        "-",
        content=json.dumps({"apiVersion": "v1", "kind": "List", "items": items}),
    )


def deployment(name, image, env, port, *, claim=None, service_account=None):
    container = {
        "name": name,
        "image": image,
        "env": [{"name": k, "value": v} for k, v in env.items()],
        "resources": {
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "1", "memory": "512Mi"},
        },
    }
    pod = {
        "containers": [container],
        "automountServiceAccountToken": bool(service_account),
    }
    if service_account:
        pod["serviceAccountName"] = service_account
    if claim:
        container["volumeMounts"] = [
            {"name": "data", "mountPath": "/var/lib/woodpecker"}
        ]
        pod["volumes"] = [
            {"name": "data", "persistentVolumeClaim": {"claimName": claim}}
        ]
    container["envFrom"] = [{"secretRef": {"name": name}}]
    if port:
        container["ports"] = [{"containerPort": port, "name": "http"}]
        container["readinessProbe"] = {"httpGet": {"path": "/healthz", "port": port}}

    return resource(
        "Deployment",
        name,
        "platform",
        "apps/v1",
        spec={
            "replicas": 1,
            "strategy": {"type": "Recreate"},
            "selector": {"matchLabels": {"app": name}},
            "template": {"metadata": {"labels": {"app": name}}, "spec": pod},
        },
    )


def main():
    os.umask(0o077)
    domain = json.loads(
        run("terraform", "-chdir=infra/terraform", "output", "-json", "base_domain")
    )
    for namespace in ["platform", "ci-jobs", *STAGES]:
        apply(resource("Namespace", namespace))
    registry = base64.b64encode(
        f"{os.environ['REGISTRY_USER']}:{os.environ['REGISTRY_TOKEN']}".encode()
    ).decode()
    docker_config = json.dumps({"auths": {"ghcr.io": {"auth": registry}}})
    apply(
        resource(
            "Secret",
            "registry",
            "ci-jobs",
            type="kubernetes.io/dockerconfigjson",
            stringData={".dockerconfigjson": docker_config},
        )
    )
    password_file = ROOT / ".secrets/playground-password"
    if not password_file.exists():
        password_file.write_text(secrets.token_urlsafe(24))
    password = password_file.read_text().strip()
    password_hash = run(
        "openssl", "passwd", "-apr1", "-stdin", content=password
    ).strip()
    for namespace in STAGES:
        apply(
            resource(
                "Secret",
                "registry",
                namespace,
                type="kubernetes.io/dockerconfigjson",
                stringData={".dockerconfigjson": docker_config},
            ),
            resource(
                "Secret",
                "playground-auth",
                namespace,
                stringData={"users": f"playground:{password_hash}"},
            ),
            resource(
                "ServiceAccount",
                "default",
                namespace,
                automountServiceAccountToken=False,
            ),
            resource(
                "ResourceQuota",
                "budget",
                namespace,
                spec={
                    "hard": {
                        "requests.cpu": "2",
                        "requests.memory": "2Gi",
                        "limits.cpu": "4",
                        "limits.memory": "3Gi",
                        "persistentvolumeclaims": "2",
                        "requests.storage": "8Gi",
                        "pods": "8",
                    }
                },
            ),
            resource(
                "LimitRange",
                "defaults",
                namespace,
                spec={
                    "limits": [
                        {
                            "type": "Container",
                            "default": {"cpu": "1", "memory": "768Mi"},
                            "defaultRequest": {"cpu": "50m", "memory": "64Mi"},
                        }
                    ]
                },
            ),
        )
    apply(
        resource(
            "ClusterIssuer",
            "letsencrypt",
            api="cert-manager.io/v1",
            spec={
                "acme": {
                    "email": os.environ["ACME_EMAIL"],
                    "server": "https://acme-v02.api.letsencrypt.org/directory",
                    "privateKeySecretRef": {"name": "letsencrypt-account"},
                    "solvers": [
                        {"http01": {"ingress": {"ingressClassName": "traefik"}}}
                    ],
                }
            },
        )
    )
    agent_file = ROOT / ".secrets/woodpecker-agent-secret"
    if not agent_file.exists():
        agent_file.write_text(secrets.token_hex(32))
    agent_secret = agent_file.read_text().strip()
    apply(
        resource(
            "Secret",
            "woodpecker-server",
            "platform",
            stringData={
                "WOODPECKER_AGENT_SECRET": agent_secret,
                "WOODPECKER_GITHUB_CLIENT": os.environ["WOODPECKER_GITHUB_CLIENT"],
                "WOODPECKER_GITHUB_SECRET": os.environ["WOODPECKER_GITHUB_SECRET"],
            },
        ),
        resource(
            "Secret",
            "woodpecker-agent",
            "platform",
            stringData={"WOODPECKER_AGENT_SECRET": agent_secret},
        ),
        resource(
            "PersistentVolumeClaim",
            "woodpecker",
            "platform",
            spec={
                "accessModes": ["ReadWriteOnce"],
                "storageClassName": "local-path",
                "resources": {"requests": {"storage": "2Gi"}},
            },
        ),
        resource("ServiceAccount", "woodpecker-agent", "platform"),
        resource(
            "ServiceAccount",
            "default",
            "ci-jobs",
            automountServiceAccountToken=False,
            imagePullSecrets=[{"name": "registry"}],
        ),
        resource(
            "Role",
            "woodpecker-agent",
            "ci-jobs",
            "rbac.authorization.k8s.io/v1",
            rules=[
                {
                    "apiGroups": [""],
                    "resources": [
                        "pods",
                        "pods/log",
                        "pods/exec",
                        "services",
                        "persistentvolumeclaims",
                    ],
                    "verbs": [
                        "get",
                        "list",
                        "watch",
                        "create",
                        "delete",
                        "patch",
                        "update",
                    ],
                }
            ],
        ),
        resource(
            "RoleBinding",
            "woodpecker-agent",
            "ci-jobs",
            "rbac.authorization.k8s.io/v1",
            roleRef={
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "Role",
                "name": "woodpecker-agent",
            },
            subjects=[
                {
                    "kind": "ServiceAccount",
                    "name": "woodpecker-agent",
                    "namespace": "platform",
                }
            ],
        ),
        deployment(
            "woodpecker-server",
            "woodpeckerci/woodpecker-server:v3.18.1",
            {
                "WOODPECKER_HOST": f"https://ci.{domain}",
                "WOODPECKER_GITHUB": "true",
                "WOODPECKER_OPEN": "false",
                "WOODPECKER_ADMIN": "neoplasmes",
                "WOODPECKER_REPO_OWNERS": "neoplasmes",
                "WOODPECKER_DEFAULT_CLONE_PLUGIN": "woodpeckerci/plugin-git:2.10.1",
            },
            8000,
            claim="woodpecker",
        ),
        deployment(
            "woodpecker-agent",
            "woodpeckerci/woodpecker-agent:v3.18.1",
            {
                "WOODPECKER_SERVER": "woodpecker-server:9000",
                "WOODPECKER_BACKEND": "kubernetes",
                "WOODPECKER_MAX_WORKFLOWS": "1",
                "WOODPECKER_BACKEND_K8S_NAMESPACE": "ci-jobs",
                "WOODPECKER_BACKEND_K8S_VOLUME_SIZE": "12Gi",
                "WOODPECKER_BACKEND_K8S_SERVICE_ACCOUNT_NAME_ALLOW_FROM_STEP": "false",
            },
            None,
            service_account="woodpecker-agent",
        ),
        resource(
            "Service",
            "woodpecker-server",
            "platform",
            spec={
                "selector": {"app": "woodpecker-server"},
                "ports": [
                    {"name": "http", "port": 8000},
                    {"name": "grpc", "port": 9000},
                ],
            },
        ),
    )
    ingress = resource(
        "Ingress",
        "woodpecker",
        "platform",
        "networking.k8s.io/v1",
        spec={
            "ingressClassName": "traefik",
            "tls": [{"hosts": [f"ci.{domain}"], "secretName": "woodpecker-tls"}],
            "rules": [
                {
                    "host": f"ci.{domain}",
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "woodpecker-server",
                                        "port": {"number": 8000},
                                    }
                                },
                            }
                        ]
                    },
                }
            ],
        },
    )
    ingress["metadata"]["annotations"] = {
        "cert-manager.io/cluster-issuer": "letsencrypt",
        "traefik.ingress.kubernetes.io/router.entrypoints": "websecure",
    }
    apply(ingress)
    run(
        "kubectl",
        "-n",
        "platform",
        "rollout",
        "status",
        "deployment/woodpecker-server",
        "--timeout=300s",
    )
    print(
        f"Woodpecker: https://ci.{domain}. App login: playground; password: .secrets/playground-password"
    )


if __name__ == "__main__":
    main()
