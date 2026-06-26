"""데몬 진입점 — `python -m qmem` 로 루트 메모리 데몬을 띄운다."""

import uvicorn

from qmem.config import build_provider, default_db_path, load_dotenv, port
from qmem.daemon.app import create_app


def main() -> None:
    load_dotenv()
    app = create_app(db_path=default_db_path(), provider=build_provider())
    uvicorn.run(app, host="127.0.0.1", port=port(), log_level="warning")


if __name__ == "__main__":
    main()
