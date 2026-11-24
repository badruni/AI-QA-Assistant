"""Filesystem containment helpers for project-scoped application data."""

import os
from pathlib import Path
import re


_PROJECT_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _is_link_or_junction(path):
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def resolve_project_directory(projects_dir, project_id, require_exists=True):
    """Resolve a direct child project directory and reject links/traversal."""
    if not isinstance(project_id, str) or not _PROJECT_ID.fullmatch(project_id):
        raise ValueError("Project ID tidak valid.")

    root = Path(projects_dir).resolve()
    candidate = root / project_id
    if _is_link_or_junction(candidate):
        raise ValueError("Folder proyek tidak boleh berupa symbolic link atau junction.")

    resolved = candidate.resolve()
    if (
        os.path.normcase(str(resolved.parent)) != os.path.normcase(str(root))
        or os.path.normcase(resolved.name) != os.path.normcase(project_id)
    ):
        raise ValueError("Path proyek berada di luar direktori proyek yang diizinkan.")
    if require_exists and not resolved.is_dir():
        raise FileNotFoundError(f"Proyek tidak ditemukan: {project_id}")
    return resolved


def resolve_project_path(project_dir, *parts):
    """Resolve a child path and reject traversal, links, and junctions."""
    lexical_root = Path(project_dir).absolute()
    if _is_link_or_junction(lexical_root):
        raise ValueError("Folder proyek tidak boleh berupa symbolic link atau junction.")
    root = lexical_root.resolve()
    candidate = root

    for part in parts:
        relative = Path(part)
        if relative.is_absolute() or relative.drive:
            raise ValueError("Path proyek harus relatif terhadap folder proyek.")
        if any(piece == ".." for piece in relative.parts):
            raise ValueError("Path proyek tidak boleh keluar dari folder proyek.")
        for piece in relative.parts:
            if piece in ("", "."):
                continue
            candidate = candidate / piece
            if _is_link_or_junction(candidate):
                raise ValueError("Path proyek tidak boleh melewati symbolic link atau junction.")

    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ValueError("Path berada di luar folder proyek yang diizinkan.") from None
    return resolved
