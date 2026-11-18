from backend.security.dlp_engine import scan_for_secrets


def test_benign_text_has_no_secrets():
    result = scan_for_secrets("This is a public research report about cybersecurity.")
    assert result["has_sensitive_data"] is False
    assert len(result["findings"]) == 0
    assert result["sanitized_text"] == "This is a public research report about cybersecurity."


def test_detects_aws_key():
    result = scan_for_secrets("My credentials are AKIAIOSFODNN7EXAMPLE for AWS.")
    assert result["has_sensitive_data"] is True
    assert any(f["category"] == "AWS_ACCESS_KEY" for f in result["findings"])
    assert "[AWS_ACCESS_KEY_REDACTED]" in result["sanitized_text"]


def test_detects_openai_key():
    fake_key = "sk-abcdefghijklmnopqrstuvwxyz1234567890abcdef"
    result = scan_for_secrets(f"OpenAI token is {fake_key}")
    assert result["has_sensitive_data"] is True
    assert any(f["category"] == "OPENAI_API_KEY" for f in result["findings"])
    assert "[OPENAI_API_KEY_REDACTED]" in result["sanitized_text"]


def test_detects_private_key_header():
    key_text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA..."
    result = scan_for_secrets(key_text)
    assert result["has_sensitive_data"] is True
    assert any(f["category"] == "PRIVATE_KEY" for f in result["findings"])
