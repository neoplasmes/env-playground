# syntax=docker/dockerfile:1.7
FROM rust:1.98.1-slim AS build
WORKDIR /workspace/rust
COPY rust/Cargo.toml rust/Cargo.lock rust/rust-toolchain.toml ./
COPY rust/apps/image_api apps/image_api
RUN --mount=type=cache,target=/usr/local/cargo/registry --mount=type=cache,target=/workspace/rust/target cargo build --release --locked && cp target/release/image-api /image-api

FROM debian:trixie-slim
RUN groupadd -g 10001 app && useradd -u 10001 -g app app && mkdir /data && chown app:app /data
COPY --from=build /image-api /usr/local/bin/image-api
ENV DATA_DIR=/data PROCESSOR_URL=http://image-processor:8081
USER 10001:10001
EXPOSE 8080
CMD ["image-api"]
