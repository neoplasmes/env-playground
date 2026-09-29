use crate::app::{
    AppError,
    use_cases::{
        create_job::CreateJob, get_job::GetJob, get_result::GetResult, list_jobs::ListJobs,
    },
};
use crate::core::entities::{Job, Transformation};
use axum::{
    Json, Router,
    body::Bytes,
    extract::{DefaultBodyLimit, Path, Query, State},
    http::{HeaderMap, StatusCode, header},
    response::{IntoResponse, Response},
    routing::get,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;

#[derive(Clone)]
pub struct ApiState {
    pub create: Arc<CreateJob>,
    pub get: Arc<GetJob>,
    pub list: Arc<ListJobs>,
    pub result: Arc<GetResult>,
}

#[derive(Deserialize)]
struct Settings {
    width: u32,
    height: u32,
    format: String,
}

#[derive(Serialize)]
struct JobDto {
    id: String,
    status: String,
    width: u32,
    height: u32,
    format: String,
    error: Option<String>,
    created_at: i64,
}
impl From<Job> for JobDto {
    fn from(j: Job) -> Self {
        Self {
            id: j.id,
            status: j.status,
            width: j.transformation.width,
            height: j.transformation.height,
            format: j.transformation.format,
            error: j.error,
            created_at: j.created_at,
        }
    }
}
impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match &self {
            AppError::Invalid(_) => (StatusCode::BAD_REQUEST, self.to_string()),
            AppError::Conflict => (StatusCode::CONFLICT, self.to_string()),
            AppError::NotFound => (StatusCode::NOT_FOUND, self.to_string()),
            AppError::NotReady => (StatusCode::CONFLICT, self.to_string()),
            AppError::Capacity => (StatusCode::TOO_MANY_REQUESTS, self.to_string()),
            AppError::Internal(error) => {
                tracing::error!(%error, "Request failed");
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "Internal server error".into(),
                )
            }
        };
        (status, Json(serde_json::json!({"error": message}))).into_response()
    }
}

pub fn router(state: ApiState) -> Router {
    Router::new()
        .route(
            "/healthz",
            get(|| async { Json(serde_json::json!({"status":"ok"})) }),
        )
        .route("/v1/jobs", get(list).post(create))
        .route("/v1/jobs/{id}", get(find))
        .route("/v1/jobs/{id}/result", get(result))
        .layer(DefaultBodyLimit::max(10 * 1024 * 1024))
        .with_state(state)
}

async fn create(
    State(s): State<ApiState>,
    Query(q): Query<Settings>,
    headers: HeaderMap,
    body: Bytes,
) -> Result<impl IntoResponse, AppError> {
    let key = headers
        .get("Idempotency-Key")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("")
        .to_owned();
    let job = tokio::task::spawn_blocking(move || {
        s.create.execute(
            key,
            Transformation {
                width: q.width,
                height: q.height,
                format: q.format,
            },
            body.to_vec(),
        )
    })
    .await
    .map_err(anyhow::Error::from)??;
    Ok((StatusCode::ACCEPTED, Json(JobDto::from(job))))
}
async fn list(State(s): State<ApiState>) -> Result<Json<Vec<JobDto>>, AppError> {
    let jobs = tokio::task::spawn_blocking(move || s.list.execute())
        .await
        .map_err(anyhow::Error::from)??;
    Ok(Json(jobs.into_iter().map(Into::into).collect()))
}
async fn find(State(s): State<ApiState>, Path(id): Path<String>) -> Result<Json<JobDto>, AppError> {
    let job = tokio::task::spawn_blocking(move || s.get.execute(&id))
        .await
        .map_err(anyhow::Error::from)??;
    Ok(Json(job.into()))
}
async fn result(
    State(s): State<ApiState>,
    Path(id): Path<String>,
) -> Result<impl IntoResponse, AppError> {
    let (content, media) = tokio::task::spawn_blocking(move || s.result.execute(&id))
        .await
        .map_err(anyhow::Error::from)??;
    Ok((
        [
            (header::CONTENT_TYPE, media),
            (header::CONTENT_DISPOSITION, "attachment".into()),
        ],
        content,
    ))
}
