from pathlib import Path

from loguru import logger
from typer import Typer

from FluentPython.core.config import GlobalConfig
from FluentPython.core.utils import query_interpreter_version

app = Typer()

cfg = GlobalConfig()


@app.command("list")
def lsit_envs():
    logger.debug("Listing environments...")

    for ver in cfg.list_versions():
        logger.info(f"Version: {ver}")

    logger.debug("Done.")


@app.command("getcfg")
def get_config():
    logger.debug("Getting config...")

    logger.info(f"Config: {cfg.cfg}")

    logger.info(
        f"Preferred interpreter: {cfg.cfg.preferred_python_interpreter}")
    logger.info(
        f"Preferred interpreter version: {query_interpreter_version(Path(cfg.cfg.preferred_python_interpreter))}"
    )


@app.command("cfgremake")
def remake_config():
    cfg.remake_global_config()
    logger.info("Config remade.")


@app.command("create")
def create_env(name: str):
    ver = cfg.create_environment(name)
    logger.info(f"Created environment {name} with version {ver}.")


@app.command("remove")
def remove_env():
    # list and remove one
    versions = cfg.list_versions()
    if not versions:
        logger.info("No environments to remove.")
        return

    for i, ver in enumerate(versions):
        logger.info(f"{i+1}. {ver}")

    choice = input("Enter the number of the environment to remove: ")
    try:
        choice = int(choice) - 1
        if choice < 0 or choice >= len(versions):
            raise ValueError
    except ValueError:
        logger.error("Invalid choice.")
        return

    cfg.remove_environment(versions[choice])
    logger.info(f"Removed environment {versions[choice]}.")


if __name__ == "__main__":
    app()
