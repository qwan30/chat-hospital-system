import os
from pathlib import Path
db_path = Path('legacy4.db').resolve()
os.environ['DATABASE_URL'] = f'sqlite+aiosqlite:///{db_path.as_posix()}'

from hospital_ai.core.config import get_settings
print(get_settings().database_url)
