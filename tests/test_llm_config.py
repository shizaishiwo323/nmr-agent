from types import SimpleNamespace

import pytest

from t2_agent.agent import AgentRuntimeContext, run_agent_turn
from t2_agent.llm import PROVIDERS, LLMConfig, create_chat_completion, get_environment_api_key


class RecordingCompletions:
    def __init__(self, fail_on_temperature: bool = False):
        self.calls: list[dict] = []
        self.fail_on_temperature = fail_on_temperature

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_on_temperature and "temperature" in kwargs:
            raise ValueError("Unsupported value: 'temperature' does not support 0.2 with this model.")
        message = SimpleNamespace(content="ok", tool_calls=None, role="assistant")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def fake_client(**kwargs):
    return SimpleNamespace(chat=SimpleNamespace(completions=RecordingCompletions(**kwargs)))


def test_deepseek_preset_sends_thinking_flag_and_base_url():
    config = LLMConfig(api_key="k", model="deepseek-v4-pro", provider="deepseek", thinking_enabled=True)
    kwargs = config.request_kwargs()
    assert kwargs["extra_body"] == {"thinking": {"type": "enabled"}}
    assert kwargs["temperature"] == 0.2
    assert config.resolved_base_url() == "https://api.deepseek.com"


@pytest.mark.parametrize("provider", ["openai", "custom"])
def test_non_deepseek_providers_send_only_standard_fields(provider):
    config = LLMConfig(api_key="k", model="some-model", provider=provider, base_url="https://llm.example/v1", thinking_enabled=True)
    kwargs = config.request_kwargs()
    assert "extra_body" not in kwargs
    assert kwargs["model"] == "some-model"
    assert config.resolved_base_url() == "https://llm.example/v1"


def test_openai_preset_uses_official_endpoint_by_default():
    config = LLMConfig(api_key="k", model="gpt-4.1", provider="openai")
    assert config.resolved_base_url() == PROVIDERS["openai"].base_url


def test_temperature_is_dropped_when_model_rejects_it():
    client = fake_client(fail_on_temperature=True)
    config = LLMConfig(api_key="k", model="reasoning-model", provider="openai")
    create_chat_completion(client, config, messages=[])
    calls = client.chat.completions.calls
    assert len(calls) == 2
    assert "temperature" in calls[0] and "temperature" not in calls[1]


def test_environment_key_lookup_ignores_streamlit_secrets(monkeypatch):
    for name in ("DEEPSEEK_API_KEY", "OPENAI_API_KEY", "LLM_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    assert get_environment_api_key("openai") == (None, None)
    monkeypatch.setenv("LLM_API_KEY", "generic")
    assert get_environment_api_key("openai") == ("generic", "LLM_API_KEY")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    assert get_environment_api_key("openai") == ("openai-key", "OPENAI_API_KEY")


def test_agent_turn_runs_with_openai_provider(tmp_path):
    client = fake_client()
    context = AgentRuntimeContext(workspace=tmp_path)
    result = run_agent_turn(
        config=LLMConfig(api_key="k", model="gpt-4.1", provider="openai"),
        user_message="What can you do?",
        context=context,
        prior_messages=[],
        client=client,
        response_language="English",
    )
    call = client.chat.completions.calls[0]
    assert result.assistant_message == "ok"
    assert call["model"] == "gpt-4.1"
    assert call["tools"] and call["tool_choice"] == "auto"
    assert "extra_body" not in call
