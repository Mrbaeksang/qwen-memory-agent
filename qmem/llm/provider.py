"""LLM Provider abstraction — OpenAI-compatible, Qwen by default + a test fake.

Non-Qwen providers degrade gracefully when rerank/web-search is unsupported:
rerank falls back to identity order (FTS score only), web_search is disabled.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


@dataclass
class ProviderConfig:
    base_url: str
    chat_model: str
    extract_model: str
    rerank_model: str | None
    supports_rerank: bool
    supports_web_search: bool


class Provider(ABC):
    config: ProviderConfig

    @abstractmethod
    def complete(self, prompt: str, *, model: str | None = None, web_search: bool = False) -> str:
        ...

    def rerank(self, query: str, documents: list[str], top_n: int | None = None) -> list[int]:
        """Default degrade — identity order (keep the original order)."""
        order = list(range(len(documents)))
        return order[:top_n] if top_n else order

    @property
    def supports_rerank(self) -> bool:
        return self.config.supports_rerank

    @property
    def supports_web_search(self) -> bool:
        return self.config.supports_web_search


class QwenProvider(Provider):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = QWEN_BASE_URL,
        chat_model: str = "qwen-plus",
        extract_model: str = "qwen-turbo",
        rerank_model: str = "qwen3-rerank",
    ):
        self._api_key = api_key
        self._client = None
        self.config = ProviderConfig(
            base_url=base_url,
            chat_model=chat_model,
            extract_model=extract_model,
            rerank_model=rerank_model,
            supports_rerank=True,
            supports_web_search=True,
        )

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key, base_url=self.config.base_url)
        return self._client

    def complete(self, prompt: str, *, model: str | None = None, web_search: bool = False) -> str:
        kwargs: dict = {}
        if web_search:
            kwargs["extra_body"] = {"enable_search": True}
        resp = self._get_client().chat.completions.create(
            model=model or self.config.chat_model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return resp.choices[0].message.content or ""

    def rerank(self, query: str, documents: list[str], top_n: int | None = None) -> list[int]:
        import httpx

        url = self.config.base_url.replace("/compatible-mode/v1", "/compatible-api/v1") + "/reranks"
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self.config.rerank_model,
                "query": query,
                "documents": documents,
                "top_n": top_n,
            },
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json()["results"]
        return [r["index"] for r in results]


class FakeProvider(Provider):
    """Deterministic provider for tests — zero real API calls."""

    def __init__(
        self,
        *,
        completion: str = "",
        by_model: dict[str, str] | None = None,
        rerank_order: list[int] | None = None,
        supports_rerank: bool = True,
        supports_web_search: bool = True,
    ):
        self._completion = completion
        self._by_model = by_model or {}
        self._rerank_order = rerank_order
        self.calls: list[dict] = []
        self.config = ProviderConfig(
            base_url="fake://",
            chat_model="fake-chat",
            extract_model="fake-extract",
            rerank_model="fake-rerank" if supports_rerank else None,
            supports_rerank=supports_rerank,
            supports_web_search=supports_web_search,
        )

    def complete(self, prompt: str, *, model: str | None = None, web_search: bool = False) -> str:
        self.calls.append({"prompt": prompt, "model": model, "web_search": web_search})
        if model in self._by_model:
            return self._by_model[model]
        return self._completion

    def rerank(self, query: str, documents: list[str], top_n: int | None = None) -> list[int]:
        if not self.supports_rerank:
            return super().rerank(query, documents, top_n)
        order = self._rerank_order if self._rerank_order is not None else list(range(len(documents)))
        return order[:top_n] if top_n else order
