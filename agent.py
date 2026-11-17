
import json
from pathlib import Path

from core.result_status import ResultStatus

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
    inspect_homepage
)
from modules.website_discovery import discover_website
from modules.generic_uat_inspection import inspect_generic_uat
from modules.authentication_discovery import inspect_authentication

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "config" / "project_template.json"


def show_menu(active_project_id=None):
    print("\n================================")
    print("       AI QA ASSISTANT")
    print("================================")
    print("1. Periksa konfigurasi template")
    print("2. Tampilkan struktur proyek")
    print("3. Kelola proyek klien")
    print("4. Jalankan Frontend Homepage Scanner")
    print("5. Jalankan Generic UAT Inspection")
    print("6. Jalankan Authentication Discovery")
    print("7. Keluar")

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
        print("Frontend URL :", config.get("base_url"))
        print("CMS URL      :", config.get("cms_url") or "(belum diatur)")
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
        print("   Frontend   :", project["base_url"])
        print("   CMS URL    :", project["cms_url"] or "(belum diatur)")


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
        print("\n[ERROR]", error)

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
        print("Detail:", error)

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
        print("Frontend   :", project.get("base_url"))
        print("CMS URL    :", project.get("cms_url") or "(belum diatur)")
        print("Dibuat     :", project.get("created_at", "(tidak tersedia)"))

    except Exception as error:
        print("\n[ERROR] Detail proyek tidak dapat dibaca.")

        log_exception(
            "Menampilkan detail proyek",
            error,
            "Konfigurasi proyek aktif tidak dapat dibaca."
        )


def run_frontend_homepage_scanner(active_project_id):
    print("\n================================")
    print("     FRONTEND HOMEPAGE SCANNER")
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

        print("\nMemulai pemeriksaan homepage...")
        print("Proyek:", config.project_name)
        print("Project ID:", config.project_id)

        result = inspect_homepage(config)

        print("\n================================")
        print("       HASIL PEMERIKSAAN")
        print("================================")
        print("Project ID :", result.project_id)
        print("HTTP Status:", result.http_status or "(tidak tersedia)")
        print("Page Title :", result.page_title or "(tidak tersedia)")
        print("Final URL  :", result.final_url or "(tidak tersedia)")
        print("Status     :", result.status.value)
        print("Pesan      :", result.message)

        if result.screenshot_path:
            print("Screenshot :", result.screenshot_path)
        else:
            print("Screenshot : Tidak tersedia")

        log_info(
            "Frontend Homepage Scanner",
            (
                f"Pemeriksaan selesai. "
                f"Project ID: {active_project_id}, "
                f"Status: {result.status.value}"
            )
        )

    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print("\n[ERROR] Scanner tidak dapat dijalankan.")
        print("Detail:", error)

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
            print("\n- URL:", item.page_url)
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
        print("Detail:", error)
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
            print("\n- URL:", page_result.page_url)
            print("  HTTP:", page_result.http_status or "(tidak tersedia)")
            print("  Status:", page_result.status.value)
            print("  Komponen:", page_result.component_summary)
            if page_result.screenshot_path:
                print("  Evidence:", page_result.screenshot_path)

        if result.findings:
            print("\nINDIKASI UNTUK DITINJAU")
            for number, finding in enumerate(result.findings, start=1):
                print(f"{number}. [{finding.category}] {finding.element}")
                print("   URL   :", finding.page_url)
                print("   Detail:", finding.issue)
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
        print("Detail:", error)
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
                log_info(
                    "Menutup aplikasi",
                    "Pengguna menutup AI QA Assistant secara normal."
                )
                print("AI QA Assistant ditutup.")
                break
                
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
