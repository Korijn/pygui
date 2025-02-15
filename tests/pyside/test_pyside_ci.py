import os

import pytest

# Make sure that this test is not skipped
# on GitHub CI. We should see a failure on CI
# when tests are run without PySide6
# See default environment variables for GitHub:
# https://docs.github.com/en/actions/learn-github-actions/variables#default-environment-variables
if not os.environ.get("CI"):
    pytest.importorskip("PySide6")


def test_pyside_runs_on_ci(qapp):
    assert qapp
