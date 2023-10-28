import sys
from pathlib import Path

import pytest
import toml

py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
version = toml.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"][
    "version"
]


def test():
    path = f"v{version}/{py_version}"
    args = [
        "--cov=src",
        "--cov-branch",
        f"--cov-report=html:tests/report/{path}/coverage",
        f"--html=tests/report/{path}/report.html",
    ]
    args.extend(sys.argv[1:])  # Pass additional arguments to pytest if any
    pytest.main(args)
