import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from qmem.daemon.app import create_app


@pytest_asyncio.fixture
async def client(tmp_path):
    """Client to the daemon HTTP API (Seam 1), isolated with a temp SQLite db."""
    app = create_app(db_path=tmp_path / "mem.db")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def make_client(tmp_path):
    """Factory that builds a client with an injected provider (use via async with)."""

    def _make(provider=None):
        app = create_app(db_path=tmp_path / "mem.db", provider=provider)
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    return _make
