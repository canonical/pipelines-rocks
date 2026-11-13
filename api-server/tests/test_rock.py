# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
import subprocess


def test_rock(rock_container):
    """Test rock."""
    # assert the rock contains the expected files
    subprocess.run(
        ["docker", "exec", rock_container[1], "ls", "-la", "/bin/apiserver"],
        check=True,
    )

    subprocess.run(
        ["docker", "exec", rock_container[1], "ls", "-la", "/samples"],
        check=True,
    )

    # assert the schedule-writer handoff opt-out patch was compiled in
    subprocess.run(
        [
            "docker",
            "exec",
            rock_container[1],
            "grep",
            "-q",
            "KFP_DISABLE_SCHEDULE_WRITER_HANDOFF",
            "/bin/apiserver",
        ],
        check=True,
    )
