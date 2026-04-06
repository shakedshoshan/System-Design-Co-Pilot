import sys
from pathlib import Path


def main() -> None:
    """Run Kafka consumer; `app` resolves under apps/api, `worker_app` under apps/worker."""
    root = Path(__file__).resolve().parents[1]
    api_dir = root / "apps" / "api"
    worker_dir = root / "apps" / "worker"
    sys.path.insert(0, str(api_dir))
    sys.path.insert(0, str(worker_dir))
    from worker_app.main import main as worker_main

    worker_main()
