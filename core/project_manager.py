
import json
import re

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from core.path_safety import resolve_project_directory, resolve_project_path
from core.security import has_sensitive_url_query


ROOT = Path(__file__).resolve().parent.parent
from core.data_paths import PROJECTS_DIR
TEMPLATE_FILE = ROOT / "config" / "project_template.json"

PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def validate_project_id(project_id):
    """Memastikan ID aman digunakan sebagai nama folder."""

    if not isinstance(project_id, str):
        raise ValueError("Project ID harus berupa teks.")

    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        raise ValueError(
            "Project ID hanya boleh berisi huruf, angka, "
            "underscore, dan tanda minus. Maksimal 64 karakter."
        )

    return project_id


def validate_url(url, required=True):
    """Memvalidasi URL frontend atau CMS."""

    if not isinstance(url, str):
        raise ValueError("URL harus berupa teks.")

    url = url.strip()

    if not url:
        if required:
            raise ValueError("URL frontend wajib diisi.")
        return ""

    try:
        parsed = urlsplit(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL harus menggunakan HTTP atau HTTPS.")

        if not parsed.hostname:
            raise ValueError("URL harus memiliki nama domain.")

        if parsed.username is not None or parsed.password is not None:
            raise ValueError(
                "URL tidak boleh mengandung username atau password."
            )

        if has_sensitive_url_query(url):
            raise ValueError(
                "URL tidak boleh mengandung parameter query sensitif. "
                "Gunakan URL tanpa token atau kredensial."
            )

        # Memastikan format port valid jika port dicantumkan.
        parsed.port

    except ValueError as error:
        raise ValueError(f"URL tidak valid: {error}") from None

    return url


def list_projects():
    """Mengambil daftar proyek yang sudah terdaftar."""

    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    projects = []

    for folder in PROJECTS_DIR.iterdir():

        try:
            safe_folder = resolve_project_directory(
                PROJECTS_DIR, folder.name, require_exists=True
            )
        except (ValueError, FileNotFoundError, OSError):
            continue

        if not safe_folder.is_dir():
            continue

        config_file = resolve_project_path(safe_folder, "project_config.json")

        if not config_file.is_file():
            continue

        try:
            with config_file.open("r", encoding="utf-8") as file:
                config = json.load(file)

            if config.get("project_id") != folder.name:
                continue

            projects.append({
                "project_id": config["project_id"],
                "project_name": config.get("project_name", ""),
                "base_url": config.get("base_url", ""),
                "cms_url": config.get("cms_url", "")
            })

        except (OSError, json.JSONDecodeError, TypeError):
            continue

    return sorted(
        projects,
        key=lambda item: item["project_id"].lower()
    )


def create_project(project_id, project_name, base_url, cms_url=""):
    """Membuat proyek klien beserta folder standarnya."""

    validate_project_id(project_id)

    if not isinstance(project_name, str) or not project_name.strip():
        raise ValueError("Nama proyek wajib diisi.")

    project_name = project_name.strip()
    base_url = validate_url(base_url)
    cms_url = validate_url(cms_url, required=False)

    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    project_dir = resolve_project_directory(
        PROJECTS_DIR, project_id, require_exists=False
    )

    if project_dir.exists():
        raise FileExistsError(
            f"Folder proyek sudah tersedia: {project_id}"
        )

    if not TEMPLATE_FILE.is_file():
        raise FileNotFoundError(
            "File config/project_template.json tidak ditemukan."
        )

    with TEMPLATE_FILE.open("r", encoding="utf-8-sig") as file:
        config = json.load(file)

    config["project_id"] = project_id
    config["project_name"] = project_name
    config["base_url"] = base_url
    config["cms_url"] = cms_url
    config["created_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    directories = [
        "logs",
        "documentation",
        "reports",
        "evidence/screenshots",
        "evidence/attachments"
    ]

    try:
        project_dir.mkdir()

        for directory in directories:
            (project_dir / directory).mkdir(parents=True)

        config_file = project_dir / "project_config.json"
        temporary_file = project_dir / "project_config.tmp"

        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(config, file, indent=4, ensure_ascii=False)
            file.write("\n")

        temporary_file.replace(config_file)

    except Exception:
        # Membersihkan hanya folder baru yang dibuat proses ini.
        import shutil
        shutil.rmtree(project_dir, ignore_errors=True)
        raise

    return project_dir


def get_project(project_id):
    """Mengambil konfigurasi satu proyek."""

    project_dir = resolve_project_directory(PROJECTS_DIR, project_id)
    config_file = resolve_project_path(project_dir, "project_config.json")

    if not config_file.is_file():
        raise FileNotFoundError(
            f"Proyek tidak ditemukan: {project_id}"
        )

    with config_file.open("r", encoding="utf-8") as file:
        config = json.load(file)

    if config.get("project_id") != project_id:
        raise ValueError("Identitas proyek tidak sesuai dengan folder.")

    return config


def get_project_directory(project_id, require_exists=True):
    """Return the canonical, contained directory for a project ID."""
    return resolve_project_directory(
        PROJECTS_DIR, project_id, require_exists=require_exists
    )


def get_project_path(project_id, *parts):
    """Return a safe path below an existing project's directory."""
    project_dir = get_project_directory(project_id)
    return resolve_project_path(project_dir, *parts)
