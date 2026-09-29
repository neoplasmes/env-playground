use crate::app::{AppError, AppResult, ports::JobRepo};
use std::sync::Arc;
pub struct GetResult(pub Arc<dyn JobRepo>);
impl GetResult {
    pub fn execute(&self, id: &str) -> AppResult<(Vec<u8>, String)> {
        let job = self.0.get(id)?;
        if job.status != "succeeded" {
            return Err(AppError::NotReady);
        }
        Ok((
            self.0.result(id)?,
            format!("image/{}", job.transformation.format),
        ))
    }
}
