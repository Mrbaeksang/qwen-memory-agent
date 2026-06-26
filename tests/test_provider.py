from qmem.llm.provider import FakeProvider, QwenProvider


def test_fake_provider_returns_scripted_completion():
    p = FakeProvider(completion="AsyncSession")

    assert p.complete("how to use sqlalchemy async?") == "AsyncSession"
    assert p.calls[0]["prompt"].startswith("how to use")


def test_fake_provider_records_web_search_flag():
    p = FakeProvider(completion="x")

    p.complete("q", web_search=True)

    assert p.calls[0]["web_search"] is True


def test_qwen_provider_has_qwen_defaults():
    p = QwenProvider()

    assert p.config.base_url.endswith("/compatible-mode/v1")
    assert p.config.chat_model == "qwen-plus"
    assert p.config.extract_model == "qwen-turbo"
    assert p.config.rerank_model == "qwen3-rerank"
    assert p.supports_rerank is True
    assert p.supports_web_search is True


def test_provider_without_rerank_degrades_to_identity():
    p = FakeProvider(supports_rerank=False)

    assert p.supports_rerank is False
    assert p.rerank("q", ["a", "b", "c"]) == [0, 1, 2]


def test_fake_provider_rerank_custom_order():
    p = FakeProvider(rerank_order=[2, 0, 1])

    assert p.rerank("q", ["a", "b", "c"]) == [2, 0, 1]
