use crate::app::{AppError, AppResult, ports::JobRepo};
use crate::core::entities::{Job, NewJob, ProcessingJob, Transformation};
use rusqlite::{Connection, OptionalExtension, params};
use std::{path::Path, sync::Mutex};

pub struct SqliteJobRepo {
    connection: Mutex<Connection>,
    max_jobs: usize,
}

impl SqliteJobRepo {
    pub fn open(path: &Path, max_jobs: usize) -> anyhow::Result<Self> {
        let connection = Connection::open(path)?;
        connection.busy_timeout(std::time::Duration::from_secs(5))?;
        connection.execute_batch(
            "PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, idempotency_key TEXT NOT NULL UNIQUE,
                fingerprint TEXT NOT NULL, status TEXT NOT NULL,
                width INTEGER NOT NULL, height INTEGER NOT NULL, format TEXT NOT NULL,
                source BLOB NOT NULL, result BLOB, error TEXT,
                created_at INTEGER NOT NULL DEFAULT (unixepoch())
            );
            UPDATE jobs SET status='queued' WHERE status='running';",
        )?;
        Ok(Self {
            connection: Mutex::new(connection),
            max_jobs,
        })
    }

    fn connection(&self) -> AppResult<std::sync::MutexGuard<'_, Connection>> {
        self.connection
            .lock()
            .map_err(|_| AppError::Internal(anyhow::anyhow!("Database mutex poisoned")))
    }
}

fn decode(row: &rusqlite::Row<'_>) -> rusqlite::Result<Job> {
    Ok(Job {
        id: row.get("id")?,
        status: row.get("status")?,
        transformation: Transformation {
            width: row.get("width")?,
            height: row.get("height")?,
            format: row.get("format")?,
        },
        error: row.get("error")?,
        created_at: row.get("created_at")?,
    })
}

fn db_error(error: rusqlite::Error) -> AppError {
    AppError::Internal(error.into())
}

impl JobRepo for SqliteJobRepo {
    fn create(&self, job: NewJob) -> AppResult<Job> {
        let mut connection = self.connection()?;
        let tx = connection.transaction().map_err(db_error)?;
        let existing = tx
            .query_row(
                "SELECT * FROM jobs WHERE idempotency_key=?1",
                [&job.idempotency_key],
                |row| Ok((decode(row)?, row.get::<_, String>("fingerprint")?)),
            )
            .optional()
            .map_err(db_error)?;
        if let Some((existing, fingerprint)) = existing {
            return if fingerprint == job.fingerprint {
                Ok(existing)
            } else {
                Err(AppError::Conflict)
            };
        }
        let count: i64 = tx
            .query_row("SELECT COUNT(*) FROM jobs", [], |r| r.get(0))
            .map_err(db_error)?;
        if count >= self.max_jobs as i64 {
            return Err(AppError::Capacity);
        }
        tx.execute(
            "INSERT INTO jobs (id,idempotency_key,fingerprint,status,width,height,format,source)
            VALUES (?1,?2,?3,'queued',?4,?5,?6,?7)",
            params![
                job.id,
                job.idempotency_key,
                job.fingerprint,
                job.transformation.width,
                job.transformation.height,
                job.transformation.format,
                job.source
            ],
        )
        .map_err(db_error)?;
        let result = tx
            .query_row("SELECT * FROM jobs WHERE id=?1", [&job.id], decode)
            .map_err(db_error)?;
        tx.commit().map_err(db_error)?;
        Ok(result)
    }
    fn list(&self) -> AppResult<Vec<Job>> {
        let connection = self.connection()?;
        let mut statement = connection.prepare("SELECT id,status,width,height,format,error,created_at FROM jobs ORDER BY created_at DESC,rowid DESC LIMIT 100").map_err(db_error)?;
        statement
            .query_map([], decode)
            .map_err(db_error)?
            .collect::<rusqlite::Result<Vec<_>>>()
            .map_err(db_error)
    }
    fn get(&self, id: &str) -> AppResult<Job> {
        self.connection()?
            .query_row(
                "SELECT id,status,width,height,format,error,created_at FROM jobs WHERE id=?1",
                [id],
                decode,
            )
            .optional()
            .map_err(db_error)?
            .ok_or(AppError::NotFound)
    }
    fn result(&self, id: &str) -> AppResult<Vec<u8>> {
        self.connection()?
            .query_row(
                "SELECT result FROM jobs WHERE id=?1 AND status='succeeded'",
                [id],
                |r| r.get(0),
            )
            .optional()
            .map_err(db_error)?
            .ok_or(AppError::NotReady)
    }
    fn claim(&self) -> AppResult<Option<ProcessingJob>> {
        let mut connection = self.connection()?;
        let tx = connection.transaction().map_err(db_error)?;
        let next = tx
            .query_row(
                "SELECT * FROM jobs WHERE status='queued' ORDER BY rowid LIMIT 1",
                [],
                |r| {
                    Ok(ProcessingJob {
                        job: decode(r)?,
                        source: r.get("source")?,
                    })
                },
            )
            .optional()
            .map_err(db_error)?;
        if let Some(ref next) = next {
            tx.execute(
                "UPDATE jobs SET status='running' WHERE id=?1",
                [&next.job.id],
            )
            .map_err(db_error)?;
        }
        tx.commit().map_err(db_error)?;
        Ok(next)
    }
    fn complete(&self, id: &str, result: &[u8]) -> AppResult<()> {
        self.connection()?
            .execute(
                "UPDATE jobs SET status='succeeded',result=?1,source=x'' WHERE id=?2",
                params![result, id],
            )
            .map_err(db_error)?;
        Ok(())
    }
    fn fail(&self, id: &str, reason: &str) -> AppResult<()> {
        self.connection()?
            .execute(
                "UPDATE jobs SET status='failed',error=?1,source=x'' WHERE id=?2",
                params![reason, id],
            )
            .map_err(db_error)?;
        Ok(())
    }
}
