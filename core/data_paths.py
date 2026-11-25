"""Central configuration for external application data.

AI_QA_DATA_DIR is mandatory. Application data must never silently fall
back to the source repository.
"""

import os
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent.parent


def get_data_root():
    """Return a validated external data root or fail closed."""
    configured_root = os.environ.get("AI_QA_DATA_DIR", "").strip()

    if not configured_root:
        raise RuntimeError(
            "AI_QA_DATA_DIR belum dikonfigurasi. "
            "Jalankan aplikasi melalui launcher yang mengatur DataRoot."
        )

    candidate = Path(configured_root).expanduser()

    if not candidate.is_absolute():
        raise ValueError(
            "AI_QA_DATA_DIR harus menggunakan absolute path."
        )

    resolved = candidate.resolve()

    try:
        resolved.relative_to(APP_ROOT.resolve())
    except ValueError:
        return resolved

    raise ValueError(
        "DataRoot tidak boleh berada di dalam direktori repository aplikasi."
    )


DATA_ROOT = get_data_root()
PROJECTS_DIR = DATA_ROOT / "projects"
SYSTEM_LOG_DIR = DATA_ROOT / "logs"