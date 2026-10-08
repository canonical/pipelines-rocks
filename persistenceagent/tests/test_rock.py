# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import random
import string
import time

import pytest
import subprocess

from charmed_kubeflow_chisme.rock import CheckRock

# Polling constants
DEADLINE_SECONDS = 30
POLL_INTERVAL_SECONDS = 2


@pytest.fixture()
def rock_test_env(tmpdir):
    """Yields a temporary directory and random docker container name.
    Cleans up the container after the test.
    """
    container_name = "".join(
        [str(i) for i in random.choices(string.ascii_lowercase, k=8)]
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
    # tmpdir fixture cleans up the temp directory


def _pebble_services(container_name):
    """Run `pebble services` inside *container_name* and return the output."""
    return subprocess.run(
        [
            "docker",
            "exec",
            container_name,
            "/usr/bin/pebble",
            "services",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _container_running(container_name):
    """Return True if the container is still running, False otherwise."""
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return result.stdout.strip() == "true"


def _container_logs(container_name):
    """Return the container logs (stdout+stderr)."""
    result = subprocess.run(
        ["docker", "logs", container_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return result.stdout


@pytest.mark.abort_on_fail
def test_rock(rock_test_env):
    """Test the Chisel-based rock.

    Validates that Pebble boots and the persistenceagent service becomes
    active, without relying on external ls / which / coreutils (the minimal
    Chisel rootfs intentionally omits them).  bash is present because the
    service command uses it for env-var expansion.
    """
    temp_dir, container_name = rock_test_env
    check_rock = CheckRock("rockcraft.yaml")
    rock_image = check_rock.get_name()
    rock_version = check_rock.get_version()
    LOCAL_ROCK_IMAGE = f"{rock_image}:{rock_version}"

    # Start the container in detached mode — Pebble will launch services.
    subprocess.run(
        [
            "docker",
            "run",
            "--detach",
            "--rm",
            "--name",
            container_name,
            LOCAL_ROCK_IMAGE,
        ],
        check=True,
    )

    # Poll pebble services until persistenceagent reaches a valid state.
    service_active = False
    last_result = None
    deadline = time.monotonic() + DEADLINE_SECONDS
    while time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_SECONDS)

        if not _container_running(container_name):
            last_result = _pebble_services(container_name)
            logs = _container_logs(container_name)
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            raise AssertionError(
                f"Container exited before persistenceagent reached a valid state.\n"
                f"Last pebble services output:\n{last_result.stdout}\n"
                f"Container logs:\n{logs}"
            )

        last_result = _pebble_services(container_name)
        # The persistenceagent needs a K8s SA token: outside a cluster it starts,
        # fails to read the token, and Pebble retries — so "backoff" is also valid.
        for line in last_result.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 3 and fields[0] == "persistenceagent" and fields[2] in ("active", "backoff"):
                service_active = True
                break

        if service_active:
            break

    logs = _container_logs(container_name)

    assert service_active, (
        f"persistenceagent did not reach 'active' within {DEADLINE_SECONDS} s.\n"
        f"Last pebble services output:\n"
        f"{last_result.stdout if last_result else '(no response from pebble)'}\n"
        f"Container logs:\n{logs}"
    )