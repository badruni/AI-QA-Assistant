
import unittest

from core.security import sanitize_text, sanitize_url


class TestSensitiveDataFilter(unittest.TestCase):

    def assert_secret_hidden(self, text, secret):
        result = sanitize_text(text)

        self.assertNotIn(
            secret,
            result,
            msg=f"Data sensitif masih terlihat: {result}"
        )

        self.assertIn("[REDACTED", result)

    def test_password(self):
        self.assert_secret_hidden(
            "password=MySecret123",
            "MySecret123"
        )

    def test_json_token(self):
        self.assert_secret_hidden(
            '"access_token": "ABC123SECRET"',
            "ABC123SECRET"
        )

    def test_authorization_header(self):
        self.assert_secret_hidden(
            "Authorization: Bearer TESTTOKEN123",
            "TESTTOKEN123"
        )

    def test_cookie_header(self):
        self.assert_secret_hidden(
            "Cookie: sessionid=SESSION123; csrf=CSRF456",
            "SESSION123"
        )

    def test_url_credentials(self):
        self.assert_secret_hidden(
            "https://user123:pass123@example.com/login",
            "pass123"
        )

    def test_url_query_token(self):
        self.assert_secret_hidden(
            "https://example.com/?token=URLTOKEN123",
            "URLTOKEN123"
        )

    def test_signature_and_signed_url_parameter_variants(self):
        for key in (
            "sig", "signature", "X-Amz-Signature", "api-key",
            "client_secret", "access_token", "credential",
        ):
            with self.subTest(key=key):
                self.assert_secret_hidden(
                    f"https://example.test/path?lang=id&{key}=SYNTHETIC_SECRET_2026",
                    "SYNTHETIC_SECRET_2026",
                )

    def test_safe_url_redacts_secret_values_and_keeps_ordinary_query(self):
        value = (
            "https://example.test/path?lang=id&page=2&token=SYNTHETIC_SECRET_2026"
            "&X-Amz-Signature=another-secret#access_token=fragment-secret"
        )
        safe = sanitize_url(value)
        self.assertNotIn("SYNTHETIC_SECRET_2026", safe)
        self.assertNotIn("another-secret", safe)
        self.assertNotIn("fragment-secret", safe)
        self.assertIn("lang=id", safe)
        self.assertIn("page=2", safe)
        self.assertIn("token=[REDACTED]", safe)
        self.assertIn("X-Amz-Signature=[REDACTED]", safe)

    def test_jwt(self):
        jwt = (
            "eyJhbGciOiJIUzI1NiJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
            "abcdefghijklmnop123456"
        )

        self.assert_secret_hidden(jwt, jwt)


if __name__ == "__main__":
    unittest.main()
