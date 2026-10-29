# Notification Worker Shutdown

Background tasks (emails, notifications, webhooks, PDF generation) run in the `worker` container with Django-Q (`python manage.py qcluster`). This note describes what happens when that container is stopped or replaced, for example during a deploy.

## Grace period

| Setting | Value | Where |
| --- | --- | --- |
| Task `timeout` | 90s (`Q_TASK_TIMEOUT`) | `backend/config/settings.py` |
| Task `retry` | `timeout + 30` = 120s | `backend/config/settings.py` |
| Container `stop_grace_period` | 120s | `docker-compose.yml` |

Rules to keep: `retry > timeout`, and `stop_grace_period > timeout`. If you raise `Q_TASK_TIMEOUT`, raise `stop_grace_period` with it.

## Behaviour on SIGTERM

1. `docker stop` / a container replacement sends SIGTERM to the `qcluster` process (it is PID 1, started without a shell).
2. The cluster stops pulling new tasks and sends a stop signal to each worker after its current task. Workers finish the task they are running.
3. The cluster waits up to `timeout` (90s) for workers to exit. Tasks that need longer than this are terminated.
4. A task that was taken from the broker but not acknowledged (terminated, or the container was killed) is delivered again after `retry` seconds. Tasks still waiting in the broker (Redis, or the ORM fallback) are untouched and picked up by the replacement worker.

Because an interrupted task can run a second time, notification tasks must be safe to repeat (idempotent).

## Long-running tasks

Tasks expected to run longer than `Q_TASK_TIMEOUT` should be split into smaller tasks, or the timeout and grace period raised together. Docker's default grace period is 10s, which is why the explicit `stop_grace_period` is set.

## Checking it locally

```bash
docker compose up -d worker
docker compose stop worker   # should return after in-flight tasks finish, not after 10s
```
