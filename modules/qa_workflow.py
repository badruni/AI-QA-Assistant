"""Coordinated read-only QA workflow across frontend and advanced stages."""

from dataclasses import dataclass
from pathlib import Path

from core.evidence_manager import list_evidence, verify_evidence
from core.authorization_manager import validate_authorization
from core.request_safety import RequestSafetyController
from core.progress_tracking import emit_progress, terminal_status_for_results
from core.result_status import ResultStatus
from modules.authentication_discovery import (
    AuthenticationDiscoveryResult,
    inspect_authentication,
)
from modules.frontend_scanner import (
    FrontendQAWorkflowResult,
    ScannerConfig,
    run_frontend_qa_workflow,
)
from modules.generic_uat_inspection import GenericUATResult, inspect_generic_uat
from modules.website_discovery import WebsiteDiscoveryResult, discover_website


@dataclass(frozen=True)
class WorkflowStage:
    name: str
    status: ResultStatus | None
    message: str


@dataclass(frozen=True)
class UnifiedQAWorkflowResult:
    project_id: str
    status: ResultStatus
    frontend: FrontendQAWorkflowResult | None
    website_discovery: WebsiteDiscoveryResult | None
    generic_uat: GenericUATResult | None
    authentication_discovery: AuthenticationDiscoveryResult | None
    stages: tuple[WorkflowStage, ...]
    evidence_ids: tuple[str, ...]
    evidence_status: str = "not_required"
    expected_evidence: int = 0
    verified_evidence: int = 0
    permission_check_status: str = "authorized"
    permission_check_message: str = "Otorisasi valid untuk target dan scope workflow."


def run_unified_qa_workflow(config, timeout_ms=30000, progress=None):
    """Run all read-only inspections with one project and safety controller."""
    if not isinstance(config, ScannerConfig):
        raise TypeError("Konfigurasi scanner tidak valid.")
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int):
        raise ValueError("timeout_ms harus berupa bilangan bulat.")
    if timeout_ms < 1000:
        raise ValueError("timeout_ms minimal 1000 milidetik.")

    emit_progress(progress, "Unified Inspection", "waiting", "Menunggu tahapan Unified QA.")
    emit_progress(progress, "Unified Inspection", "running", "Memeriksa otorisasi sebelum request website.")

    try:
        authorized, authorization_reason = validate_authorization(
            config.project_id,
            config.base_url,
            required_scope=["frontend", "read_only"],
        )
    except Exception:
        # Fail closed: an unreadable or invalid authorization record must never
        # permit a network request. Do not expose filesystem or record details.
        authorized, authorization_reason = False, "authorization_check_failed"

    if not authorized:
        reason = str(authorization_reason or "authorization_invalid")
        emit_progress(
            progress, "Authorization Preflight", "stopped",
            f"Unified QA dihentikan sebelum request: {reason}.",
        )
        stages = [
            WorkflowStage(
                "authorization_preflight", ResultStatus.BLOCKED,
                f"Otorisasi tidak valid: {reason}",
            ),
            WorkflowStage("frontend_qa", None, "Dilewati: preflight otorisasi gagal."),
            WorkflowStage("website_discovery", None, "Dilewati: preflight otorisasi gagal."),
            WorkflowStage("generic_uat", None, "Dilewati: preflight otorisasi gagal."),
            WorkflowStage("authentication_discovery", None, "Dilewati: preflight otorisasi gagal."),
        ]
        return _make_result(
            config, None, None, None, None, stages, progress,
            permission_check_status="blocked",
            permission_check_message=reason,
        )

    emit_progress(
        progress, "Authorization Preflight", "completed",
        "Otorisasi valid untuk target dan scope frontend read-only.",
    )

    controller = RequestSafetyController(
        config.max_requests_per_minute,
        config.stop_after_consecutive_403,
    )
    frontend = _run_with_progress(
        run_frontend_qa_workflow, progress, config,
        timeout_ms=timeout_ms, controller=controller,
    )
    stages = [
        WorkflowStage(
            "authorization_preflight", ResultStatus.PASSED,
            "Otorisasi valid untuk target dan scope frontend read-only.",
        ),
        WorkflowStage(
            "frontend_qa",
            frontend.status,
            "Workflow homepage, gambar, dan tautan selesai.",
        ),
    ]
    discovery = None
    generic_uat = None
    authentication = None

    if frontend.status == ResultStatus.ACCESS_RESTRICTED or controller.is_stopped:
        reason = frontend.stopped_reason or "Akses frontend dibatasi."
        stages.extend((
            WorkflowStage("website_discovery", None, f"Dilewati: {reason}"),
            WorkflowStage("generic_uat", None, f"Dilewati: {reason}"),
            WorkflowStage("authentication_discovery", None, f"Dilewati: {reason}"),
        ))
        _emit_skipped(progress, "Website Discovery", reason)
        _emit_skipped(progress, "Generic UAT", reason)
        _emit_skipped(progress, "Authentication Discovery", reason)
        return _make_result(
            config, frontend, discovery, generic_uat, authentication, stages,
            progress,
        )

    discovery = _run_with_progress(
        discover_website, progress, config,
        timeout_ms=timeout_ms, controller=controller,
    )
    stages.append(WorkflowStage(
        "website_discovery", discovery.status, discovery.message
    ))
    if discovery.status == ResultStatus.ACCESS_RESTRICTED or controller.is_stopped:
        reason = discovery.stopped_reason or "Website Discovery dibatasi."
        stages.extend((
            WorkflowStage("generic_uat", None, f"Dilewati: {reason}"),
            WorkflowStage("authentication_discovery", None, f"Dilewati: {reason}"),
        ))
        _emit_skipped(progress, "Generic UAT", reason)
        _emit_skipped(progress, "Authentication Discovery", reason)
        return _make_result(
            config, frontend, discovery, generic_uat, authentication, stages,
            progress,
        )

    generic_uat = _run_with_progress(
        inspect_generic_uat, progress, config, discovery,
        timeout_ms=timeout_ms, controller=controller,
    )
    stages.append(WorkflowStage(
        "generic_uat", generic_uat.status, generic_uat.message
    ))
    if generic_uat.status == ResultStatus.ACCESS_RESTRICTED or controller.is_stopped:
        reason = generic_uat.stopped_reason or "Generic UAT dibatasi."
        stages.append(WorkflowStage(
            "authentication_discovery", None, f"Dilewati: {reason}"
        ))
        _emit_skipped(progress, "Authentication Discovery", reason)
        return _make_result(
            config, frontend, discovery, generic_uat, authentication, stages,
            progress,
        )

    authentication = _run_with_progress(
        inspect_authentication, progress, config, discovery,
        timeout_ms=timeout_ms, controller=controller,
    )
    stages.append(WorkflowStage(
        "authentication_discovery", authentication.status,
        authentication.message,
    ))
    return _make_result(
        config, frontend, discovery, generic_uat, authentication, stages,
        progress,
    )


def _run_with_progress(function, progress, *args, **kwargs):
    if progress is None:
        return function(*args, **kwargs)
    try:
        return function(*args, progress=progress, **kwargs)
    except Exception:
        emit_progress(
            progress, "Unified Inspection", "failed",
            "Tahap Unified QA gagal sebelum workflow selesai.",
        )
        raise


def _emit_skipped(progress, stage, reason):
    emit_progress(progress, stage, "stopped", f"Dilewati karena akses dibatasi: {reason}")


def _make_result(
    config, frontend, discovery, generic_uat, authentication, stages, progress=None,
    permission_check_status="authorized",
    permission_check_message="Otorisasi valid untuk target dan scope workflow.",
):
    statuses = [stage.status for stage in stages if stage.status is not None]
    if ResultStatus.ACCESS_RESTRICTED in statuses:
        status = ResultStatus.ACCESS_RESTRICTED
    elif ResultStatus.FAILED in statuses:
        status = ResultStatus.FAILED
    elif ResultStatus.BLOCKED in statuses:
        status = ResultStatus.BLOCKED
    elif ResultStatus.TIMEOUT in statuses:
        status = ResultStatus.TIMEOUT
    elif ResultStatus.NEEDS_REVIEW in statuses:
        status = ResultStatus.NEEDS_REVIEW
    elif ResultStatus.INCONCLUSIVE in statuses:
        status = ResultStatus.INCONCLUSIVE
    else:
        status = ResultStatus.PASSED

    evidence_ids = _evidence_ids(
        config, frontend, discovery, generic_uat
    )
    screenshot_paths = (
        {Path(frontend.homepage.screenshot_path).resolve()}
        if frontend is not None and frontend.homepage.screenshot_path
        else set()
    )
    if discovery is not None:
        screenshot_paths.update(
            Path(page.screenshot_path).resolve()
            for page in discovery.pages if page.screenshot_path
        )
    if generic_uat is not None:
        screenshot_paths.update(
            Path(page.screenshot_path).resolve()
            for page in generic_uat.pages if page.screenshot_path
        )
    expected_evidence = len(screenshot_paths)
    verified_evidence = len(evidence_ids)

    if expected_evidence == 0:
        evidence_status = "not_required"
    elif verified_evidence == expected_evidence:
        evidence_status = "verified"
    else:
        evidence_status = "failed"

    result = UnifiedQAWorkflowResult(
        project_id=config.project_id,
        status=status,
        frontend=frontend,
        website_discovery=discovery,
        generic_uat=generic_uat,
        authentication_discovery=authentication,
        stages=tuple(stages),
        evidence_ids=evidence_ids,
        evidence_status=evidence_status,
        expected_evidence=expected_evidence,
        verified_evidence=verified_evidence,
        permission_check_status=permission_check_status,
        permission_check_message=permission_check_message,
    )

    evidence_progress_status = (
        "failed" if evidence_status == "failed" else "completed"
    )
    emit_progress(
        progress, "Unified Evidence Collection", evidence_progress_status,
        (f"Evidence status: {evidence_status}; verified: "
         f"{verified_evidence}/{expected_evidence} file screenshot "
         "melalui registry dan SHA-256."),
        verified_evidence, expected_evidence,
    )

    observed_statuses = [result.status]
    observed_statuses.extend(
        item.status for stage_result in (
            frontend, discovery, generic_uat, authentication
        ) if stage_result is not None
        for item in (
            getattr(stage_result, "pages", ())
            if stage_result is not frontend
            else (getattr(stage_result, "homepage", None),
                  *getattr(stage_result, "image_results", ()),
                  *getattr(stage_result, "link_results", ()))
        ) if item is not None and hasattr(item, "status")
    )
    terminal = terminal_status_for_results(observed_statuses)
    if evidence_status == "failed" and terminal == "completed":
        terminal = "failed"
    emit_progress(
        progress, "Unified Inspection", terminal,
        "Unified inspection selesai diproses; hasil QA: "
        f"{result.status.value}; evidence verified: "
        f"{verified_evidence}/{expected_evidence}.",
    )
    return result


def _evidence_ids(config, frontend, discovery, generic_uat):
    screenshot_paths = set()
    homepage_path = (
        frontend.homepage.screenshot_path if frontend is not None else None
    )
    if homepage_path:
        screenshot_paths.add(Path(homepage_path).resolve())
    if discovery is not None:
        screenshot_paths.update(
            Path(item.screenshot_path).resolve()
            for item in discovery.pages if item.screenshot_path
        )
    if generic_uat is not None:
        screenshot_paths.update(
            Path(item.screenshot_path).resolve()
            for item in generic_uat.pages if item.screenshot_path
        )
    if not screenshot_paths:
        return ()

    try:
        evidence_dir = (Path(config.project_dir) / "evidence").resolve()
        matches = []
        for record in list_evidence(config.project_id):
            candidate = (evidence_dir / record["file_path"]).resolve()
            if candidate in screenshot_paths and verify_evidence(
                config.project_id, record["evidence_id"]
            ):
                matches.append(record["evidence_id"])
        return tuple(matches)
    except (OSError, ValueError, KeyError, TypeError):
        return ()
