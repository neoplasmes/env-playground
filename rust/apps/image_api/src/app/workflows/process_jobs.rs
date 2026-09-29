use crate::app::{
    AppError, AppResult,
    ports::{JobRepo, ProcessorClient},
};
use std::{sync::Arc, time::Duration};

pub async fn process_jobs(
    repo: Arc<dyn JobRepo>,
    processor: Arc<dyn ProcessorClient>,
) -> AppResult<()> {
    loop {
        let db = repo.clone();
        let next = tokio::task::spawn_blocking(move || db.claim())
            .await
            .map_err(anyhow::Error::from)??;
        if let Some(next) = next {
            let result = processor
                .transform(next.source, &next.job.transformation)
                .await;
            let db = repo.clone();
            tokio::task::spawn_blocking(move || match result {
                Ok(bytes) => db.complete(&next.job.id, &bytes),
                Err(reason) => db.fail(&next.job.id, &reason),
            })
            .await
            .map_err(|e| AppError::Internal(e.into()))??;
        } else {
            tokio::time::sleep(Duration::from_millis(500)).await;
        }
    }
}
