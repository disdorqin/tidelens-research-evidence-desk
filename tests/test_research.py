import json
import tempfile
import unittest
from pathlib import Path
from xml.sax.saxutils import escape
from unittest.mock import patch
import os

from tidelens.research import parse_arxiv_atom, snapshot, build, FEED_URL

NS='http://www.w3.org/2005/Atom'
ABSTRACT=("This research system evaluates how agent coordination interacts with external scientific evidence. "
          "Each claimed improvement is described as a hypothesis until experiments reproduce the results. "
          "We observe a separation between original source traceability and scientific truth claims. ")
def feed(abstract=ABSTRACT, identifier="2611.12872v1", host="arxiv.org"):
    body=f'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="{NS}">
<title>arXiv Research</title>
<entry>
<id>https://{host}/abs/{identifier}</id>
<updated>2026-11-09T18:58:00Z</updated>
<published>2026-11-09T18:57:00Z</published>
<title>Trustworthy Research Agents with Evidence Provenance</title>
<author><name>Dr. Alice</name></author><author><name>Dr. Bob</name></author>
<summary>{escape(abstract)}</summary>
</entry>
</feed>'''
    return body.encode("utf-8")

class ScientificResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_original_author_abstract_parses_without_making_peer_review_claim(self):
        rows=parse_arxiv_atom(feed())
        self.assertEqual(len(rows),1)
        p=rows[0]
        self.assertEqual(p["id"],"2611.12872v1")
        self.assertFalse(p["peer_review_confirmed"])
        self.assertEqual(p["url"],"https://arxiv.org/abs/2611.12872v1")
        self.assertIn(p["evidence_quote"],p["abstract"])
        self.assertLessEqual(len(p["evidence_quote"].split()),20)
        self.assertIn("agents",p["topics"])

    def test_disallows_forged_arxiv_host(self):
        self.assertEqual(parse_arxiv_atom(feed(host="arxiv.org.evil.test")),[])

    def test_disallows_invalid_paper_id(self):
        self.assertEqual(parse_arxiv_atom(feed(identifier="../unsafe")),[])

    def test_disallows_xml_entities(self):
        raw=b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'+feed()
        with self.assertRaises(ValueError):
            parse_arxiv_atom(raw)

    def test_public_snapshot_only_short_quotes_not_full_abstracts(self):
        public, private = snapshot(feed(),published_at="2026-11-10T00:00:00+00:00")
        card=public["papers"][0]
        self.assertEqual(public["schema"],"tidelens-scientific-research/v1")
        self.assertNotIn("abstract",card)
        self.assertTrue(private["papers"][0]["abstract"].startswith("This research"))
        self.assertEqual(card["ai"]["status"],"not_run")
        self.assertFalse(public["is_user_or_peer_reviewed"])

    def test_model_quote_mismatch_never_claimed_as_verified(self):
        provider=[{"name":"fixture","enabled":True,"verified_free_tier":True,
                   "endpoint":"http://127.0.0.1:9999/v1/chat/completions",
                   "model":"fixture","api_key_env":"TIDELENS_TEST_AI"}]
        def false_claim(_):
            return {"model":"fixture","choices":[{"message":{"content":json.dumps({
                "summary":"Invented scientific claim without support",
                "quote":"The original paper proves guaranteed general intelligence"
            })}}]}
        with patch.dict(os.environ,{"TIDELENS_TEST_AI":"offline-value"}):
            public,_=snapshot(feed(),models=provider,transport=false_claim)
        self.assertEqual(public["papers"][0]["ai"]["status"],"unavailable_or_unverified")
        self.assertIsNone(public["papers"][0]["ai"]["summary"])

    def test_real_model_style_reply_requires_valid_exact_quote(self):
        provider=[{"name":"fixture","enabled":True,"verified_free_tier":True,
                   "endpoint":"http://127.0.0.1:9999/v1/chat/completions",
                   "model":"fixture","api_key_env":"TIDELENS_TEST_AI"}]
        def valid_response(_):
            return {"model":"fixture","choices":[{"message":{"content":json.dumps({
                "summary":"作者报告了证据追踪框架，但尚须独立验证。",
                "quote":"Each claimed improvement is described as a hypothesis"
            })}}]}
        with patch.dict(os.environ,{"TIDELENS_TEST_AI":"offline-value"}):
            public,_=snapshot(feed(),models=provider,transport=valid_response)
        self.assertEqual(public["papers"][0]["ai"]["status"],"quote_checked")
        self.assertTrue(public["papers"][0]["ai"]["source_quote_verified"])

    def test_end_to_end_build_keeps_full_abstract_private(self):
        public=self.base/"web"/"research-data.json"
        internal=self.base/".state"/"research"
        report=build(output=public,state=internal,fetcher=lambda _:feed())
        self.assertEqual(report["papers"],1)
        self.assertEqual(report["short_quotes_exact_match"],1)
        self.assertNotIn("We observe a separation",public.read_text())
        self.assertIn("Each claimed improvement", (internal/"arxiv-full-abstracts.json").read_text())

    def test_committed_public_research_snapshot_is_minimal_and_traceable(self):
        root=Path(__file__).resolve().parents[1]
        public=json.loads((root/"web"/"research-data.json").read_text(encoding="utf-8"))
        self.assertEqual(public["schema"],"tidelens-scientific-research/v1")
        self.assertEqual(public["source"],"arxiv_public_api")
        self.assertTrue(public["is_live_source_snapshot"])
        self.assertGreaterEqual(len(public["papers"]),6)
        self.assertEqual(len({p["id"] for p in public["papers"]}),len(public["papers"]))
        for paper in public["papers"]:
            self.assertNotIn("abstract",paper)
            self.assertTrue(paper["url"].startswith("https://arxiv.org/abs/"))
            self.assertLessEqual(len(paper["evidence_quote"].split()),20)
            self.assertEqual(len(paper["abstract_sha256"]),64)
            self.assertFalse(paper["peer_review_confirmed"])
            self.assertTrue(paper["quote_exact_match"])
            self.assertIn(paper["ai"]["status"],{"not_run","quote_checked","unavailable_or_unverified"})
            if paper["ai"]["status"]=="quote_checked":
                self.assertTrue(paper["ai"]["source_quote_verified"])

    def test_refuses_unapproved_public_output_filename(self):
        with self.assertRaises(ValueError):
            build(output=self.base/"research-auth.json",state=self.base/".state",
                  fetcher=lambda _:feed())

    def test_refuses_private_data_outside_ignored_state(self):
        with self.assertRaises(ValueError):
            build(output=self.base/"research-data.json",state=self.base/"public",
                  fetcher=lambda _:feed())

    def test_dashboard_structure_no_private_credentials_or_external_script(self):
        root=Path(__file__).resolve().parents[1]/"web"
        ui=(root/"index.html").read_text()
        script=(root/"research.js").read_text()
        css=(root/"research.css").read_text()
        self.assertIn('id="paperlist"',ui)
        self.assertIn('id="verify"',ui)
        self.assertIn('id="claimresult"',ui)
        self.assertIn("arxiv.org",ui)
        self.assertNotIn("eval(",script)
        self.assertNotIn(".innerHTML",script)
        self.assertNotIn("TIDELENS_LLM_API_KEY",script)
        self.assertIn("@media(max-width:670px)",css)

if __name__=="__main__":
    unittest.main()
