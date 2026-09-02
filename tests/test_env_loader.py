from app.env_loader import load_foundry_env


def test_nested_session_is_supported_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_USE_FOUNDRY", "1")
    monkeypatch.setenv("ANTHROPIC_FOUNDRY_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_FOUNDRY_RESOURCE", "test-resource")
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "test-entrypoint")

    bundle = load_foundry_env(tmp_path / "missing.env", None)

    assert "CLAUDECODE" not in bundle["env"]
    assert "CLAUDE_CODE_ENTRYPOINT" not in bundle["env"]
