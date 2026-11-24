
import json
import os
import queue
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))
INDONESIAN_MONTHS = (
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
)


def _parse_authorization_expiry_input(date_text, time_text):
    """Convert user-friendly DD-MM-YYYY and HH:MM WIB input to ISO 8601."""
    try:
        local_value = datetime.strptime(
            f"{date_text.strip()} {time_text.strip()}",
            "%d-%m-%Y %H:%M",
        ).replace(tzinfo=WIB)
    except (AttributeError, ValueError):
        raise ValueError(
            "Tanggal/waktu tidak valid. Gunakan DD-MM-YYYY dan HH:MM (WIB)."
        ) from None
    if local_value <= datetime.now(WIB):
        raise ValueError("Masa berlaku harus berada di masa depan.")
    return local_value.isoformat()


def _format_authorization_expiry(value):
    """Format stored ISO 8601 expiry as Indonesian date/time in WIB."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return value
        local_value = parsed.astimezone(WIB)
        month = INDONESIAN_MONTHS[local_value.month - 1]
        return (
            f"{local_value.day} {month} {local_value.year}, "
            f"{local_value:%H:%M} WIB"
        )
    except (AttributeError, TypeError, ValueError):
        return str(value)


from core.result_status import ResultStatus
from core.authorization_manager import (
    create_authorization, get_authorization, revoke_authorization,
    validate_authorization,
)
from core.progress_tracking import ProgressReporter
from core.report_manager import save_inspection_report
from core.evidence_manager import verify_evidence
from core.security import sanitize_text, sanitize_url
from core.evidence_viewer import (
    list_project_evidence,
    get_evidence_details,
    resolve_evidence_path,
)

from core.logger import (
    log_info,
    log_warning,
    log_error,
    log_exception
)

from core.project_manager import (
    create_project,
    list_projects,
    get_project
)

from modules.frontend_scanner import (
    load_scanner_config,
    run_frontend_qa_workflow,
)
from modules.website_discovery import discover_website
from modules.generic_uat_inspection import inspect_generic_uat
from modules.authentication_discovery import inspect_authentication
from modules.qa_workflow import run_unified_qa_workflow

from modules.documentation_generator import generate_document_draft
from core.document_viewer import open_document_viewer
from core.docx_renderer import render_approved_docx

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "config" / "project_template.json"


def show_menu(active_project_id=None):
    print("\n================================")
    print("       AI QA ASSISTANT")
    print("================================")
    print("1. Periksa konfigurasi template")
    print("2. Tampilkan struktur proyek")
    print("3. Kelola proyek klien")
    print("4. Jalankan Frontend QA Workflow")
    print("5. Jalankan Generic UAT Inspection")
    print("6. Jalankan Authentication Discovery")
    print("7. Documentation Generator")
    print("8. Evidence Viewer")
    print("9. Keluar")
    print("10. Unified QA Workflow (Frontend + Advanced Inspection)")
    print("11. Kelola Otorisasi QA")

    if active_project_id:
        print(f"\nProyek aktif: {active_project_id}")
    else:
        print("\nProyek aktif: Belum dipilih")


def check_template():
    print("\nMemeriksa konfigurasi...")

    if not TEMPLATE.exists():
        message = "File konfigurasi template tidak ditemukan."
        print("[ERROR]", message)

        log_error(
            activity="Memeriksa konfigurasi template",
            explanation=message,
            causes=[
                "File project_template.json belum dibuat atau lokasinya berubah."
            ],
            actions=[
                "Pastikan folder config tersedia.",
                "Pastikan file config/project_template.json tersedia."
            ]
        )
        return

    try:
        with TEMPLATE.open("r", encoding="utf-8-sig") as file:
            config = json.load(file)

        print("\nKonfigurasi berhasil dibaca.")
        print("Nama project :", config.get("project_name"))
        print("Frontend URL :", sanitize_url(config.get("base_url")))
        print("CMS URL      :", sanitize_url(config.get("cms_url")) if config.get("cms_url") else "(belum diatur)")
        print("Scanner      : belum dijalankan")

        log_info(
            "Memeriksa konfigurasi template",
            "File konfigurasi berhasil dibaca."
        )

    except json.JSONDecodeError as error:
        message = "Format file konfigurasi tidak valid."
        print("\n[ERROR]", message)
        print("Silakan periksa file config/project_template.json.")
        print("Detail error dapat diperiksa di folder logs.")

        log_error(
            activity="Membaca konfigurasi template",
            explanation=message,
            causes=[
                "Ada tanda koma, kutip, atau kurung JSON yang salah.",
                "Isi file mungkin bukan JSON yang valid."
            ],
            actions=[
                "Buka config/project_template.json.",
                "Periksa format JSON.",
                "Jalankan kembali aplikasi setelah diperbaiki."
            ],
            exception=error
        )

    except OSError as error:
        message = "File konfigurasi tidak dapat dibaca."
        print("\n[ERROR]", message)
        print("Detail error dapat diperiksa di folder logs.")

        log_exception(
            "Membaca konfigurasi template",
            error,
            message,
            ["Periksa izin akses dan kondisi file konfigurasi."]
        )


def show_structure():
    print("\nFolder proyek:")

    folders = [
        "core", "modules", "config", "projects",
        "templates", "reports", "backups", "docs"
    ]

    missing = []

    for name in folders:
        path = ROOT / name
        status = "OK" if path.is_dir() else "BELUM ADA"
        print(f"- {name}/ {status}")

        if not path.is_dir():
            missing.append(name)

    if missing:
        log_warning(
            "Memeriksa struktur proyek",
            "Beberapa folder proyek belum tersedia.",
            ["Buat kembali folder yang belum tersedia."]
        )
    else:
        log_info(
            "Memeriksa struktur proyek",
            "Semua folder utama tersedia."
        )


def show_project_list():
    projects = list_projects()

    print("\n================================")
    print("       DAFTAR PROYEK KLIEN")
    print("================================")

    if not projects:
        print("Belum ada proyek klien yang terdaftar.")
        return

    for number, project in enumerate(projects, start=1):
        print(f"\n{number}. {project['project_name']}")
        print("   Project ID :", project["project_id"])
        print("   Frontend   :", sanitize_url(project["base_url"]))
        print("   CMS URL    :", sanitize_url(project["cms_url"]) if project["cms_url"] else "(belum diatur)")


def create_client_project():
    print("\n================================")
    print("       BUAT PROYEK KLIEN")
    print("================================")

    project_id = input("Project ID: ").strip()
    project_name = input("Nama proyek/klien: ").strip()
    base_url = input("Frontend URL: ").strip()
    cms_url = input("CMS URL (boleh kosong): ").strip()

    try:
        project_dir = create_project(
            project_id=project_id,
            project_name=project_name,
            base_url=base_url,
            cms_url=cms_url
        )

        print("\nProyek berhasil dibuat.")
        print("Lokasi:", project_dir)

        log_info(
            "Membuat proyek klien",
            f"Proyek baru berhasil dibuat. Project ID: {project_id}"
        )

    except (ValueError, FileExistsError, FileNotFoundError) as error:
        print("\n[ERROR]", sanitize_text(error))

        log_warning(
            "Membuat proyek klien",
            "Pembuatan proyek tidak dapat dilanjutkan."
        )

    except Exception as error:
        print("\n[ERROR] Terjadi kegagalan saat membuat proyek.")
        print("Detail dapat diperiksa di folder logs.")

        log_exception(
            "Membuat proyek klien",
            error,
            "Pembuatan proyek mengalami kesalahan."
        )


def select_active_project():
    projects = list_projects()

    if not projects:
        print("\nBelum ada proyek untuk dipilih.")
        return None

    show_project_list()

    project_id = input(
        "\nMasukkan Project ID yang ingin diaktifkan: "
    ).strip()

    try:
        project = get_project(project_id)

        print("\nProyek berhasil dipilih.")
        print("Proyek aktif:", project["project_name"])

        log_info(
            "Memilih proyek aktif",
            f"Proyek aktif diubah. Project ID: {project_id}"
        )

        return project_id

    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print("\n[ERROR] Proyek tidak dapat dipilih.")
        print("Detail:", sanitize_text(error))

        log_warning(
            "Memilih proyek aktif",
            "Project ID tidak ditemukan atau konfigurasi proyek tidak valid."
        )

        return None


def show_active_project(active_project_id):
    if not active_project_id:
        print("\nBelum ada proyek aktif.")
        print("Pilih proyek terlebih dahulu.")
        return

    try:
        project = get_project(active_project_id)

        print("\n================================")
        print("       DETAIL PROYEK AKTIF")
        print("================================")
        print("Project ID :", project.get("project_id"))
        print("Nama       :", project.get("project_name"))
        print("Frontend   :", sanitize_url(project.get("base_url")))
        print("CMS URL    :", sanitize_url(project.get("cms_url")) if project.get("cms_url") else "(belum diatur)")
        print("Dibuat     :", project.get("created_at", "(tidak tersedia)"))

    except Exception as error:
        print("\n[ERROR] Detail proyek tidak dapat dibaca.")

        log_exception(
            "Menampilkan detail proyek",
            error,
            "Konfigurasi proyek aktif tidak dapat dibaca."
        )


def _frontend_qa_terminal_status(result, report_error=None):
    if report_error is not None:
        return "failed"
    if result.status == ResultStatus.ACCESS_RESTRICTED:
        return "stopped"
    if result.status in (
        ResultStatus.FAILED,
        ResultStatus.BLOCKED,
        ResultStatus.TIMEOUT,
    ):
        return "failed"
    if not getattr(result, "evidence_ids", ()):
        return "failed"
    return "completed"


def _display_progress_event(event, previous_stage=None):
    if previous_stage is not None and event.stage != previous_stage:
        print()

    count = ""
    if event.current is not None and event.total is not None:
        count = f" | item {event.current}/{event.total}"
    elif event.current is not None:
        count = f" | item {event.current} (total belum diketahui)"
    else:
        count = " | total belum diketahui"

    print(
        f"\r[{event.status.upper()}] {event.stage}{count} | {event.activity}",
        end="",
        flush=True,
    )
    return event.stage


def _project_authorization_allowed(config):
    """Fail closed before standalone scanner menus make network requests."""
    try:
        allowed, reason = validate_authorization(
            config.project_id,
            config.base_url,
            required_scope=["frontend", "read_only"],
        )
    except Exception:
        allowed, reason = False, "authorization_check_failed"
    if not allowed:
        safe_reason = sanitize_text(str(reason or "authorization_invalid"))
        print(
            "\n[BLOCKED] Pemindaian tidak dimulai karena otorisasi tidak valid "
            f"({safe_reason})."
        )
        print("Gunakan menu 11 untuk membuat atau memeriksa otorisasi proyek.")
        log_warning(
            "Authorization Preflight",
            f"Pemindaian diblokir sebelum request: {safe_reason}.",
        )
        return False
    return True


def run_frontend_homepage_scanner(active_project_id):
    print("\n================================")
    print("     FRONTEND QA WORKFLOW")
    print("================================")

    if not active_project_id:
        print("\nBelum ada proyek aktif.")
        print("Silakan pilih proyek yang akan diperiksa.")

        active_project_id = select_active_project()

        if not active_project_id:
            print("\nScanner tidak dijalankan.")
            return None

    try:
        config = load_scanner_config(active_project_id)
        if not _project_authorization_allowed(config):
            return active_project_id

        print("\nMemulai siklus QA frontend...")
        print("Proyek:", config.project_name)
        print("Project ID:", config.project_id)

        progress_events = queue.Queue()
        outcome = {}

        def run_workflow():
            reporter = ProgressReporter(progress_events.put)
            reporter.emit(
                "Frontend QA", "waiting", "Menyiapkan worker scanner."
            )
            try:
                result = run_frontend_qa_workflow(config, progress=reporter)
                outcome["result"] = result

                reporter.emit(
                    "Report Generation", "waiting",
                    "Menunggu hasil inspeksi untuk disimpan.",
                )
                reporter.emit(
                    "Report Generation", "running",
                    "Menyimpan laporan frontend_qa.", 0, 1,
                )
                try:
                    outcome["report_path"] = save_inspection_report(
                        active_project_id, "frontend_qa", result
                    )
                except Exception as report_error:
                    outcome["report_error"] = report_error
                    reporter.emit(
                        "Report Generation", "failed",
                        "Laporan gagal disimpan; hasil inspeksi tetap tersedia.",
                        0, 1,
                    )
                else:
                    reporter.emit(
                        "Report Generation", "completed",
                        "Laporan frontend_qa tersimpan.", 1, 1,
                    )

                report_error = outcome.get("report_error")
                overall = _frontend_qa_terminal_status(result, report_error)
                if result.status == ResultStatus.ACCESS_RESTRICTED:
                    activity = "Workflow berhenti karena akses dibatasi."
                elif overall == "failed":
                    activity = (
                        "Workflow selesai diproses dengan hasil QA "
                        f"{result.status.value}; evidence verified: "
                        f"{len(getattr(result, 'evidence_ids', ())) }/1; "
                        f"report saved: {'no' if report_error else 'yes'}."
                    )
                else:
                    activity = (
                        "Workflow selesai diproses; hasil QA: "
                        f"{result.status.value}; evidence verified: "
                        f"{len(getattr(result, 'evidence_ids', ())) }/1."
                    )
                reporter.emit("Frontend QA", overall, activity)
            except Exception as error:
                outcome["error"] = error
                reporter.emit(
                    "Frontend QA", "failed",
                    "Workflow gagal sebelum seluruh tahap selesai.",
                )
            finally:
                progress_events.put(None)

        progress_events.put(
            ProgressReporter().emit(
                "Frontend QA", "waiting", "Menunggu scanner dimulai."
            )
        )
        worker = threading.Thread(
            target=run_workflow,
            name="frontend-qa-worker",
            daemon=True,
        )
        worker.start()

        last_stage = None
        while True:
            event = progress_events.get()
            if event is None:
                break
            last_stage = _display_progress_event(event, last_stage)
        print()
        worker.join()

        if "error" in outcome:
            raise outcome["error"]
        result = outcome["result"]
        report_path = outcome.get("report_path")
        report_error = outcome.get("report_error")

        if report_path is not None:
            print("Laporan JSON :", report_path)
        if report_error is not None:
            print(
                "[WARNING] Laporan Frontend QA gagal disimpan. "
                "Hasil inspeksi tetap tersedia."
            )
            log_warning(
                "Frontend QA Workflow",
                "Hasil inspeksi tersedia, tetapi laporan JSON gagal disimpan.",
            )

        print("\n================================")
        print("       HASIL PEMERIKSAAN")
        print("================================")
        print("Project ID :", result.project_id)
        print("HTTP Status:", result.homepage.http_status or "(tidak tersedia)")
        print("Page Title :", sanitize_text(result.homepage.page_title) if result.homepage.page_title else "(tidak tersedia)")
        print("Final URL  :", sanitize_url(result.homepage.final_url) if result.homepage.final_url else "(tidak tersedia)")
        print("Status     :", result.status.value)
        print("Homepage   :", result.homepage.status.value, "-", result.homepage.message)
        print("Gambar     :", result.image_status.value if result.image_status else "Skipped",
              f"({len(result.image_results)} item) - {result.image_message}")
        print("Tautan     :", result.link_status.value if result.link_status else "Skipped",
              f"({len(result.link_results)} item) - {result.link_message}")
        if result.stopped_reason:
            print("Penghentian:", result.stopped_reason)

        if result.homepage.screenshot_path:
            print("Screenshot :", result.homepage.screenshot_path)
        else:
            print("Screenshot : Tidak tersedia")

        log_info(
            "Frontend QA Workflow",
            (
                f"Siklus QA frontend selesai. "
                f"Project ID: {active_project_id}, "
                f"Status: {result.status.value}"
            )
        )

    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print("\n[ERROR] Scanner tidak dapat dijalankan.")
        print("Detail:", sanitize_text(error))

        log_warning(
            "Frontend Homepage Scanner",
            "Konfigurasi proyek tidak memenuhi persyaratan scanner."
        )

    except Exception as error:
        print("\n[ERROR] Terjadi kesalahan saat menjalankan scanner.")
        print("Detail error dapat diperiksa di folder logs.")

        log_error(
            activity="Frontend Homepage Scanner",
            explanation="Pemeriksaan homepage mengalami kegagalan.",
            causes=[
                "Browser atau scanner mengalami kendala.",
                "Konfigurasi atau lingkungan aplikasi bermasalah."
            ],
            actions=[
                "Periksa folder logs.",
                "Pastikan instalasi Playwright dan Chromium tersedia."
            ]
        )

    return active_project_id


def run_authentication_discovery(active_project_id):
    print("\n================================")
    print("       AUTHENTICATION DISCOVERY")
    print("================================")

    if not active_project_id:
        print("\nBelum ada proyek aktif.")
        active_project_id = select_active_project()
        if not active_project_id:
            print("\nAuthentication Discovery tidak dijalankan.")
            return None

    try:
        config = load_scanner_config(active_project_id)
        if not _project_authorization_allowed(config):
            return active_project_id
        print("\nTahap 1/2: Website Discovery...")
        discovery = discover_website(config)
        print("Discovery status:", discovery.status.value)
        print("Halaman ditemukan:", len(discovery.pages))

        if discovery.status == ResultStatus.ACCESS_RESTRICTED:
            print("\nAuthentication Discovery dihentikan karena akses dibatasi.")
            log_warning(
                "Authentication Discovery",
                "Tahap dilewati karena Website Discovery berstatus Access Restricted."
            )
            return active_project_id

        print("\nTahap 2/2: Deteksi indikasi autentikasi (read-only)...")
        result = inspect_authentication(config, discovery)
        try:
            report_path = save_inspection_report(
                active_project_id, "authentication_discovery", result
            )
            print("Laporan JSON :", report_path)
        except Exception as report_error:
            print("[WARNING] Laporan Authentication Discovery gagal disimpan. Hasil inspeksi tetap tersedia.")
            log_warning(
                "Authentication Discovery",
                "Hasil inspeksi tersedia, tetapi laporan JSON gagal disimpan."
            )
        print("\n================================")
        print("       HASIL AUTHENTICATION DISCOVERY")
        print("================================")
        print("Project ID    :", result.project_id)
        print("Status        :", result.status.value)
        print("Klasifikasi   :", result.classification)
        print("Confidence    :", result.confidence)
        print("Halaman       :", len(result.pages))
        print("Selesai       :", result.completed)
        print("Pesan         :", result.message)

        for item in result.pages:
            print("\n- URL:", sanitize_url(item.page_url))
            print("  HTTP:", item.http_status or "(tidak tersedia)")
            print("  Status:", item.status.value)
            if item.signals:
                print("  Indikasi:", item.signals)
            print("  Catatan:", item.message)

        log_info(
            "Authentication Discovery",
            (
                f"Project ID: {active_project_id}, "
                f"Classification: {result.classification}, "
                f"Status: {result.status.value}, Pages: {len(result.pages)}"
            )
        )
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print("\n[ERROR] Authentication Discovery tidak dapat dijalankan.")
        print("Detail:", sanitize_text(error))
        log_warning(
            "Authentication Discovery",
            "Konfigurasi proyek tidak memenuhi persyaratan."
        )
    except Exception as error:
        print("\n[ERROR] Terjadi kendala saat Authentication Discovery.")
        print("Detail error dapat diperiksa di folder logs.")
        log_exception(
            "Authentication Discovery",
            error,
            "Pemeriksaan indikasi autentikasi mengalami kendala."
        )

    return active_project_id
def run_generic_uat_inspection(active_project_id):
    print("\n================================")
    print("       GENERIC UAT INSPECTION")
    print("================================")

    if not active_project_id:
        print("\nBelum ada proyek aktif.")
        print("Silakan pilih proyek yang akan diperiksa.")
        active_project_id = select_active_project()
        if not active_project_id:
            print("\nGeneric UAT tidak dijalankan.")
            return None

    try:
        config = load_scanner_config(active_project_id)
        if not _project_authorization_allowed(config):
            return active_project_id

        print("\nTahap 1/2: Website Discovery...")
        discovery = discover_website(config)
        print("Discovery status:", discovery.status.value)
        print("Halaman ditemukan:", len(discovery.pages))

        if discovery.status == ResultStatus.ACCESS_RESTRICTED:
            print("\nGeneric UAT dihentikan karena Website Discovery mendeteksi pembatasan akses.")
            log_warning(
                "Generic UAT Inspection",
                "Tahap dilewati karena Website Discovery berstatus Access Restricted."
            )
            return active_project_id

        if not discovery.pages:
            print("Tidak ada halaman yang dapat diproses.")
            return active_project_id

        print("\nTahap 2/2: Generic UAT DOM Inspection...")
        result = inspect_generic_uat(config, discovery)
        try:
            report_path = save_inspection_report(
                active_project_id, "generic_uat", result
            )
            print("Laporan JSON :", report_path)
        except Exception as report_error:
            print("[WARNING] Laporan Generic UAT gagal disimpan. Hasil inspeksi tetap tersedia.")
            log_warning(
                "Generic UAT Inspection",
                "Hasil inspeksi tersedia, tetapi laporan JSON gagal disimpan."
            )

        print("\n================================")
        print("       HASIL GENERIC UAT")
        print("================================")
        print("Project ID :", result.project_id)
        print("Status     :", result.status.value)
        print("Halaman    :", len(result.pages))
        print("Temuan     :", len(result.findings))
        print("Selesai    :", result.completed)
        print("Pesan      :", result.message)

        for page_result in result.pages:
            print("\n- URL:", sanitize_url(page_result.page_url))
            print("  HTTP:", page_result.http_status or "(tidak tersedia)")
            print("  Status:", page_result.status.value)
            print("  Komponen:", page_result.component_summary)
            if page_result.screenshot_path:
                print("  Evidence:", page_result.screenshot_path)

        if result.findings:
            print("\nINDIKASI UNTUK DITINJAU")
            for number, finding in enumerate(result.findings, start=1):
                print(f"{number}. [{finding.category}] {sanitize_text(finding.element)}")
                print("   URL   :", sanitize_url(finding.page_url))
                print("   Detail:", sanitize_text(finding.issue))
                print("   Status:", finding.status.value)

        log_info(
            "Generic UAT Inspection",
            (
                f"Inspeksi selesai. Project ID: {active_project_id}, "
                f"Status: {result.status.value}, "
                f"Halaman: {len(result.pages)}, "
                f"Temuan: {len(result.findings)}"
            )
        )

    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print("\n[ERROR] Generic UAT tidak dapat dijalankan.")
        print("Detail:", sanitize_text(error))
        log_warning(
            "Generic UAT Inspection",
            "Konfigurasi proyek tidak memenuhi persyaratan inspeksi."
        )
    except Exception as error:
        print("\n[ERROR] Terjadi kesalahan saat Generic UAT.")
        print("Detail error dapat diperiksa di folder logs.")
        log_error(
            activity="Generic UAT Inspection",
            explanation="Inspeksi DOM mengalami kegagalan.",
            causes=[
                "Browser atau scanner mengalami kendala.",
                "Konfigurasi atau lingkungan aplikasi bermasalah."
            ],
            actions=[
                "Periksa folder logs.",
                "Pastikan instalasi Playwright dan Chromium tersedia."
            ]
        )

    return active_project_id


def manage_project_authorization(active_project_id):
    """View, create, or revoke this project's explicit QA authorization."""
    if not active_project_id:
        active_project_id = select_active_project()
        if not active_project_id:
            print("\nPengelolaan otorisasi dibatalkan: belum ada proyek aktif.")
            return None

    config = load_scanner_config(active_project_id)
    while True:
        print("\n================================")
        print("       OTORISASI QA PROJECT")
        print("================================")
        print("Project ID :", active_project_id)
        print("Target     :", sanitize_url(config.base_url))
        print("1. Lihat status otorisasi")
        print("2. Buat / perbarui otorisasi")
        print("3. Cabut otorisasi aktif")
        print("0. Kembali")

        choice = input("\nPilih menu: ").strip()
        try:
            if choice == "0":
                break
            if choice == "1":
                record = get_authorization(active_project_id)
                if record is None:
                    print("[INFO] Belum ada otorisasi untuk proyek ini.")
                else:
                    print("Status       :", record.get("status", "unknown"))
                    print("Target       :", sanitize_url(record.get("target_url")))
                    print("Diberikan oleh:", sanitize_text(record.get("authorized_by", "")))
                    print("Scope        :", ", ".join(record.get("scope", [])))
                    print("Berlaku sampai:", _format_authorization_expiry(record.get("expires_at", "")))
                    print(
                        "Konfirmasi admin:",
                        "Ya" if record.get("admin_access_confirmed") else "Tidak",
                    )
            elif choice == "2":
                print("\nOtorisasi hanya boleh dibuat jika Anda memiliki izin eksplisit.")
                print("Target diambil dari konfigurasi proyek dan tidak dapat diganti di sini.")
                confirmation = input(
                    "Ketik YA untuk mengonfirmasi izin pengujian pada target ini: "
                ).strip()
                if confirmation != "YA":
                    print("[INFO] Pembuatan otorisasi dibatalkan.")
                    continue
                authorized_by = input("Nama pemberi otorisasi: ").strip()
                while True:
                    expiry_date = input(
                        "Tanggal kedaluwarsa (DD-MM-YYYY): "
                    ).strip()
                    expiry_time = input(
                        "Waktu kedaluwarsa (24 jam, WIB, HH:MM): "
                    ).strip()
                    try:
                        expires_at = _parse_authorization_expiry_input(
                            expiry_date, expiry_time
                        )
                        break
                    except ValueError as error:
                        print("[ERROR]", sanitize_text(error))
                        print("Silakan masukkan tanggal dan waktu kembali.")
                admin_answer = input(
                    "Apakah administrator sudah mengonfirmasi akses resmi/"
                    "allowlisting bila diperlukan? (y/N): "
                ).strip().lower()
                if admin_answer not in ("", "y", "n"):
                    print("[ERROR] Jawaban admin harus y atau n.")
                    continue
                record = create_authorization(
                    active_project_id,
                    config.base_url,
                    authorized_by,
                    ["frontend", "read_only"],
                    expires_at,
                    admin_access_confirmed=(admin_answer == "y"),
                )
                print("[SUCCESS] Otorisasi tersimpan untuk proyek ini.")
                print("Authorization ID:", record["authorization_id"])
                print("Berlaku sampai   :", _format_authorization_expiry(record["expires_at"]))
            elif choice == "3":
                current = get_authorization(active_project_id)
                if current is None or current.get("status") != "active":
                    print("[INFO] Tidak ada otorisasi aktif untuk dicabut.")
                    continue
                print("Target:", sanitize_url(current.get("target_url")))
                confirmation = input(
                    "Ketik YA untuk mencabut otorisasi aktif: "
                ).strip()
                if confirmation != "YA":
                    print("[INFO] Pencabutan dibatalkan.")
                    continue
                revoked_by = input("Nama pencabut otorisasi: ").strip()
                reason = input("Alasan pencabutan (boleh kosong): ").strip()
                revoke_authorization(active_project_id, revoked_by, reason)
                print("[SUCCESS] Otorisasi aktif telah dicabut.")
            else:
                print("Pilihan tidak valid.")
        except (ValueError, OSError) as error:
            print("[ERROR] Pengelolaan otorisasi gagal:", sanitize_text(error))
    return active_project_id


def run_unified_qa_inspection(active_project_id):
    """Run and save the complete project-scoped QA workflow."""
    print("\n================================")
    print("       UNIFIED QA WORKFLOW")
    print("================================")
    if not active_project_id:
        print("\nBelum ada proyek aktif.")
        active_project_id = select_active_project()
        if not active_project_id:
            print("\nUnified QA Workflow tidak dijalankan.")
            return None

    try:
        config = load_scanner_config(active_project_id)
        progress_events = queue.Queue()
        observed_events = []
        outcome = {}

        def publish(event):
            observed_events.append(event)
            progress_events.put(event)

        def run_workflow():
            reporter = ProgressReporter(publish)
            reporter.emit(
                "Unified QA Workflow", "waiting",
                "Menunggu Unified QA Workflow dimulai.",
            )
            reporter.emit(
                "Unified QA Workflow", "running",
                "Menjalankan seluruh tahap inspeksi proyek.",
            )
            try:
                result = run_unified_qa_workflow(config, progress=reporter)
                outcome["result"] = result
                reporter.emit(
                    "Report Generation", "waiting",
                    "Menunggu hasil Unified QA untuk disimpan.",
                )
                reporter.emit(
                    "Report Generation", "running",
                    "Menyimpan laporan unified_qa.", 0, 1,
                )
                try:
                    outcome["report_path"] = save_inspection_report(
                        active_project_id, "unified_qa", result
                    )
                except Exception as report_error:
                    outcome["report_error"] = report_error
                    reporter.emit(
                        "Report Generation", "failed",
                        "Laporan Unified QA gagal disimpan.", 0, 1,
                    )
                else:
                    reporter.emit(
                        "Report Generation", "completed",
                        "Laporan unified_qa tersimpan.", 1, 1,
                    )

                evidence_failed = any(
                    event.stage == "Unified Evidence Collection"
                    and event.status == "failed"
                    for event in observed_events
                )
                result_status = getattr(result.status, "value", result.status)
                if outcome.get("report_error") is not None or evidence_failed:
                    terminal = "failed"
                elif result_status == ResultStatus.ACCESS_RESTRICTED.value:
                    terminal = "stopped"
                elif result_status in (
                    ResultStatus.FAILED.value,
                    ResultStatus.BLOCKED.value,
                    ResultStatus.TIMEOUT.value,
                ):
                    terminal = "failed"
                else:
                    terminal = "completed"
                reporter.emit(
                    "Unified QA Workflow", terminal,
                    "Workflow selesai diproses; hasil QA: "
                    f"{result_status}; report saved: "
                    f"{'no' if outcome.get('report_error') else 'yes'}; "
                    f"evidence verified: {len(result.evidence_ids)}.",
                )
            except Exception as error:
                outcome["error"] = error
                reporter.emit(
                    "Unified QA Workflow", "failed",
                    "Unified QA gagal sebelum seluruh tahap selesai.",
                )
            finally:
                progress_events.put(None)

        progress_events.put(ProgressReporter().emit(
            "Unified QA Workflow", "waiting", "Menunggu worker Unified QA."
        ))
        worker = threading.Thread(
            target=run_workflow,
            name="unified-qa-worker",
            daemon=True,
        )
        worker.start()
        last_stage = None
        while True:
            event = progress_events.get()
            if event is None:
                break
            last_stage = _display_progress_event(event, last_stage)
        print()
        worker.join()
        if "error" in outcome:
            raise outcome["error"]

        result = outcome["result"]
        report_path = outcome.get("report_path")
        report_error = outcome.get("report_error")
        if report_path is not None:
            print("Laporan QA  :", report_path)
        if report_error is not None:
            print(
                "[WARNING] Laporan Unified QA gagal disimpan. "
                "Hasil inspeksi tetap tersedia."
            )
            log_warning(
                "Unified QA Workflow",
                "Hasil tersedia, tetapi laporan QA gagal disimpan.",
            )

        print("Project ID  :", result.project_id)
        print("Status      :", result.status.value)
        for stage in result.stages:
            label = stage.status.value if stage.status else "Skipped"
            print(f"{stage.name:26}: {label} — {stage.message}")
        print("Evidence IDs:", ", ".join(result.evidence_ids) or "Tidak ada")
        log_info(
            "Unified QA Workflow",
            f"Project ID: {result.project_id}, Status: {result.status.value}",
        )
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print("\n[ERROR] Unified QA tidak dapat dijalankan.")
        print("Detail:", sanitize_text(error))
        log_warning(
            "Unified QA Workflow",
            "Konfigurasi proyek tidak memenuhi persyaratan inspeksi.",
        )
    except Exception as error:
        print("\n[ERROR] Terjadi kendala saat Unified QA Workflow.")
        print("Detail error dapat diperiksa di folder logs.")
        log_exception(
            "Unified QA Workflow", error,
            "Siklus QA mengalami kendala yang tidak tertangani.",
        )
    return active_project_id

def project_manager_menu(active_project_id):
    while True:
        print("\n================================")
        print("          PROJECT MANAGER")
        print("================================")
        print("1. Buat proyek klien baru")
        print("2. Lihat daftar proyek")
        print("3. Pilih proyek aktif")
        print("4. Lihat detail proyek aktif")
        print("5. Kembali ke menu utama")

        choice = input("\nPilih menu: ").strip()

        try:
            if choice == "1":
                create_client_project()

            elif choice == "2":
                show_project_list()

            elif choice == "3":
                selected_project = select_active_project()

                if selected_project:
                    active_project_id = selected_project

            elif choice == "4":
                show_active_project(active_project_id)

            elif choice == "5":
                return active_project_id

            else:
                print("Pilihan tidak valid.")
                log_warning(
                    "Project Manager",
                    "Pengguna memilih menu yang tidak tersedia."
                )

        except Exception as error:
            print("\n[ERROR] Terjadi kesalahan pada Project Manager.")
            print("Detail dapat diperiksa di folder logs.")

            log_exception(
                "Menjalankan Project Manager",
                error,
                "Project Manager mengalami kesalahan yang tidak tertangani."
            )


def open_screenshot_file(screenshot_path):
    """Open a screenshot with the Windows default app, falling back to Explorer."""
    start_file = getattr(os, "startfile", None)
    if start_file is None:
        raise OSError("Membuka file otomatis hanya didukung pada Windows.")
    try:
        start_file(str(screenshot_path))
    except OSError as exc:
        # Windows modern can have a working AppX default association even when
        # os.startfile raises WinError 1155. Explorer honors that association.
        if getattr(exc, "winerror", None) != 1155:
            raise
        subprocess.Popen(["explorer.exe", str(screenshot_path)])


def run_evidence_viewer(active_project_id):
    """Interactive, read-only evidence viewer for the active project."""
    print("\n================================")
    print("          EVIDENCE VIEWER")
    print("================================")

    if not active_project_id:
        print("\nBelum ada proyek aktif.")
        print("Silakan pilih proyek yang evidence-nya ingin dilihat.")
        active_project_id = select_active_project()
        if not active_project_id:
            print("\nEvidence Viewer tidak dijalankan.")
            return None

    while True:
        print("\n--- EVIDENCE VIEWER ---")
        print("Project ID:", active_project_id)
        print("1. Daftar evidence")
        print("2. Detail evidence")
        print("3. Buka screenshot")
        print("4. Verifikasi integritas evidence")
        print("5. Kembali ke menu utama")
        choice = input("\nPilih menu: ").strip()

        if choice == "1":
            records = list_project_evidence(active_project_id)
            if not records:
                print("\nBelum ada evidence terdaftar untuk proyek ini.")
                continue
            print("\nDAFTAR EVIDENCE")
            for index, record in enumerate(records, start=1):
                print(
                    f"{index}. [{record.get('evidence_type', '-')}] "
                    f"{record.get('title') or '(tanpa judul)'}"
                )
                print("   ID     :", record.get("evidence_id", "-"))
                print("   Source :", record.get("source", "-"))
                print("   File   :", record.get("file_path", "-"))

        elif choice == "2":
            evidence_id = input("Evidence ID: ").strip()
            record = get_evidence_details(active_project_id, evidence_id)
            print("\nDETAIL EVIDENCE")
            for field in (
                "evidence_id", "project_id", "evidence_type", "source",
                "title", "page_url", "file_path", "file_size", "sha256",
                "created_at", "related_finding_ids", "metadata",
            ):
                print(f"{field:20}: {record.get(field)}")

        elif choice == "3":
            evidence_id = input("Evidence ID screenshot: ").strip()
            record = get_evidence_details(active_project_id, evidence_id)
            if record.get("evidence_type") != "screenshot":
                print("Evidence yang dipilih bukan screenshot.")
                continue
            screenshot_path = resolve_evidence_path(active_project_id, evidence_id)
            try:
                open_screenshot_file(screenshot_path)
            except OSError as exc:
                print(f"Gagal membuka screenshot: {exc}")
                continue
            print("Permintaan membuka screenshot dikirim ke Windows:", screenshot_path)

        elif choice == "4":
            evidence_id = input("Evidence ID yang diverifikasi: ").strip()
            if verify_evidence(active_project_id, evidence_id):
                print("Hasil verifikasi: VALID (SHA-256 cocok).")
            else:
                print("Hasil verifikasi: TIDAK VALID (file hilang atau hash berbeda).")

        elif choice == "5":
            break
        else:
            print("Pilihan tidak valid.")

    return active_project_id


def run_documentation_generator(active_project_id):
    """Create/review/preview/export project documentation drafts."""
    from modules.documentation_generator import generate_document_draft, list_project_document_drafts
    from core.document_viewer import open_document_viewer
    from core.docx_renderer import render_approved_docx
    from core.document_manager import approve_document, get_document

    if not active_project_id:
        print("\nBelum ada proyek aktif.")
        active_project_id = select_active_project()
        if not active_project_id:
            print("Documentation Generator tidak dijalankan.")
            return None

    while True:
        print("\n--- DOCUMENTATION GENERATOR ---")
        print("Project ID:", active_project_id)
        print("1. Buat draft UAT")
        print("2. Buat draft User Guide Web")
        print("3. Buat draft User Guide CMS")
        print("4. Daftar dan review dokumen")
        print("5. Kembali")
        choice = input("Pilih menu: ").strip()
        if choice == "5":
            break
        if choice in ("1", "2", "3"):
            doc_type = {"1": "UAT", "2": "User_Guide_Web", "3": "User_Guide_CMS"}[choice]
            try:
                record = generate_document_draft(active_project_id, doc_type)
                manifest, version = record["manifest"], record["version"]
                doc_id = manifest["document_id"]
                print("\nDraft dibuat:", doc_id)
                print("Status:", version["status"])
                print("Bagian perlu ditinjau:", len(version.get("unverified_sections", [])))
                if version.get("unverified_sections"):
                    for item in version["unverified_sections"]:
                        print("-", item)
                if input("Buka A4 Print Preview? (y/n): ").strip().lower() == "y":
                    open_document_viewer(active_project_id, doc_id)
                print("DOCX final belum dibuat. Persetujuan hanya tersedia setelah seluruh bagian diverifikasi.")
            except Exception as error:
                print("\n[INFO] Draft tidak dapat dibuat:", sanitize_text(error))
        elif choice == "4":
            docs = list_project_document_drafts(active_project_id)
            if not docs:
                print("Belum ada dokumen.")
                continue
            for index, item in enumerate(docs, 1):
                print(f"{index}. [{item['status']}] {item['document_type']} - {item['title']}")
                print("   ID:", item["document_id"], "| Versi:", item["current_version"])
            selected = input("Masukkan nomor dokumen (kosong untuk kembali): ").strip()
            if not selected:
                continue
            try:
                number = int(selected)
                item = docs[number - 1]
                doc_id = item["document_id"]
                action = input("Aksi: [1] Preview [2] Approve [3] Export DOCX [Enter] kembali: ").strip()
                if action == "1":
                    open_document_viewer(active_project_id, doc_id)
                elif action == "2":
                    current = get_document(active_project_id, doc_id)["version"]
                    if current.get("unverified_sections"):
                        print("Persetujuan ditolak: masih ada bagian yang belum diverifikasi.")
                    elif input("Konfirmasi: Anda telah memeriksa isi dan evidence? (y/n): ").strip().lower() == "y":
                        approved = approve_document(active_project_id, doc_id)
                        print("Versi disetujui:", approved["version"].get("status"))
                elif action == "3":
                    output = render_approved_docx(active_project_id, doc_id)
                    print("DOCX dibuat:", output)
            except (ValueError, IndexError, OSError, RuntimeError) as error:
                print("[INFO] Aksi dokumen tidak dapat diselesaikan:", sanitize_text(error))
        else:
            print("Pilihan tidak valid.")
    return active_project_id

def main():
    active_project_id = None

    log_info(
        "Menjalankan aplikasi",
        "AI QA Assistant berhasil dimulai."
    )

    while True:
        show_menu(active_project_id)
        choice = input("\nPilih menu: ").strip()

        try:
            if choice == "1":
                check_template()

            elif choice == "2":
                show_structure()

            elif choice == "3":
                active_project_id = project_manager_menu(
                    active_project_id
                )

            elif choice == "4":
                active_project_id = run_frontend_homepage_scanner(
                    active_project_id
                )
            
            elif choice == "5":
                active_project_id = run_generic_uat_inspection(
                    active_project_id
                )

            elif choice == "6":
                active_project_id = run_authentication_discovery(active_project_id)

            elif choice == "7":
                active_project_id = run_documentation_generator(active_project_id)

            elif choice == "8":
                active_project_id = run_evidence_viewer(active_project_id)

            elif choice == "9":
                log_info(
                    "Menutup aplikasi",
                    "Pengguna menutup AI QA Assistant secara normal."
                )
                print("AI QA Assistant ditutup.")
                break

            elif choice == "10":
                active_project_id = run_unified_qa_inspection(active_project_id)

            elif choice == "11":
                active_project_id = manage_project_authorization(active_project_id)

            else:
                print("Pilihan tidak valid.")
                log_warning(
                    "Memilih menu",
                    "Pengguna memasukkan pilihan menu yang tidak tersedia."
                )

        except Exception as error:
            print("\n[ERROR] Terjadi kesalahan pada aplikasi.")
            print("Silakan periksa folder logs.")

            log_exception(
                "Menjalankan menu aplikasi",
                error,
                "Aplikasi mengalami kesalahan yang tidak tertangani.",
                [
                    "Jangan menghapus file log.",
                    "Periksa log untuk petunjuk penanganan."
                ]
            )


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        log_warning(
            "Menghentikan aplikasi",
            "Aplikasi dihentikan menggunakan keyboard (Ctrl+C)."
        )
        print("\nAplikasi dihentikan.")

    except Exception as error:
        print("\n[ERROR] Aplikasi mengalami kesalahan fatal.")
        print("Silakan periksa folder logs.")

        log_exception(
            "Kesalahan fatal aplikasi",
            error,
            "Aplikasi berhenti akibat kesalahan yang tidak tertangani."
        )
