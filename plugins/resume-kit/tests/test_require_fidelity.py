"""The fidelity check may skip on a laptop, never on CI.

Every skip path in check-fidelity.sh exits 0. That is right for a
contributor who cannot be expected to carry one exact typst, and wrong for
a runner that installs its own toolchain: there a skip means the workflow
is broken, and a green tick would mean the renderer went unchecked.

RESUME_KIT_REQUIRE_FIDELITY=1 turns those skips into failures. These tests
drive the version-mismatch path with a stub typst on PATH, because that is
the skip most likely to fire for real: the pinned version moves and the
install step keeps working.
"""
import os
import pathlib
import subprocess
import shutil
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
CHECK = REPO / "skills" / "resume" / "tools" / "check-fidelity.sh"


def _expected_typst():
    """The version check-fidelity.sh pins, read from the script rather than
    duplicated here, so bumping the pin cannot leave this test stale."""
    for line in CHECK.read_text().splitlines():
        if line.startswith("expected_typst="):
            return line.split("=", 1)[1].strip().strip('"')
    raise AssertionError("no expected_typst= line in check-fidelity.sh")


def _stub_typst_dir(version):
    """A directory holding a `typst` that reports `version` and otherwise
    delegates to the real one, so only the version check is perturbed."""
    real = shutil.which("typst")
    directory = tempfile.mkdtemp(prefix="stub_typst_")
    stub = pathlib.Path(directory) / "typst"
    stub.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "--version" ]; then echo "typst %s"; else exec %s "$@"; fi\n'
        % (version, real)
    )
    stub.chmod(0o755)
    return directory


def _run(env_extra, path_prefix=None):
    env = dict(os.environ, **env_extra)
    if path_prefix:
        env["PATH"] = path_prefix + os.pathsep + env["PATH"]
    return subprocess.run([str(CHECK)], capture_output=True, text=True, env=env)


@unittest.skipUnless(shutil.which("typst") and shutil.which("pdftotext"),
                     "needs typst and pdftotext")
class RequireFidelityTests(unittest.TestCase):
    def test_a_version_mismatch_skips_when_not_required(self):
        directory = _stub_typst_dir("0.99.0")
        try:
            result = _run({"RESUME_KIT_REQUIRE_FIDELITY": ""}, directory)
        finally:
            shutil.rmtree(directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SKIP:", result.stdout)

    def test_a_version_mismatch_fails_when_required(self):
        """Without the require mode this returns 0 and the suite is green
        with the renderer unchecked. That is the hole being closed."""
        directory = _stub_typst_dir("0.99.0")
        try:
            result = _run({"RESUME_KIT_REQUIRE_FIDELITY": "1"}, directory)
        finally:
            shutil.rmtree(directory)
        self.assertEqual(result.returncode, 1,
                         f"expected failure, got {result.returncode}: "
                         f"{result.stdout!r} {result.stderr!r}")
        self.assertIn("0.99.0", result.stderr)
        self.assertIn("renderer went unchecked", result.stderr)

    def test_a_matching_version_still_passes_when_required(self):
        """The require mode must not turn a good run red.

        Guarded on the ambient typst actually being the pinned one: on a
        host with a different version there is no good run to observe, and
        asserting one would make this test report a toolchain difference as
        a defect in the require mode.
        """
        expected = _expected_typst()
        actual = subprocess.run(["typst", "--version"], capture_output=True,
                                text=True).stdout.split()[1]
        if actual != expected:
            self.skipTest(f"host typst is {actual}, baseline pins {expected}")
        result = _run({"RESUME_KIT_REQUIRE_FIDELITY": "1"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS:", result.stdout)


if __name__ == "__main__":
    unittest.main()
