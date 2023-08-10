from pathlib import Path


def is_django_settings_file(file_path: Path):
    if "settings.py" not in file_path.name:
        return
    # the most telling fact is the presence of a manage.py file in the parent directory
    if file_path.parent.parent.is_dir():
        return "manage.py" in (f.name for f in file_path.parent.parent.iterdir())
    return False
