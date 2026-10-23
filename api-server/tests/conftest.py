# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.
import subprocess

import pytest
from charmed_kubeflow_chisme.rock import CheckRock


@pytest.fixture(scope="session")
def rock_container():
    """Run the rock once for the whole test session, then remove it."""
    check_rock = CheckRock("rockcraft.yaml")
    rock_image = check_rock.get_name()
    rock_version = check_rock.get_version()
    LOCAL_ROCK_IMAGE = f"{rock_image}:{rock_version}"

    container_id = subprocess.run(
        ["docker", "run", "-d", LOCAL_ROCK_IMAGE],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout.strip()

    yield check_rock, container_id

    subprocess.run(["docker", "rm", "--force", container_id])
