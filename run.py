#!/usr/bin/env python3
"""xIssue plugin template.

Reads one JSON event from stdin and writes optional actions to stdout.
Keep the process under 15 seconds: xIssue kills the whole process group.
"""

import json
import sys


def build_actions(payload):
    event = payload.get("event", "")
    project = (payload.get("project") or {}).get("name", "project")
    actions = []

    if event == "issue_created":
        issue = payload.get("issue") or {}
        actions.append({
            "type": "notify",
            "message": f"New issue {issue.get('key')} in {project}: {issue.get('title')}",
        })
    elif event == "run_finished":
        run = payload.get("run") or {}
        actions.append({
            "type": "notify",
            "message": f"Run #{run.get('id')} finished with status {run.get('status')} in {project}",
        })

    return actions


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception as exc:
        print(f"invalid stdin JSON: {exc}", file=sys.stderr)
        return 1
    actions = build_actions(payload)
    if actions:
        print(json.dumps({"actions": actions}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
