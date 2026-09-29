use crate::app::{AppResult, ports::JobRepo};
use crate::core::entities::Job;
use std::sync::Arc;
pub struct ListJobs(pub Arc<dyn JobRepo>);
impl ListJobs {
    pub fn execute(&self) -> AppResult<Vec<Job>> {
        self.0.list()
    }
}
