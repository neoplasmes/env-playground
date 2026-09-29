use super::Transformation;

#[derive(Clone, Debug)]
pub struct Job {
    pub id: String,
    pub status: String,
    pub transformation: Transformation,
    pub error: Option<String>,
    pub created_at: i64,
}

pub struct NewJob {
    pub id: String,
    pub idempotency_key: String,
    pub fingerprint: String,
    pub transformation: Transformation,
    pub source: Vec<u8>,
}

pub struct ProcessingJob {
    pub job: Job,
    pub source: Vec<u8>,
}
