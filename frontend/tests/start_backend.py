"""Run the existing FastAPI app against a throwaway database for browser tests."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='campus-e2e-') as temporary:
    env = {**os.environ, 'DATABASE_URL': f'sqlite:///{temporary}/test.db', 'SEED_PASSWORD': 'Activity3-test-password-123!', 'CORS_ORIGINS': '["http://127.0.0.1:5174"]'}
    for args in [['-m','alembic','upgrade','head'], ['-m','app.seed']]:
        subprocess.run([sys.executable, *args], cwd=root, env=env, check=True)
    subprocess.run([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8001'], cwd=root, env=env, check=True)
