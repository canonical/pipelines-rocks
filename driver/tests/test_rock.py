# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import random
import string

import pytest
import subprocess

from charmed_kubeflow_chisme.rock import CheckRock


@pytest.fixture()
def rock_test_env(tmpdir):
    """Yields a temporary directory and random docker container name."""
    container_name = "".join(
        random.choices(string.ascii_lowercase, k=8)
    )
    yield tmpdir, container_name

    try:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


@pytest.mark.abort_on_fail
def test_rock(rock_test_env):
    """Test the Chisel-based rock.

    The driver is a one-shot launcher — it is NOT a daemon.  Pebble will
    start it, but it exits immediately (code 1) because no pipeline args are
    provided.  That is expected behaviour, not a crash.

    Validation: run the binary directly with a minimal flag set and verify
    that it walks past flag parsing and reaches its real error message,
    proving the static binary + Go version bump are sound.
    """
    temp_dir, container_name = rock_test_env
    check_rock = CheckRock("rockcraft.yaml")
    rock_image = check_rock.get_name()
    rock_version = check_rock.get_version()
    LOCAL_ROCK_IMAGE = f"{rock_image}:{rock_version}"

    # Fudge enough required flags to get past arg validation.
    # The expected failure is a real business-logic error, not a crash.
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "--entrypoint",
            "/bin/driver",
            LOCAL_ROCK_IMAGE,
            "--type",
            "CONTAINER",
            "--http_proxy",
            "",
            "--https_proxy",
            "",
            "--no_proxy",
            "",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    combined = result.stdout
    # The driver prints a fatal message starting with "KFP driver:"
    # when it fails on business logic — that proves it's the right binary.
    assert "KFP driver:" in combined, (
        f"Expected 'KFP driver:' prefix in output (binary identity check), got:\n{combined}"
    )
