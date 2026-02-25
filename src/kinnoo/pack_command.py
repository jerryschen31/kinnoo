"""
pack_command.py: Implements packaging logic for kinnoo pack (task26).
- Builds/downloads wheel files for dependencies in requirements.txt.
- Stores wheels in a temp directory for packaging.
- Aborts with error if any dependency cannot be built/downloaded.
"""
import subprocess
import tempfile
import os
from pathlib import Path

class WheelBuildError(Exception):
    pass

def build_wheels(requirements_path: Path, wheels_dir: Path):
    """
    Build/download wheel files for all dependencies in requirements.txt using pip wheel.
    Wheels are stored in wheels_dir. Raises WheelBuildError on failure.
    """
    if not requirements_path.exists() or not requirements_path.read_text().strip():
        # No requirements or empty file: nothing to do
        return []
    wheels_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "python3", "-m", "pip", "wheel",
        "-r", str(requirements_path),
        "--wheel-dir", str(wheels_dir),
        "--no-deps"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise WheelBuildError(f"Failed to build wheels:\n{result.stderr}")
    # Return list of wheel files
    return list(wheels_dir.glob("*.whl"))
