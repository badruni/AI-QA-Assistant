import unittest

from core.access_classification import classify_access_restriction


class AccessClassificationTests(unittest.TestCase):
    def test_cloudflare_challenge_is_classified_without_retaining_page_text(self):
        result = classify_access_restriction(
            200, "Just a moment...",
            "Checking your browser before accessing this site.",
        )
        self.assertTrue(result.restricted)
        self.assertEqual(result.classification, "CLOUDFLARE_CHALLENGE")
        self.assertEqual(result.provider, "cloudflare")
        self.assertIn("challenge_phrase", result.indicators)

    def test_cloudflare_marker_and_challenge_phrase_are_classified(self):
        result = classify_access_restriction(
            403, "Attention Required! | Cloudflare",
            "cf-chl- challenge-platform. Verify you are human.",
        )
        self.assertEqual(result.classification, "CLOUDFLARE_CHALLENGE")

    def test_generic_security_challenge_is_restricted(self):
        result = classify_access_restriction(
            200, "Security verification", "Verify you are human to continue.",
        )
        self.assertTrue(result.restricted)
        self.assertEqual(result.classification, "SECURITY_CHALLENGE")

    def test_waf_bot_block_is_restricted(self):
        result = classify_access_restriction(
            200, "Request blocked", "Bot detected by security policy.",
        )
        self.assertEqual(result.classification, "WAF_BLOCK")

    def test_cloudflare_block_page_is_distinguished_from_challenge(self):
        result = classify_access_restriction(
            403, "Attention Required! | Cloudflare",
            "Sorry, you have been blocked. Error 1020.",
        )
        self.assertEqual(result.classification, "CLOUDFLARE_WAF_BLOCK")
        self.assertEqual(result.provider, "cloudflare")

    def test_cloudflare_site_reference_alone_is_not_restricted(self):
        result = classify_access_restriction(
            200, "Welcome", "This site is protected by Cloudflare.",
        )
        self.assertFalse(result.restricted)
        self.assertEqual(result.classification, "NONE")

    def test_ambiguous_just_a_moment_title_alone_is_not_restricted(self):
        result = classify_access_restriction(200, "Just a moment", "Welcome")
        self.assertFalse(result.restricted)

    def test_http_forbidden_is_recorded_as_access_restricted(self):
        result = classify_access_restriction(403, "Forbidden", "")
        self.assertEqual(result.classification, "HTTP_ACCESS_RESTRICTED")
        self.assertIn("http_403", result.indicators)

    def test_cloudflare_http_forbidden_records_provider(self):
        result = classify_access_restriction(
            403, "Forbidden | Cloudflare", "Request denied.",
        )
        self.assertEqual(result.classification, "CLOUDFLARE_ACCESS_RESTRICTED")
        self.assertEqual(result.provider, "cloudflare")

    def test_http_rate_limit_is_access_restricted(self):
        result = classify_access_restriction(429, "Too Many Requests", "")
        self.assertTrue(result.restricted)
        self.assertEqual(result.classification, "HTTP_RATE_LIMITED")
        self.assertIn("http_429", result.indicators)

    def test_cloudflare_rate_limit_records_provider(self):
        result = classify_access_restriction(
            429, "Cloudflare", "Request being rate limited"
        )
        self.assertEqual(result.classification, "CLOUDFLARE_ACCESS_RESTRICTED")


if __name__ == "__main__":
    unittest.main()
