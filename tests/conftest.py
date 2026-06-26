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
