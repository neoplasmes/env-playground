use crate::app::{AppError, AppResult, ports::JobRepo};
use crate::core::entities::{Job, NewJob, Transformation};
use crate::core::processes::validate_transformation::validate_transformation;
use sha2::{Digest, Sha256};
use std::sync::Arc;

pub struct CreateJob(pub Arc<dyn JobRepo>);

impl CreateJob {
    pub fn execute(
        &self,
        key: String,
        settings: Transformation,
        source: Vec<u8>,
    ) -> AppResult<Job> {
        validate_transformation(&settings).map_err(|e| AppError::Invalid(e.into()))?;
        if key.is_empty() || key.len() > 128 || !key.is_ascii() {
            return Err(AppError::Invalid(
                "A valid Idempotency-Key is required".into(),
            ));
        }
        if source.is_empty() || source.len() > 10 * 1024 * 1024 {
            return Err(AppError::Invalid(
                "Upload must contain 1 byte to 10 MiB".into(),
            ));
        }
        let mut hash = Sha256::new();
        hash.update(format!(
            "{}:{}:{}:",
            settings.width, settings.height, settings.format
        ));
        hash.update(&source);
        self.0.create(NewJob {
            id: uuid::Uuid::new_v4().to_string(),
            idempotency_key: key,
            fingerprint: hash
                .finalize()
                .iter()
                .map(|byte| format!("{byte:02x}"))
                .collect(),
            transformation: settings,
            source,
        })
    }
}
