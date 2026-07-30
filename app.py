#!/usr/bin/env python3
"""
AI-Powered Data Solutions Accelerator — Web App
==================================================
A public-facing website: the visitor types a business requirement + schema,
clicks Generate, and all 6 agents run automatically on the server. Only the
final deliverable is shown to the visitor — nobody sees the API key, and
nobody needs to run anything themselves.

SECURITY NOTES (read before deploying publicly)
-------------------------------------------------
1. The API key lives ONLY in an environment variable on the server
   (OPENAI_API_KEY). It is never sent to the browser, never in this file's
   source, never in the GitHub repo.
2. Because this is public, an optional SITE_ACCESS_CODE environment variable
   gates access — set it on your hosting platform, and share that code only
   with people you want using this. Without it, anyone with the link could
   run agents against your API key and rack up real charges. If you leave
   SITE_ACCESS_CODE unset, the site is open to anyone — only do this if you
   are comfortable with unlimited public usage against your billing.
"""

import json
import os
from pathlib import Path

from flask import Flask, request, jsonify, render_template
from openai import OpenAI

app = Flask(__name__)

MODEL = "gpt-4o"  # verify current at platform.openai.com/docs/models
MAX_TOKENS = 8000
PROMPTS_DIR = Path(__file__).parent / "prompts"

client = OpenAI()  # reads OPENAI_API_KEY from environment
SITE_ACCESS_CODE = os.environ.get("SITE_ACCESS_CODE")  # optional gate


def load_prompt(agent_num: int) -> str:
    return (PROMPTS_DIR / f"agent{agent_num}.txt").read_text()


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _parse_json_with_retry(raw_text: str) -> dict:
    text = _strip_fences(raw_text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fix_response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": "Return ONLY valid JSON. No markdown fences, no preamble, no explanation. Fix the formatting error in the input below and return corrected JSON only."},
            {"role": "user", "content": raw_text},
        ],
    )
    fixed_text = _strip_fences(fix_response.choices[0].message.content.strip())
    return json.loads(fixed_text)  # let this raise if it still fails -- caller handles it


def call_agent(agent_num: int, user_message: str) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": load_prompt(agent_num)},
            {"role": "user", "content": user_message},
        ],
    )
    raw_text = response.choices[0].message.content.strip()
    return _parse_json_with_retry(raw_text)


def run_pipeline(requirement: str, schema: str) -> dict:
    """Runs all 6 agents in sequence. Returns a dict with the final
    deliverable plus per-agent status, so the frontend can show progress."""
    steps = []

    def log(agent_num, label, status):
        steps.append({"agent": agent_num, "label": label, "status": status})

    log(1, "Requirements & Schema Analyzer", "running")
    agent1_out = call_agent(1, f"Business requirement:\n{requirement}\n\nSchema:\n{schema}")
    log(1, "Requirements & Schema Analyzer", "done")

    log(2, "Architecture & KPI Framework Designer", "running")
    agent2_out = call_agent(2, json.dumps(agent1_out, indent=2))
    log(2, "Architecture & KPI Framework Designer", "done")

    log(3, "Dashboard Designer", "running")
    agent3_out = call_agent(3, json.dumps(agent2_out, indent=2))
    log(3, "Dashboard Designer", "done")

    log(4, "Query Generator", "running")
    agent4_input = (
        f"architecture_and_kpi_output:\n{json.dumps(agent2_out, indent=2)}\n\n"
        f"dashboard_output:\n{json.dumps(agent3_out, indent=2)}\n\n"
        f"schema:\n{schema}"
    )
    agent4_out = call_agent(4, agent4_input)
    log(4, "Query Generator", "done")

    log(5, "Critic / Validator", "running")
    agent5_input = (
        f"schema:\n{schema}\n\n"
        f"architecture_and_kpi_output:\n{json.dumps(agent2_out, indent=2)}\n\n"
        f"dashboard_output:\n{json.dumps(agent3_out, indent=2)}\n\n"
        f"query_generator_output:\n{json.dumps(agent4_out, indent=2)}"
    )
    agent5_out = call_agent(5, agent5_input)
    log(5, "Critic / Validator", "done")

    log(6, "Documentation Generator", "running")
    agent6_input = (
        f"agent1_output:\n{json.dumps(agent1_out, indent=2)}\n\n"
        f"agent2_output:\n{json.dumps(agent2_out, indent=2)}\n\n"
        f"agent3_output:\n{json.dumps(agent3_out, indent=2)}\n\n"
        f"agent4_output:\n{json.dumps(agent4_out, indent=2)}\n\n"
        f"agent5_output:\n{json.dumps(agent5_out, indent=2)}"
    )
    agent6_out = call_agent(6, agent6_input)
    log(6, "Documentation Generator", "done")

    return {
        "steps": steps,
        "deliverable_markdown": agent6_out.get("deliverable_markdown", ""),
        "validation_status_summary": agent6_out.get("validation_status_summary", ""),
    }


@app.route("/")
def index():
    return render_template("index.html", access_code_required=bool(SITE_ACCESS_CODE))


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    if SITE_ACCESS_CODE:
        if data.get("access_code") != SITE_ACCESS_CODE:
            return jsonify({"error": "Incorrect access code."}), 403

    requirement = (data.get("requirement") or "").strip()
    schema = (data.get("schema") or "").strip()

    if not requirement or not schema:
        return jsonify({"error": "Both a business requirement and a schema are required."}), 400

    try:
        result = run_pipeline(requirement, schema)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Pipeline failed: {e}"}), 500


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: Set OPENAI_API_KEY before running.")
        raise SystemExit(1)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
