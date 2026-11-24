import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from core import authorization_manager, project_manager


class AuthorizationManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "projects"
        self.root.mkdir()
        self.project_ids = ("AUTH_A", "AUTH_B")
        for project_id in self.project_ids:
            (self.root / project_id).mkdir()

        self.patcher = patch.object(project_manager, "PROJECTS_DIR", self.root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.target = "https://qa-example.test"
        self.expiry = (
            datetime.now(timezone.utc) + timedelta(days=7)
        ).isoformat()

    def create(self, project_id="AUTH_A", **overrides):
        values = {
            "project_id": project_id,
            "target_url": self.target,
            "authorized_by": "QA Lead",
            "scope": ["frontend", "read_only"],
            "expires_at": self.expiry,
            "admin_access_confirmed": True,
        }
        values.update(overrides)
        return authorization_manager.create_authorization(**values)

    def test_create_and_read_authorization(self):
        created = self.create()
        loaded = authorization_manager.get_authorization("AUTH_A")

        self.assertEqual(loaded["authorization_id"], created["authorization_id"])
        self.assertEqual(loaded["target_url"], self.target)
        self.assertEqual(loaded["status"], "active")
        self.assertEqual(loaded["scope"], ["frontend", "read_only"])

    def test_projects_have_separate_authorization_and_history(self):
        self.create("AUTH_A")
        self.create("AUTH_B", authorized_by="Different QA Lead")

        auth_a = authorization_manager.get_authorization("AUTH_A")
        auth_b = authorization_manager.get_authorization("AUTH_B")
        history_a = authorization_manager.list_authorization_history("AUTH_A")
        history_b = authorization_manager.list_authorization_history("AUTH_B")

        self.assertNotEqual(auth_a["authorization_id"], auth_b["authorization_id"])
        self.assertEqual(len(history_a), 1)
        self.assertEqual(len(history_b), 1)
        self.assertEqual(history_a[0]["authorized_by"], "QA Lead")
        self.assertEqual(history_b[0]["authorized_by"], "Different QA Lead")

    def test_missing_authorization_is_denied(self):
        allowed, reason = authorization_manager.validate_authorization(
            "AUTH_A", self.target
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "authorization_missing")

    def test_wrong_target_is_denied(self):
        self.create()
        allowed, reason = authorization_manager.validate_authorization(
            "AUTH_A", "https://other-example.test"
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "target_not_authorized")

    def test_scope_must_be_granted(self):
        self.create()
        allowed, reason = authorization_manager.validate_authorization(
            "AUTH_A", self.target, required_scope="cms_write"
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "scope_not_authorized")

        allowed, reason = authorization_manager.validate_authorization(
            "AUTH_A", self.target, required_scope="frontend"
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "authorized")

    def test_admin_confirmation_can_be_required(self):
        self.create(admin_access_confirmed=False)
        allowed, reason = authorization_manager.validate_authorization(
            "AUTH_A", self.target, require_admin_confirmation=True
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "admin_access_not_confirmed")

        allowed, reason = authorization_manager.validate_authorization(
            "AUTH_A", self.target, require_admin_confirmation=False
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "authorized")

    def test_expired_authorization_is_denied(self):
        expired = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat()
        with self.assertRaises(ValueError):
            self.create(expires_at=expired)

    def test_naive_expiry_is_rejected(self):
        naive = (datetime.now() + timedelta(days=1)).isoformat()
        with self.assertRaises(ValueError):
            self.create(expires_at=naive)

    def test_sensitive_query_and_fragment_targets_are_rejected(self):
        with self.assertRaises(ValueError):
            self.create(target_url="https://qa-example.test/?access_token=secret")
        with self.assertRaises(ValueError):
            self.create(target_url="https://qa-example.test/#token=secret")

    def test_invalid_project_id_is_rejected(self):
        with self.assertRaises(ValueError):
            authorization_manager.get_authorization("../AUTH_B")

    def test_revoke_denies_future_validation_and_appends_history(self):
        self.create()
        revoked = authorization_manager.revoke_authorization(
            "AUTH_A", "QA Manager", "Testing completed"
        )

        self.assertEqual(revoked["status"], "revoked")
        allowed, reason = authorization_manager.validate_authorization(
            "AUTH_A", self.target
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "authorization_inactive")
        history = authorization_manager.list_authorization_history("AUTH_A")
        self.assertEqual([item["event"] for item in history], ["created", "revoked"])

    def test_revoke_without_active_authorization_is_rejected(self):
        with self.assertRaises(ValueError):
            authorization_manager.revoke_authorization("AUTH_A", "QA Manager")

    def test_replacement_preserves_audit_history(self):
        first = self.create()
        second = self.create(authorized_by="New QA Lead")

        self.assertNotEqual(first["authorization_id"], second["authorization_id"])
        history = authorization_manager.list_authorization_history("AUTH_A")
        self.assertEqual([item["event"] for item in history], ["created", "replaced"])
        self.assertEqual(
            history[1]["previous_authorization_id"], first["authorization_id"]
        )

    def test_credentials_are_not_part_of_authorization_schema(self):
        record = self.create()
        serialized = json.dumps(record).casefold()
        for forbidden_key in (
            "password", "passwd", "token", "cookie", "authorization_header",
            "session", "api_key", "secret",
        ):
            self.assertNotIn(forbidden_key, serialized)

    def test_authorization_file_is_project_scoped(self):
        self.create("AUTH_A")
        path_a = self.root / "AUTH_A" / "authorization" / "authorization.json"
        path_b = self.root / "AUTH_B" / "authorization" / "authorization.json"

        self.assertTrue(path_a.is_file())
        self.assertFalse(path_b.exists())
        self.assertEqual(
            json.loads(path_a.read_text(encoding="utf-8"))["project_id"],
            "AUTH_A",
        )


if __name__ == "__main__":
    unittest.main()
