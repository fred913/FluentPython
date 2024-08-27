import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from pydantic import BaseModel

from FluentPython.core.utils import (find_python_interpreter, myhash,
                                     query_interpreter_version, safe_rmtree)
from FluentPython.globals import OperationFailure


class ConfigObj(BaseModel):
    preferred_python_interpreter: str


class VersionConfig(BaseModel):
    name: str
    interpreter: str


@dataclass
class FluentPyVersion:
    name: str
    version: tuple[int, int, int]

    @property
    def hash(self):
        return myhash(self.name)

    @property
    def envdir(self):
        return _GlobalConfig.get_environments_dir() / self.hash

    @property
    def py_executable(self):
        return self.envdir / 'Scripts' / 'python'


class _GlobalConfig:

    @staticmethod
    def user_cfgdir():
        return Path('~/.fluentpython').expanduser()

    @classmethod
    def get_environments_dir(cls):
        res = cls.user_cfgdir() / 'environments'
        res.mkdir(parents=True, exist_ok=True)
        return res

    @property
    def environments_dir(self):
        return self.get_environments_dir()

    def __init__(self):
        self._base_config_path = self.user_cfgdir() / 'config.json'

        self._load_config()

    def _load_config(self, asserted: bool = False):
        if not self._base_config_path.is_file():
            python_interp = find_python_interpreter()
            if python_interp is None:
                logger.warning(
                    "Could not find a valid Python interpreter; using default interpreter"
                )
                python_interp = "python"

            self._config = ConfigObj(
                preferred_python_interpreter=python_interp)
            self._save_config()

        else:
            if asserted:
                raise ValueError(
                    f"Config file {self._base_config_path} is invalid; unable to remove before loading. Check permissions or delete manually."
                )

            try:
                self._config = ConfigObj.model_validate_json(
                    self._base_config_path.read_text("utf-8"))
            except json.JSONDecodeError:
                logger.error(
                    f"Invalid JSON in {self._base_config_path}; resetting to default (empty)"
                )
                self._base_config_path.unlink(False)
                return self._load_config(asserted=True)

    def _save_config(self):
        self._base_config_path.parent.mkdir(parents=True, exist_ok=True)
        self._base_config_path.write_text(
            json.dumps(self._config.model_dump(), indent=4,
                       ensure_ascii=False), "utf-8")

    def remake_global_config(self):
        interp = find_python_interpreter()
        if interp is None:
            logger.warning(
                "Could not find a valid Python interpreter; using default interpreter"
            )
            interp = "python3"

        self._config = ConfigObj(preferred_python_interpreter=interp)
        self._save_config()

    @property
    def cfg(self):
        return self._config

    def _list_version_dirs(self):
        return os.listdir(self.environments_dir)

    def list_versions(self) -> list[FluentPyVersion]:
        res = []
        for verdirname in self._list_version_dirs():
            corrupted = False
            while True:
                version_dir = self.environments_dir / verdirname
                ver_config_file = version_dir / 'fluentpy.json'
                try:
                    ver_config = VersionConfig.model_validate_json(
                        ver_config_file.read_text("utf-8"))

                except json.JSONDecodeError:
                    logger.error(
                        f"Invalid JSON in {ver_config_file}; skipping")
                    corrupted = True
                    break

                except FileNotFoundError:
                    logger.error(
                        f"Version directory {version_dir} is missing fluentpy.json; skipping"
                    )
                    corrupted = True
                    break

                ver_name = ver_config.name
                ver_interp = Path(ver_config.interpreter)
                if not ver_interp.is_file():
                    logger.warning(
                        f"Interpreter {ver_interp} for version {ver_name} does not exist; skipping"
                    )
                    corrupted = True
                    break

                ver_pyver = query_interpreter_version(ver_interp)

                break
            if not corrupted:
                res.append(FluentPyVersion(ver_name, ver_pyver))
            else:
                # remove the corrupted version directory
                logger.warning(
                    f"Removing corrupted version directory {version_dir}")
                try:
                    safe_rmtree(
                        base_path=self.environments_dir,
                        target_path=version_dir,
                    )
                except ValueError:
                    logger.error(
                        f"Failed to remove corrupted version directory {version_dir}: might be an unsafe, not relative to {self.environments_dir}"
                    )
        return res

    def create_environment(self,
                           name: str,
                           interpreter: str | Path | None = None):
        logger.debug(f"Creating environment {name}")
        if interpreter is None:
            interpreter = self.cfg.preferred_python_interpreter
            logger.debug(f"Using default interpreter {interpreter}")
        else:
            logger.debug(f"Using interpreter {interpreter}")

        try:
            interp_ver = query_interpreter_version(Path(interpreter))
        except FileNotFoundError:
            logger.error(f"Interpreter {interpreter} does not exist")
            raise OperationFailure(f"Interpreter {interpreter} does not exist")

        logger.debug(f"Interpreter version: {interp_ver}")

        # check if virtualenv is installed
        try:
            subprocess.check_output(
                [str(interpreter), "-m", "virtualenv", "--version"])
        except subprocess.CalledProcessError:
            # install via pip
            logger.debug(
                f"Virtualenv not found; installing virtualenv via pip")
            subprocess.check_output(
                [str(interpreter), "-m", "pip", "install", "virtualenv"])

        # create venv dir
        namehash = myhash(name)
        venv_dir = self.environments_dir / namehash

        venv_dir.mkdir(parents=True, exist_ok=True)

        # create venv using target interpreter
        venv_cmd = [str(interpreter), "-m", "venv", str(venv_dir)]
        logger.debug(f"Running command: {' '.join(venv_cmd)}")
        try:
            subprocess.check_output(venv_cmd)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create venv: {e.output.decode()}")
            raise OperationFailure(
                f"Failed to create venv: {e.output.decode()}")

        # create fluentpy.json
        ver_config = VersionConfig(name=name, interpreter=str(interpreter))
        ver_config_file = venv_dir / 'fluentpy.json'
        ver_config_file.write_text(
            json.dumps(ver_config.model_dump(), indent=4, ensure_ascii=False),
            "utf-8")

        logger.debug(f"Created environment {name} at {venv_dir}")
        return FluentPyVersion(name, interp_ver)

    def get_version(self, name: str) -> FluentPyVersion | None:
        for ver in self.list_versions():
            if ver.name == name:
                return ver
            if ver.hash == name:
                return ver
        return None

    def remove_environment(self, version: FluentPyVersion | str | None):
        if version is None:
            raise ValueError("Version not specified")

        if isinstance(version, str):
            version = self.get_version(version)

        if version is None:
            raise ValueError(
                f"Version {version} not found or not specified from source")

        logger.debug(f"Removing environment {version.name}")

        try:
            safe_rmtree(
                base_path=self.environments_dir,
                target_path=version.envdir,
            )
        except ValueError:
            logger.error(
                f"Failed to remove environment {version.name}: might be an unsafe, not relative to {self.environments_dir}"
            )
            raise OperationFailure(
                f"Failed to remove environment {version.name}: might be an unsafe, not relative to {self.environments_dir}"
            )

        logger.debug(f"Removed environment {version.name} successfully")


CFG = _GlobalConfig()
