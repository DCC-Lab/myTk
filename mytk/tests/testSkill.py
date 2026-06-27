import importlib.resources as resources
import tempfile
import unittest
from pathlib import Path

from mytk.__main__ import SKILL_RESOURCE, install_skill

# The skill exists in two committed places: the repository copy that Claude Code
# auto-discovers from a clone (.claude/skills/mytk/SKILL.md), and the packaged
# copy shipped in the wheel for `pip install mytk` users
# (mytk/resources/skills/mytk/SKILL.md). They must stay byte-identical.
PACKAGE_SKILL = (
    Path(__file__).resolve().parents[1] / "resources" / "skills" / "mytk" / "SKILL.md"
)
REPO_SKILL = (
    Path(__file__).resolve().parents[2] / ".claude" / "skills" / "mytk" / "SKILL.md"
)


class TestSkillPackaging(unittest.TestCase):
    def test_packaged_skill_is_accessible_as_resource(self):
        # This is how the installer (and thus a pip user) reaches the skill.
        source = resources.files("mytk.resources").joinpath(SKILL_RESOURCE)
        self.assertTrue(source.is_file())
        self.assertIn("NotificationCenter", source.read_text(encoding="utf-8"))

    def test_repo_and_packaged_skill_in_sync(self):
        if not REPO_SKILL.exists():
            self.skipTest("repository .claude skill not present (installed package)")
        self.assertEqual(
            PACKAGE_SKILL.read_text(encoding="utf-8"),
            REPO_SKILL.read_text(encoding="utf-8"),
            "The packaged skill and the .claude/ repo skill have drifted. "
            "Copy .claude/skills/mytk/SKILL.md to mytk/resources/skills/mytk/SKILL.md "
            "(or vice versa) so they match.",
        )

    def test_install_skill_to_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            import os

            previous = os.getcwd()
            try:
                os.chdir(tmp)
                result = install_skill(scope="project")
            finally:
                os.chdir(previous)

            self.assertEqual(result, 0)
            installed = Path(tmp) / ".claude" / "skills" / "mytk" / "SKILL.md"
            self.assertTrue(installed.is_file())
            self.assertEqual(
                installed.read_text(encoding="utf-8"),
                PACKAGE_SKILL.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
