"""Central configuration for application data locations."""

import os
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent.parent


def get_data_root():
    """Return the configured data root or the legacy application root."""
    configured_root = os.environ.get("AI_QA_DATA_DIR", "").strip()

    if not configured_root:
        return APP_ROOT

    candidate = Path(configured_root).expanduser()

    if not candidate.is_absolute():
        raise ValueError(
            "AI_QA_DATA_DIR harus menggunakan absolute path."
        )

    return candidate.resolve()


DATA_ROOT = get_data_root()
PROJECTS_DIR = DATA_ROOT / "projects"
SYSTEM_LOG_DIR = DATA_ROOT / "logs"
