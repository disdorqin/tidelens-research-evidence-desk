"""Run only the isolated STEM2Connect research snapshot collector."""
from __future__ import annotations
from pathlib import Path
import argparse
import json
import os
from .research import build

def main(argv=None):
    parser=argparse.ArgumentParser(prog="tidelens",description="Scientific Research Evidence Desk")
    subs=parser.add_subparsers(dest="command",required=True)
    research=subs.add_parser("research-build",help="refresh an official arXiv public metadata snapshot")
    research.add_argument("--max-papers",type=int,default=12)
    research.add_argument("--output",default="web/research-data.json")
    research.add_argument("--state",default=".state/research")
    research.add_argument("--enable-model",action="store_true")
    args=parser.parse_args(argv)
    backends=[]
    if args.enable_model:
        backends=[{
          "name":"authorized-free-gateway",
          "endpoint":os.environ.get("TIDELENS_LLM_ENDPOINT","http://127.0.0.1:8852/v1/chat/completions"),
          "model":os.environ.get("TIDELENS_LLM_MODEL","auto"),
          "api_key_env":"TIDELENS_LLM_API_KEY",
          "verified_free_tier":True,
          "enabled":bool(os.environ.get("TIDELENS_LLM_API_KEY")),
        }]
    report=build(output=Path(args.output),state=Path(args.state),
                 limit=args.max_papers,models=backends)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
