use crate::app::AppResult;
use crate::core::entities::{Job, NewJob, ProcessingJob};

pub trait JobRepo: Send + Sync {
    fn create(&self, job: NewJob) -> AppResult<Job>;
    fn list(&self) -> AppResult<Vec<Job>>;
    fn get(&self, id: &str) -> AppResult<Job>;
    fn result(&self, id: &str) -> AppResult<Vec<u8>>;
    fn claim(&self) -> AppResult<Option<ProcessingJob>>;
    fn complete(&self, id: &str, result: &[u8]) -> AppResult<()>;
    fn fail(&self, id: &str, reason: &str) -> AppResult<()>;
}
