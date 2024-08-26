import hashlib
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from loguru import logger

POSSIBLE_INTERPRETERS = ['python3', 'python']


def find_python_interpreter() -> str | None:
    for intp in POSSIBLE_INTERPRETERS:
        try:
            res = subprocess.check_output(
                f"{intp} -c \"import sys; print(sys.executable)\"", shell=True)
            res = res.decode().strip()
            return res
        except subprocess.CalledProcessError:
            pass
    return None


def query_interpreter_version(interpreter: Path) -> tuple[int, int, int]:
    if not interpreter.exists():
        raise FileNotFoundError(f"Python interpreter {interpreter} not found")

    res = subprocess.check_output(
        [str(interpreter), "-c", "import sys; print(sys.version_info[:3])"])
    res = res.decode().strip()
    # res: (X, Y, Z)
    res = tuple(int(x) for x in res[1:-1].split(','))

    if len(res) != 3:
        if len(res) == 2:
            res = (res[0], res[1], 0)
        else:
            logger.error(f"Invalid interpreter version: {res}")
            raise ValueError("Invalid interpreter version")
    return res


def safe_rmtree(base_path: Path, target_path: Path):
    # ensure target_path is a child of base_path
    if not target_path.is_relative_to(base_path):
        raise ValueError(f"{target_path} is not a child of {base_path}")
    # remove target_path
    shutil.rmtree(target_path, ignore_errors=False)


def myhash(s: str):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()
