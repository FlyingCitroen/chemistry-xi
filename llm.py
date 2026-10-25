"""LLM wrapper with two interchangeable providers (both via the `openai` SDK):
  1. Azure OpenAI  - AZURE_OPENAI_ENDPOINT / _API_KEY / _DEPLOYMENT
  2. GitHub Models - GITHUB_MODELS_TOKEN (PAT with models:read), optional GITHUB_MODELS_MODEL
Returns None when nothing is configured or a call fails, so callers fall back to templates."""
import os

_AZURE_VARS = ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT")
GITHUB_ENDPOINT = "https://models.github.ai/inference"
LAST_ERROR = None


def azure_configured() -> bool:
    return all(os.getenv(v) for v in _AZURE_VARS)


def provider():
    """'azure' | 'github' | None (Azure wins when both are set)."""
    if azure_configured():
        return "azure"
    if os.getenv("GITHUB_MODELS_TOKEN"):
        return "github"
    return None


def status() -> str:
    return {"azure": "🟢 Azure OpenAI connected",
            "github": "🟢 GitHub Models connected (free tier)"}.get(
        provider(), "⚪ Template mode — set AZURE_OPENAI_* or GITHUB_MODELS_TOKEN to enable the LLM narrator")


def _client_and_model():
    if provider() == "azure":
        from openai import AzureOpenAI
        client = AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                             api_key=os.environ["AZURE_OPENAI_API_KEY"],
                             api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"))
        return client, os.environ["AZURE_OPENAI_DEPLOYMENT"]
    from openai import OpenAI
    client = OpenAI(base_url=os.getenv("GITHUB_MODELS_ENDPOINT", GITHUB_ENDPOINT),
                    api_key=os.environ["GITHUB_MODELS_TOKEN"])
    return client, os.getenv("GITHUB_MODELS_MODEL", "openai/gpt-4o-mini")


def chat(system: str, user: str, max_tokens: int = 200):
    global LAST_ERROR
    if provider() is None:
        return None
    try:
        client, model = _client_and_model()
        resp = client.chat.completions.create(
            model=model, temperature=0.3, max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        return (resp.choices[0].message.content or "").strip() or None
    except Exception as exc:  # network, auth, quota, wrong model name... never crash the demo
        LAST_ERROR = repr(exc)
        return None
