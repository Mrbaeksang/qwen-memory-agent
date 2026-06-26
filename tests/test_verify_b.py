from qmem.llm.provider import FakeProvider
from qmem.store.memory import LessonStore
from qmem.verify.verifier import verify_and_store, verify_b


def test_verify_b_uses_web_search_and_marks_source():
    provider = FakeProvider(completion="Use Depends() (current)")

    lesson = verify_b({"tech": "fastapi", "wrong": "old di", "context": "deps"}, provider)

    assert lesson["source"] == "web_search"
    assert lesson["trigger"] == "fastapi | deps"
    assert provider.calls[-1]["web_search"] is True


def test_verify_b_degrades_without_web_search():
    provider = FakeProvider(completion="x", supports_web_search=False)

    assert verify_b({"tech": "fastapi", "wrong": "old"}, provider) is None


def test_verify_and_store_falls_back_to_web_when_no_package(tmp_path):
    store = LessonStore(tmp_path / "s.db")
    provider = FakeProvider(completion="web-sourced fix")

    created = verify_and_store(
        [{"tech": "ghostlib", "wrong": "x", "context": "c"}], [tmp_path], provider, store
    )

    assert len(created) == 1
    assert created[0]["source"] == "web_search"


def test_no_lesson_when_no_package_and_no_web_search(tmp_path):
    store = LessonStore(tmp_path / "s.db")
    provider = FakeProvider(completion="x", supports_web_search=False)

    created = verify_and_store(
        [{"tech": "ghostlib", "wrong": "x"}], [tmp_path], provider, store
    )

    assert created == []
