use crate::app::{AppResult, ports::JobRepo};
use crate::core::entities::Job;
use std::sync::Arc;
pub struct GetJob(pub Arc<dyn JobRepo>);
impl GetJob {
    pub fn execute(&self, id: &str) -> AppResult<Job> {
        self.0.get(id)
    }
}
