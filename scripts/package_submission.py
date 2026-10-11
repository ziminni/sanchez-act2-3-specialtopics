"""Package both laboratory applications without local credentials or databases."""
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output'
ROOT_FILES = ['README.md', '.env.example', '.gitignore', '.python-version', 'alembic.ini', 'pytest.ini', 'requirements.txt', 'requirements.lock.txt']
FRONTEND_FILES = ['README.md', '.env.example', '.gitignore', 'index.html', 'package.json', 'package-lock.json', 'tsconfig.json', 'vite.config.ts', 'vitest.config.ts', 'playwright.config.ts']
DIRECTORIES = ['app', 'migrations', 'tests', 'docs', 'scripts', 'frontend/src', 'frontend/tests', 'frontend/docs', 'frontend/dist']
EXCLUDED = {'__pycache__', '.pytest_cache', 'node_modules', '.git', '.venv', 'test-results', 'playwright-report'}


def main():
    OUTPUT.mkdir(exist_ok=True)
    if not (ROOT / 'frontend/dist/index.html').exists():
        raise SystemExit('Run npm --prefix frontend run build first.')
    files = [ROOT / name for name in ROOT_FILES]
    files += [ROOT / 'frontend' / name for name in FRONTEND_FILES]
    for directory in DIRECTORIES:
        files += [path for path in (ROOT / directory).rglob('*') if path.is_file() and not any(part in EXCLUDED for part in path.relative_to(ROOT).parts) and path.suffix not in {'.pyc', '.db', '.zip'} and path.name not in {'.env', '.env.local'}]
    for template in [ROOT / '.env.example', ROOT / 'frontend/.env.example']:
        for line in template.read_text().splitlines():
            if line.startswith('SEED_PASSWORD=') and line.partition('=')[2].strip():
                raise SystemExit('Remove the seed password value from the public template first.')
    archive_path = OUTPUT / 'Activities-2-and-3-submission.zip'
    with ZipFile(archive_path, 'w', ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            archive.write(path, Path('Act2') / path.relative_to(ROOT))
        history = subprocess.check_output(['git', 'log', '--date=iso-strict', '--format=%h %ad %s', '--', '.'], cwd=ROOT, text=True)
        archive.writestr('Act2/SUBMISSION_HISTORY.txt', 'Local Git history for this activity. The actual repository remains in the parent project.\n\n' + history)
    with ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert not any(Path(name).name in {'.env', '.env.local'} for name in archive.namelist())
        print(f'Verified submission archive: {archive_path.name} ({len(archive.namelist())} files)')
    with ZipFile(OUTPUT / 'activity3-frontend-build.zip', 'w', ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / 'frontend/dist').rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT / 'frontend/dist'))


if __name__ == '__main__':
    main()
