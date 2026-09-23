"""The renderer fidelity check must find its inputs from its own location.

`check-fidelity.sh` used to anchor the repo at `$HOME/workspace/resumes`.
That is only true on one machine: a CI runner checks the repo out somewhere
else entirely with `$HOME` set to `/root` or `/home/runner`, and the check
failed with "fixture ... missing" before it ever compiled anything. These
tests pin the fix: the script resolves its own skill directory from its own
file location, and keeps working through a symlinked skill directory, which
is how a plugin is reached under `~/.claude/plugins/` (which is why the
resolution has to be physical, not logical -- walking ".." out of the
symlinked path lands in the wrong place otherwise).

Ported from resumes/tests/test_fidelity_paths.py. Only CheckFidelityPathTests
survives: CompareDefaultRefTests tested compare.py's DEFAULT_REF, and Task 4
deleted compare.py along with the golden-reference fixture it pointed at.
"""

import os
import shutil
import subprocess
import tempfile
import unittest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(PLUGIN_ROOT, "skills", "resume")
CHECK_FIDELITY_PATH = os.path.join(SKILL_DIR, "tools", "check-fidelity.sh")


@unittest.skipUnless(shutil.which("typst") and shutil.which("pdftotext"),
                     "needs typst and pdftotext")
class CheckFidelityPathTests(unittest.TestCase):
    def _run(self, script, env_home):
        env = dict(os.environ, HOME=env_home)
        return subprocess.run([script], capture_output=True, text=True, env=env)

    def test_passes_with_an_unrelated_home(self):
        with tempfile.TemporaryDirectory() as fake_home:
            result = self._run(CHECK_FIDELITY_PATH, fake_home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: renderer fidelity intact (60 lines match the baseline)",
                       result.stdout)

    def test_passes_when_invoked_through_a_symlinked_skill_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            link = os.path.join(tmp, "resume")
            os.symlink(SKILL_DIR, link)
            result = self._run(os.path.join(link, "tools", "check-fidelity.sh"),
                               tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: renderer fidelity intact (60 lines match the baseline)",
                       result.stdout)


if __name__ == "__main__":
    unittest.main()
