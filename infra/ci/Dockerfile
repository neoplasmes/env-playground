# syntax=docker/dockerfile:1.7
FROM moby/buildkit:v0.33.0 AS buildkit
FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git xz-utils unzip build-essential pkg-config openssl && rm -rf /var/lib/apt/lists/*
ARG PROTO_VERSION=0.62.3
RUN curl -fsSL "https://github.com/moonrepo/proto/releases/download/v${PROTO_VERSION}/proto_cli-x86_64-unknown-linux-gnu.tar.xz" -o /tmp/proto.tar.xz \
    && mkdir /tmp/proto && tar -xJf /tmp/proto.tar.xz -C /tmp/proto --strip-components=1 \
    && install /tmp/proto/proto /usr/local/bin/proto && install /tmp/proto/proto-shim /usr/local/bin/proto-shim \
    && rm -rf /tmp/proto /tmp/proto.tar.xz
ENV PROTO_HOME=/opt/proto CARGO_HOME=/opt/cargo RUSTUP_HOME=/opt/rustup PROTO_OFFLINE=false
ENV PROTO_NODE_VERSION=26.10.0
ENV PATH="/opt/proto/bin:/opt/proto/shims:/opt/cargo/bin:$PATH"
WORKDIR /opt/toolchain
COPY .prototools .prototools
COPY infra/proto infra/proto
RUN proto install && chmod -R a+rX /opt/proto /opt/cargo /opt/rustup
COPY --from=buildkit /usr/bin/buildctl /usr/local/bin/buildctl
WORKDIR /workspace
