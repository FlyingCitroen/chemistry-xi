import llm

ALL_VARS = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT", "GITHUB_MODELS_TOKEN"]


def clear(monkeypatch):
    for v in ALL_VARS:
        monkeypatch.delenv(v, raising=False)


def test_no_provider_returns_none(monkeypatch):
    clear(monkeypatch)
    assert llm.provider() is None and llm.chat("s", "u") is None


def test_github_provider(monkeypatch):
    clear(monkeypatch)
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "x")
    assert llm.provider() == "github"


def test_azure_wins_when_both(monkeypatch):
    clear(monkeypatch)
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "x")
    for v in ALL_VARS[:3]:
        monkeypatch.setenv(v, "y")
    assert llm.provider() == "azure"


def test_bad_credentials_never_crash(monkeypatch):
    clear(monkeypatch)
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "bad")
    monkeypatch.setenv("GITHUB_MODELS_ENDPOINT", "http://127.0.0.1:9")  # nothing listens here
    assert llm.chat("s", "u") is None and llm.LAST_ERROR
