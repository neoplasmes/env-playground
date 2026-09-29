use image_api::{
    app::{AppError, ports::JobRepo, use_cases::create_job::CreateJob},
    core::entities::Transformation,
    env::SqliteJobRepo,
};
use std::sync::Arc;

fn settings() -> Transformation {
    Transformation {
        width: 100,
        height: 100,
        format: "png".into(),
    }
}

#[test]
fn idempotency_recovery_and_output() {
    let temp = tempfile::tempdir().unwrap();
    let path = temp.path().join("jobs.sqlite");
    let repo = Arc::new(SqliteJobRepo::open(&path, 2).unwrap());
    let create = CreateJob(repo.clone());
    let job = create
        .execute("same-key".into(), settings(), vec![1, 2])
        .unwrap();
    assert_eq!(
        create
            .execute("same-key".into(), settings(), vec![1, 2])
            .unwrap()
            .id,
        job.id
    );
    assert!(matches!(
        create.execute("same-key".into(), settings(), vec![3]),
        Err(AppError::Conflict)
    ));
    assert_eq!(repo.claim().unwrap().unwrap().job.id, job.id);
    assert!(repo.claim().unwrap().is_none());
    drop(create);
    drop(repo);
    let repo = SqliteJobRepo::open(&path, 2).unwrap();
    assert_eq!(repo.claim().unwrap().unwrap().source, vec![1, 2]);
    repo.complete(&job.id, &[8, 9]).unwrap();
    assert_eq!(repo.get(&job.id).unwrap().status, "succeeded");
    assert_eq!(repo.result(&job.id).unwrap(), vec![8, 9]);
}

#[test]
fn rejects_invalid_settings_and_capacity() {
    let temp = tempfile::tempdir().unwrap();
    let repo = Arc::new(SqliteJobRepo::open(&temp.path().join("jobs.sqlite"), 1).unwrap());
    let create = CreateJob(repo);
    let mut invalid = settings();
    invalid.width = 0;
    assert!(matches!(
        create.execute("key".into(), invalid, vec![1]),
        Err(AppError::Invalid(_))
    ));
    create.execute("key".into(), settings(), vec![1]).unwrap();
    assert!(matches!(
        create.execute("other".into(), settings(), vec![1]),
        Err(AppError::Capacity)
    ));
}
