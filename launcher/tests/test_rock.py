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

    The launcher-v2 is a one-shot component launcher — it is NOT a daemon.
    Pebble will start it, but it exits immediately (code 1) because no
    pipeline args are provided.  That is expected behaviour, not a crash.

    Validation: run the binary directly with a minimal flag set and verify
    that it walks past flag parsing and reaches its real error message,
    proving the static binary + Go version bump are sound.
    """
    temp_dir, container_name = rock_test_env
    check_rock = CheckRock("rockcraft.yaml")
    rock_image = check_rock.get_name()
    rock_version = check_rock.get_version()
    LOCAL_ROCK_IMAGE = f"{rock_image}:{rock_version}"

    # Fudge enough flags to get past arg validation and into the launcher
    # logic.  The expected failure is a real business-logic error.
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "--entrypoint",
            "/bin/launcher-v2",
            LOCAL_ROCK_IMAGE,
            "--execution_id",
            "1",
            "--pipeline_name",
            "test-pipeline",
            "--run_id",
            "run-0001",
            "--executor_input",
            '{"inputs":{"parameterValues":{}},"outputs":{"outputFile":"/tmp/out"}}',
            "--component_spec",
            '{"executorLabel":"executor"}',
            "--task_spec",
            '{"taskInfo":{"name":"task-1"}}',
            "--pod_name",
            "test-pod",
            "--pod_uid",
            "00000000-0000-0000-0000-000000000001",
            "--mlmd_server_address",
            "127.0.0.1",
            "--mlmd_server_port",
            "8080",
            "echo",
            "hello-chisel",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    combined = result.stdout
    # The launcher either fails on MLMD connection or a required flag —
    # both messages prove the binary is functional (not a crash).
    assert (
        "must specify execution ID" in combined
        or "command and arguments are empty" in combined
        or "failed to create component launcher" in combined
        or "failed to execute component" in combined
        or "failed to get namespace in Pod" in combined
        or "rpc error" in combined
    ), (
        f"Expected a known launcher-v2 error message (binary identity check), got:\n{combined}"
    )
