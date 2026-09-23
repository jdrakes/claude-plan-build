import contextlib
import io
import os
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                 "skills", "resume-assessment", "tools"))
from keyword_staleness import candidates, main


class CandidatesTests(unittest.TestCase):
    def test_multiword_tracked_term_fully_masked(self):
        # "GitHub Actions" is tracked as one two-word entry; neither half
        # should surface as an untracked candidate on its own.
        tracked = [("GitHub Actions", "cicd"), ("Kubernetes", "cloud_infra")]
        text = "We use GitHub Actions and Kubernetes for deployment pipelines."
        result = candidates(text, tracked)
        self.assertNotIn("GitHub", result)
        self.assertNotIn("Actions", result)
        self.assertNotIn("Kubernetes", result)

    def test_untracked_term_surfaces(self):
        tracked = [("Kubernetes", "cloud_infra")]
        text = "Experience with Snowflake and Snowflake pipelines using Kubernetes."
        result = candidates(text, tracked)
        self.assertEqual(result["Snowflake"], 2)

    def test_stopwords_excluded(self):
        tracked = []
        text = "We are looking for a team with strong experience across the board."
        result = candidates(text, tracked)
        for noisy in ("the", "with", "for", "team", "experience", "across"):
            self.assertNotIn(noisy, [t.lower() for t in result])

    def test_min_len_excludes_short_tokens(self):
        tracked = []
        result = candidates("Go is a language, as is C or Go.", tracked, min_len=3)
        self.assertNotIn("Go", result)  # 2 chars, excluded by min_len
        self.assertNotIn("is", result)
        self.assertNotIn("as", result)

    def test_case_insensitive_tracked_masking(self):
        tracked = [("kafka", "messaging_streaming")]
        text = "We use Kafka and KAFKA extensively."
        result = candidates(text, tracked)
        self.assertNotIn("Kafka", result)
        self.assertNotIn("KAFKA", result)

    def test_empty_market_text_returns_empty_counter(self):
        self.assertEqual(candidates("", [("Kubernetes", "cloud_infra")]), Counter())

    def test_sentence_final_stopword_filtered_after_period_strip(self):
        # "experience." at a sentence end should be filtered as the stopword
        # "experience" after stripping the trailing period
        tracked = []
        text = "Strong background in Python and AWS. Experience with DevOps."
        result = candidates(text, tracked)
        self.assertNotIn("experience.", result)
        self.assertNotIn("experience", result)

    def test_dotted_suffix_preserved_through_period_strip(self):
        # "Node.js." at a sentence end should reduce to "Node.js", not "Node"
        # (preserving multi-dot suffixes)
        tracked = []
        text = "We use Node.js and React. Node.js powers the backend."
        result = candidates(text, tracked)
        self.assertIn("Node.js", result)
        self.assertNotIn("Node", result)

    def test_sentence_final_mention_aggregates_with_mid_sentence_mentions(self):
        # "Datadog" appears twice mid-sentence and once sentence-final
        # ("Datadog."). All three must count toward one candidate, not
        # split into "Datadog": 2 and "Datadog.": 1 (which would each sit
        # below --min-count 2 and hide a term mentioned 3 times).
        tracked = []
        text = ("We use Datadog daily. Datadog is central. "
                "Our stack includes Datadog.")
        result = candidates(text, tracked)
        self.assertEqual(result["Datadog"], 3)
        self.assertNotIn("Datadog.", result)

    def test_case_variants_aggregate_into_one_candidate(self):
        # Sentence-initial vs mid-sentence casing is ordinary prose. All
        # three spellings are one term mentioned three times, not three
        # terms mentioned once each - which at the default --min-count 2
        # would hide the term completely.
        tracked = []
        text = "Terraform is used. we run terraform. TERRAFORM again."
        result = candidates(text, tracked)
        self.assertEqual(result["Terraform"], 3)
        self.assertNotIn("terraform", result)
        self.assertNotIn("TERRAFORM", result)

    def test_display_form_is_the_most_frequent_casing(self):
        # The aggregated row is shown under the casing that dominates the
        # corpus, so output reads "PagerDuty", not "pagerduty".
        tracked = []
        text = "pagerduty pages. PagerDuty rotates. PagerDuty escalates."
        result = candidates(text, tracked)
        self.assertEqual(result["PagerDuty"], 3)
        self.assertNotIn("pagerduty", result)

    def test_punctuation_glued_stopwords_are_dropped(self):
        # "and" and "or" are both stopwords; the token they form by way of
        # a slash is not, so it clears the stopword check and can outrank
        # real candidates.
        tracked = []
        text = "Design and/or build systems. Ship and/or maintain."
        result = candidates(text, tracked)
        self.assertNotIn("and/or", result)

    def test_short_dotted_abbreviation_is_dropped(self):
        # "e.g" survives the length check as one 3-char token, but both of
        # its components are a single letter.
        tracked = []
        text = "Cloud platforms (e.g. AWS) matter. Tooling e.g. CI."
        result = candidates(text, tracked)
        self.assertNotIn("e.g", result)
        self.assertNotIn("e.g.", result)

    def test_ellipsis_aggregates_rather_than_forming_its_own_row(self):
        # Stripping only one trailing period leaves "Datadog.." behind.
        tracked = []
        text = "We run Datadog. Datadog everywhere... Datadog..."
        result = candidates(text, tracked)
        self.assertEqual(result["Datadog"], 3)
        self.assertNotIn("Datadog..", result)
        self.assertNotIn("Datadog.", result)

    def test_slash_separated_alternatives_count_as_separate_terms(self):
        # "Terraform/Pulumi" names two real tools, and a human reads it as
        # one mention of each. Counted as one glued token, a term named
        # three times across glued and bare forms totals three rather than
        # splitting into rows that each fall under --min-count.
        tracked = []
        text = ("Deep expertise in Terraform/Pulumi. Strong Terraform/Ansible "
                "background. We use Terraform daily for infrastructure.")
        result = candidates(text, tracked)
        self.assertEqual(result["Terraform"], 3)
        self.assertEqual(result["Pulumi"], 1)
        self.assertEqual(result["Ansible"], 1)
        self.assertNotIn("Terraform/Pulumi", result)
        self.assertNotIn("Terraform/Ansible", result)

    def test_trailing_slash_stripped_like_other_edge_punctuation(self):
        # A slash never ends a sentence but does end a token, so it has to
        # come off the edge like any other punctuation.
        tracked = []
        text = "Terraform/ Ansible. Terraform is core. Terraform again."
        result = candidates(text, tracked)
        self.assertEqual(result["Terraform"], 3)
        self.assertEqual(result["Ansible"], 1)
        self.assertNotIn("Terraform/", result)

    def test_missing_space_after_a_period_does_not_split_the_count(self):
        # "Datadog.We" is two sentences with the space missing. The glued-on
        # component is a stopword, so it is sentence furniture and comes off.
        tracked = []
        text = "Datadog.We alert on Datadog. Datadog rules."
        result = candidates(text, tracked)
        self.assertEqual(result["Datadog"], 3)
        self.assertNotIn("Datadog.We", result)

    def test_dotted_product_names_survive_the_component_split(self):
        # "js" is short but not a stopword, so it is part of the product's
        # name rather than glued-on sentence furniture: Node.js and Vue.js
        # stay whole exactly where Terraform/Pulumi splits.
        tracked = []
        text = ("Node.js and Vue.js are core. We ship Node.js services and "
                "Vue.js frontends.")
        result = candidates(text, tracked)
        self.assertEqual(result["Node.js"], 2)
        self.assertEqual(result["Vue.js"], 2)
        self.assertNotIn("Node", result)
        self.assertNotIn("Vue", result)


class MainOutputTests(unittest.TestCase):
    def _run_main(self, market_text, extra_args=()):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "market.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(market_text)
            argv = ["keyword_staleness.py", path, *extra_args]
            out = io.StringIO()
            with mock.patch.object(sys, "argv", argv):
                with contextlib.redirect_stdout(out):
                    main()
            return out.getvalue()

    def _rows(self, market_text, extra_args=()):
        """Parse main()'s printed table into {candidate: mentions}."""
        rows = {}
        for line in self._run_main(market_text, extra_args).splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit():
                rows[parts[0]] = int(parts[1])
        return rows

    def test_mixed_case_term_survives_default_min_count(self):
        # End to end against the real keywords.yaml: Datadog is untracked
        # there, and appears three times in three casings. With per-casing
        # counting each row sits at 1, below the default --min-count 2, and
        # the term never prints at all.
        out = self._run_main(
            "Datadog is our monitor. we run datadog nightly. "
            "DATADOG alerts our responders.\n"
        )
        self.assertNotIn("No untracked candidates", out)
        self.assertIn("Datadog", out)
        self.assertNotIn("DATADOG", out)

    def test_tracked_term_never_reaches_the_candidate_list(self):
        # Kubernetes is tracked in the real keywords.yaml; Datadog is not.
        out = self._run_main(
            "Kubernetes and Datadog. Kubernetes and Datadog again.\n"
        )
        self.assertIn("Datadog", out)
        self.assertNotIn("Kubernetes", out)

    def test_slash_glued_term_clears_the_default_min_count(self):
        # Datadog and Grafana are both untracked in the real keywords.yaml.
        # Counted as the glued token "Datadog/Grafana", Datadog's own row
        # sits at 1 and never prints at the default --min-count 2; split
        # into components it is a three-mention candidate. Every other word
        # here is a stopword or a single mention, so this is the whole table.
        rows = self._rows(
            "Datadog/Grafana is the stack. Datadog/Grafana again. "
            "Datadog pages on-call.\n"
        )
        self.assertEqual(rows, {"Datadog": 3, "Grafana": 2})


if __name__ == "__main__":
    unittest.main()
