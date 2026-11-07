"""Launch the security monitor from the project directory.

Usage:
    python run.py
"""

from importlib import import_module
from pathlib import Path
import sys


def main():
    project_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_dir.parent))

    package_name = project_dir.name
    if not package_name.isidentifier():
        raise SystemExit(
            f"La carpeta del proyecto debe tener un nombre válido de módulo: "
            f"{package_name!r}"
        )

    module = import_module(f"{package_name}.__main__")
    module.main()


if __name__ == "__main__":
    main()
