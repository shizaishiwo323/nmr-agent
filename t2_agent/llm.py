"""LLM provider settings for the OpenAI-compatible chat-completions API.

The agent talks to the model through the OpenAI Python client, so any provider
that implements the chat-completions endpoint with function calling can be used
(OpenAI, DeepSeek, or a self-hosted/compatible gateway). Users supply their own
API key at runtime; the hosted web app never ships a key of its own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any


@dataclass(frozen=True)
class ProviderPreset:
    key: str
    label: str
    base_url: str
    models: tuple[str, ...]
    default_model: str
    supports_thinking: bool = False
    env_key: str = "LLM_API_KEY"


PROVIDERS: dict[str, ProviderPreset] = {
    "deepseek": ProviderPreset(
        key="deepseek",
        label="DeepSeek",
        base_url="https://api.deepseek.com",
        models=("deepseek-v4-pro", "deepseek-v4-flash"),
        default_model="deepseek-v4-pro",
        supports_thinking=True,
        env_key="DEEPSEEK_API_KEY",
    ),
    "openai": ProviderPreset(
        key="openai",
        label="OpenAI",
        base_url="https://api.openai.com/v1",
        models=(),
        default_model="gpt-4.1",
        env_key="OPENAI_API_KEY",
    ),
    "custom": ProviderPreset(
        key="custom",
        label="Custom (OpenAI-compatible)",
        base_url="",
        models=(),
        default_model="",
        env_key="LLM_API_KEY",
    ),
}
DEFAULT_PROVIDER = "deepseek"
DEFAULT_TEMPERATURE = 0.2


@dataclass
class LLMConfig:
    """Everything needed to call one OpenAI-compatible chat model."""

    api_key: str
    model: str
    provider: str = DEFAULT_PROVIDER
    base_url: str | None = None
    thinking_enabled: bool = False
    temperature: float | None = DEFAULT_TEMPERATURE
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def preset(self) -> ProviderPreset:
        return PROVIDERS.get(self.provider, PROVIDERS["custom"])

    def resolved_base_url(self) -> str | None:
        return (self.base_url or "").strip() or self.preset.base_url or None

    def make_client(self) -> Any:
        from openai import OpenAI

        return OpenAI(api_key=self.api_key, base_url=self.resolved_base_url())

    def request_kwargs(self) -> dict[str, Any]:
        """Provider-specific keyword arguments for ``chat.completions.create``."""

        kwargs: dict[str, Any] = {"model": self.model}
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.preset.supports_thinking:
            # DeepSeek extension; other providers would reject the unknown field.
            kwargs["extra_body"] = {"thinking": {"type": "enabled" if self.thinking_enabled else "disabled"}}
        kwargs.update(self.extra)
        return kwargs


def create_chat_completion(client: Any, config: LLMConfig, **kwargs: Any) -> Any:
    """Call the chat-completions endpoint, retrying once without ``temperature``.

    Some reasoning models accept only their default temperature and answer a
    custom value with a 400 error; dropping the field keeps those models usable.
    """

    request = {**config.request_kwargs(), **kwargs}
    try:
        return client.chat.completions.create(**request)
    except Exception as exc:
        if "temperature" in request and "temperature" in str(exc).lower():
            request.pop("temperature")
            return client.chat.completions.create(**request)
        raise


def get_environment_api_key(provider: str = DEFAULT_PROVIDER) -> tuple[str | None, str | None]:
    """Read an API key from the local environment (for running the app locally).

    Looks at the provider's own variable (e.g. ``OPENAI_API_KEY``) and then the
    generic ``LLM_API_KEY``. Streamlit secrets are deliberately not read, so a
    hosted deployment never pays for visitors' requests with a shared key.
    """

    preset = PROVIDERS.get(provider, PROVIDERS["custom"])
    for name in dict.fromkeys((preset.env_key, "LLM_API_KEY")):
        value = os.getenv(name)
        if value:
            return value, name
    return None, None
