"""Read-only helpers for browsing project evidence."""
from pathlib import Path

from core.evidence_manager import list_evidence
from core.project_manager import PROJECTS_DIR, get_project_directory
from core.path_safety import resolve_project_path


def list_project_evidence(project_id):
    """Return registered evidence for one validated project."""
    return tuple(list_evidence(project_id))


def get_evidence_details(project_id, evidence_id):
    """Return one evidence record or raise KeyError."""
    for record in list_project_evidence(project_id):
        if record.get("evidence_id") == evidence_id:
            return record
    raise KeyError("Evidence ID tidak ditemukan.")


def resolve_evidence_path(project_id, evidence_id):
    """Resolve an indexed file path and enforce project evidence containment."""
    record = get_evidence_details(project_id, evidence_id)
    evidence_dir = (PROJECTS_DIR / project_id / "evidence").resolve()
    candidate_input = evidence_dir / Path(record.get("file_path", ""))
    if candidate_input.is_symlink():
        raise ValueError("Symlink tidak diizinkan sebagai evidence.")
    candidate = candidate_input.resolve()
    try:
        candidate.relative_to(evidence_dir)
    except ValueError:
        raise ValueError("Path evidence berada di luar folder proyek.") from None
    if not candidate.is_file():
        raise FileNotFoundError("File evidence tidak ditemukan.")
    return candidate
