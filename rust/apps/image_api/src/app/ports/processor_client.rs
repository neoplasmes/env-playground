use crate::core::entities::Transformation;
use async_trait::async_trait;

#[async_trait]
pub trait ProcessorClient: Send + Sync {
    async fn transform(
        &self,
        source: Vec<u8>,
        settings: &Transformation,
    ) -> Result<Vec<u8>, String>;
}
