#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("{0}")]
    Invalid(String),
    #[error("Idempotency key already belongs to a different request")]
    Conflict,
    #[error("Job not found")]
    NotFound,
    #[error("Result is not ready")]
    NotReady,
    #[error("Environment job limit reached")]
    Capacity,
    #[error(transparent)]
    Internal(#[from] anyhow::Error),
}
pub type AppResult<T> = Result<T, AppError>;
