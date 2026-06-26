import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from qmem.daemon.app import create_app


@pytest_asyncio.fixture
async def client(tmp_path):
    """데몬 HTTP API(Seam 1)에 임시 SQLite로 격리해 접근하는 클라이언트."""
    app = create_app(db_path=tmp_path / "mem.db")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def make_client(tmp_path):
    """provider를 주입한 클라이언트를 만드는 팩토리 (async with 로 사용)."""

    def _make(provider=None):
        app = create_app(db_path=tmp_path / "mem.db", provider=provider)
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    return _make
