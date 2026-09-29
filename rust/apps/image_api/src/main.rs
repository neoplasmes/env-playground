use image_api::{
    api::{ApiState, router},
    app::{
        ports::JobRepo,
        use_cases::{
            create_job::CreateJob, get_job::GetJob, get_result::GetResult, list_jobs::ListJobs,
        },
        workflows::process_jobs,
    },
    env::{HttpProcessor, SqliteJobRepo},
};
use std::{path::PathBuf, sync::Arc};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("image_api=info")
        .init();
    let dir =
        PathBuf::from(std::env::var("DATA_DIR").unwrap_or_else(|_| ".local/image-api".into()));
    std::fs::create_dir_all(&dir)?;
    let repo: Arc<dyn JobRepo> = Arc::new(SqliteJobRepo::open(&dir.join("jobs.sqlite"), 50)?);
    let processor = Arc::new(HttpProcessor::new(
        &std::env::var("PROCESSOR_URL").unwrap_or_else(|_| "http://127.0.0.1:8081".into()),
    )?);
    let state = ApiState {
        create: Arc::new(CreateJob(repo.clone())),
        get: Arc::new(GetJob(repo.clone())),
        list: Arc::new(ListJobs(repo.clone())),
        result: Arc::new(GetResult(repo.clone())),
    };
    let listener = tokio::net::TcpListener::bind(
        std::env::var("BIND_ADDRESS").unwrap_or_else(|_| "0.0.0.0:8080".into()),
    )
    .await?;
    tokio::select! {
        result = axum::serve(listener, router(state)).with_graceful_shutdown(async { let _ = tokio::signal::ctrl_c().await; }) => result?,
        result = process_jobs(repo, processor) => { result?; }
    }
    Ok(())
}
