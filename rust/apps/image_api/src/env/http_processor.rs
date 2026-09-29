use crate::app::ports::ProcessorClient;
use crate::core::entities::Transformation;
use async_trait::async_trait;
use std::time::Duration;

pub struct HttpProcessor {
    client: reqwest::Client,
    url: String,
}

impl HttpProcessor {
    pub fn new(base: &str) -> anyhow::Result<Self> {
        let url = reqwest::Url::parse(base)?;
        anyhow::ensure!(
            url.scheme() == "http",
            "Processor must use an internal HTTP address"
        );
        Ok(Self {
            client: reqwest::Client::builder()
                .timeout(Duration::from_secs(60))
                .build()?,
            url: format!("{}/v1/transform", base.trim_end_matches('/')),
        })
    }
}

#[async_trait]
impl ProcessorClient for HttpProcessor {
    async fn transform(
        &self,
        source: Vec<u8>,
        settings: &Transformation,
    ) -> Result<Vec<u8>, String> {
        for attempt in 0..3 {
            let response = self
                .client
                .post(&self.url)
                .query(&[
                    ("width", settings.width.to_string()),
                    ("height", settings.height.to_string()),
                    ("format", settings.format.clone()),
                ])
                .header("Content-Type", "application/octet-stream")
                .body(source.clone())
                .send()
                .await;
            match response {
                Ok(response) if response.status().is_success() => {
                    let mut response = response;
                    let mut output = Vec::new();
                    while let Some(chunk) = response
                        .chunk()
                        .await
                        .map_err(|_| "Cannot read processing result")?
                    {
                        if output.len() + chunk.len() > 80 * 1024 * 1024 {
                            return Err("Processing result too large".into());
                        }
                        output.extend_from_slice(&chunk);
                    }

                    return Ok(output);
                }
                Ok(response)
                    if response.status().is_client_error() && response.status().as_u16() != 429 =>
                {
                    return Err("Image rejected: use a valid non-animated PNG, JPEG or WebP up to 16 megapixels".into());
                }
                _ if attempt < 2 => tokio::time::sleep(Duration::from_secs(1 << attempt)).await,
                _ => return Err("Image processor is unavailable; submit a new job later".into()),
            }
        }
        unreachable!()
    }
}
