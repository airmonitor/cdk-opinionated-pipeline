from os import walk
from pathlib import Path

import yaml


def load_properties(stage: str) -> dict:
    """Loads configuration properties from YAML files.

    Returns:
        props (dict): Dictionary containing configuration properties loaded from YAML files.

    Functionality:
        1. Load base config properties from cdk/config/config-ci-cd.yaml into prop dict.
        2. Set props['stage'] to value of STAGE environment variable.
        3. Walk the directory tree under cdk/config/<STAGE> and load properties from
           each .yaml file into props_env dict.
        4. Merge props_env into props to produce final props dict containing
           properties from all config files.
        5. Return populated props dict.
    """

    config_file_path = Path("cdk/config/config-ci-cd.yaml")
    with config_file_path.open(encoding="utf-8") as file:
        props = yaml.safe_load(file)
        props["stage"] = stage

    props_env: dict[list, dict] = {}

    # pylint: disable=W0612
    for dir_path, dir_names, files in walk(f"cdk/config/{stage}", topdown=False):  # noqa
        for file_name in files:
            file_path = Path(f"{dir_path}/{file_name}")
            with file_path.open(encoding="utf-8") as f:
                props_env |= yaml.safe_load(f)
                props = {**props_env, **props}

    return props
