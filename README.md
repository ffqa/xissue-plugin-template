# xIssue Plugin Template

Template for building an [xIssue](https://github.com/ffqa/xissue) plugin.

Use this repository as a GitHub template, rename the plugin, then publish it to
your own repository or submit it to [xissue-plugins](https://github.com/ffqa/xissue-plugins).

## Quick start

```bash
git clone https://github.com/ffqa/xissue-plugin-template my-plugin
cd my-plugin
python3 scripts/validate_manifest.py .
printf '%s' "$(cat fixtures/issue_created.json)" | ./run.py
```

Rename `my-plugin` in `plugin.yaml`, set `entrypoint`, `events`, and
`permissions`, then implement `build_actions()` in `run.py`.

Install into a running xIssue:

```bash
xissue plugin install your-github-user/my-plugin
xissue plugin list
xissue plugin disable my-plugin
```

For local development:

```bash
xissue plugin check .
mkdir -p ~/.xissue/plugins
ln -s "$PWD" ~/.xissue/plugins/my-plugin
```

## Contract v1

`plugin.yaml` is validated before a plugin is executed. An invalid manifest is
listed with an error and remains disabled.

```yaml
apiVersion: 1
name: my-plugin              # lowercase id, used as the install directory
version: 0.1.0
description: one sentence
author: your-name
entrypoint: run.py           # relative path inside the plugin directory
events:
  - issue_created
permissions:
  - notify                   # informational, not a sandbox
```

Required fields: `apiVersion`, `name`, `version`, `entrypoint`, `events`.
Unknown event names, permissions, API versions, absolute entrypoints, and
entrypoints escaping the plugin directory are rejected.

### Events

| Event | When |
|---|---|
| `branch_push` | A monitored branch receives commits |
| `pr_created` | xIssue creates a pull request |
| `pr_comment` | A PR receives a comment/report |
| `pr_review` | A PR receives a review |
| `pr_merged` | A PR is merged |
| `notification_dispatch` | xIssue sends an in-app notification |
| `issue_created` | A local or remote issue is created |
| `issue_status_changed` | Issue status changes |
| `run_started` | An agent run starts |
| `run_finished` | A run completes, fails, or is cancelled |
| `all` / `*` | Subscribe to every event |

### Input

One JSON object is written to stdin. See `fixtures/` for complete examples.

```json
{
  "event": "run_finished",
  "timestamp": "2026-01-01T00:10:00Z",
  "project": { "id": 1, "name": "demo", "targetBranch": "main" },
  "repo": { "id": 3, "name": "web", "provider": "github" },
  "issue": { "id": 7, "key": "LOCAL-7", "status": "review" },
  "run": { "id": 42, "status": "completed" },
  "previousStatus": "todo"
}
```

Fields not relevant to an event are omitted. Event-specific fields include
`branch`, `tipSha`, `commits`, `pr`, `comment`, `review`, and `notification`.

### Output

Write a JSON object to stdout. Empty stdout means "no actions".

```json
{
  "actions": [
    { "type": "notify", "message": "Markdown supported" }
  ]
}
```

Action support depends on the event:

| Action | Supported events |
|---|---|
| `notify` | All events |
| `create_issue`, `trigger_run`, `pull_local`, `merge_pr`, `set_issue_status` | `branch_push`, `pr_comment`, `pr_review` only |

Lifecycle events (`issue_*`, `run_*`, `pr_created`, `notification_dispatch`)
ignore mutating actions to prevent recursive event loops. Other actions are
logged and skipped.

## Execution model

- Each enabled plugin runs as a subprocess with the plugin directory as cwd.
- Python files run with `python3`; JavaScript files run with `node`; other
  entrypoints run directly.
- Each invocation has a 15-second timeout. On Unix the whole process group is
  killed on timeout.
- stderr is captured in xIssue's monitor log on non-zero exit.
- Plugins run with your user's permissions. A manifest cannot restrict files,
  network, or process access. Install only code you trust.
- State should be written inside the plugin directory (for example
  `state.json`) or a directory you configure explicitly.

## Testing

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_manifest.py .
printf '%s' "$(cat fixtures/run_finished.json)" | ./run.py
```

CI validates the manifest and runs the Python, Node, and shell examples.

## Publishing

1. Keep `apiVersion: 1` and bump `version` for every release.
2. Tag releases with the same version.
3. Make the repository public.
4. Add an entry to `index.json` in `ffqa/xissue-plugins`:

```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "one sentence",
  "repo": "your-github-user/my-plugin",
  "path": "",
  "events": ["issue_created"],
  "permissions": ["notify"]
}
```

Users install with `xissue plugin install my-plugin`.

## License

MIT
