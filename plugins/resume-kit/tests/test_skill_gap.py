"""Tests for skills/resume-assessment/tools/skill_gap.py.

The module lives under a path (leading dot, hyphens) that isn't importable
as a normal package, so it's loaded by file path instead.
"""

import importlib.util
import os
import unittest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_GAP_PATH = os.path.join(
    PLUGIN_ROOT, "skills", "resume-assessment", "tools", "skill_gap.py"
)


def _load_skill_gap():
    spec = importlib.util.spec_from_file_location("skill_gap", SKILL_GAP_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


skill_gap = _load_skill_gap()


class WordBoundaryPatternTests(unittest.TestCase):
    def test_go_does_not_match_inside_google(self):
        pat = skill_gap.word_boundary_pattern("Go")
        self.assertIsNone(pat.search("Google Cloud"))

    def test_go_does_not_match_inside_mongodb(self):
        pat = skill_gap.word_boundary_pattern("Go")
        self.assertIsNone(pat.search("MongoDB"))

    def test_go_matches_standalone_word(self):
        pat = skill_gap.word_boundary_pattern("Go")
        self.assertIsNotNone(pat.search("wrote Go services"))

    def test_csharp_matches_next_to_hash(self):
        pat = skill_gap.word_boundary_pattern("C#")
        self.assertIsNotNone(pat.search("C# developer"))

    def test_nodejs_matches_with_literal_dot(self):
        pat = skill_gap.word_boundary_pattern("Node.js")
        self.assertIsNotNone(pat.search("Node.js and React"))

    def test_nodejs_dot_is_not_a_wildcard(self):
        pat = skill_gap.word_boundary_pattern("Node.js")
        self.assertIsNone(pat.search("NodeXjs"))

    def test_ci_cd_matches_with_slash(self):
        pat = skill_gap.word_boundary_pattern("CI/CD")
        self.assertIsNotNone(pat.search("owns CI/CD"))

    def test_kafka_matches_case_insensitively(self):
        pat = skill_gap.word_boundary_pattern("kafka")
        self.assertIsNotNone(pat.search("Apache Kafka"))


class ResumeTextCoverageTests(unittest.TestCase):
    def test_skill_in_skills_list_is_covered(self):
        content = {"skills": ["Kubernetes"]}
        text = skill_gap.resume_text(content)
        pat = skill_gap.word_boundary_pattern("Kubernetes")
        self.assertIsNotNone(pat.search(text))

    def test_skill_in_experience_bullet_is_covered(self):
        content = {"experience": [{"bullets": ["Deployed services with Kubernetes"]}]}
        text = skill_gap.resume_text(content)
        pat = skill_gap.word_boundary_pattern("Kubernetes")
        self.assertIsNotNone(pat.search(text))

    def test_skill_in_summary_is_covered(self):
        content = {"summary": "Engineer experienced with Kubernetes at scale"}
        text = skill_gap.resume_text(content)
        pat = skill_gap.word_boundary_pattern("Kubernetes")
        self.assertIsNotNone(pat.search(text))

    def test_skill_in_education_only_is_not_covered(self):
        content = {"education": [{"notes": "Studied Kubernetes in a course"}]}
        text = skill_gap.resume_text(content)
        pat = skill_gap.word_boundary_pattern("Kubernetes")
        self.assertIsNone(pat.search(text))

    def test_skill_in_hobbies_only_is_not_covered(self):
        content = {"hobbies": ["Home-labs with Kubernetes"]}
        text = skill_gap.resume_text(content)
        pat = skill_gap.word_boundary_pattern("Kubernetes")
        self.assertIsNone(pat.search(text))

    def test_missing_skills_and_experience_returns_string_not_raise(self):
        content = {"name": "Someone"}
        text = skill_gap.resume_text(content)
        self.assertIsInstance(text, str)


if __name__ == "__main__":
    unittest.main()
