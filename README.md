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
ui:                          # optional web UI
  entry: ui/index.html       # must live under ui/
  title: My Plugin
  slots:
    - project.page
```

Required fields: `apiVersion`, `name`, `version`, `entrypoint`, `events`.
Unknown event names, permissions, API versions, absolute entrypoints, and
entrypoints escaping the plugin directory are rejected. Optional `ui.entry`
must exist under `ui/`; unknown `ui.slots` are rejected.

### Web UI

A plugin can ship a web page and mount it into host slots. Remove the
`ui` block if the plugin is lifecycle-only.

| Slot | Where |
|---|---|
| `project.header` | Project page, under the title row |
| `project.page` | Project page, below the board |
| `project.toolbar` | Compact slot at the end of the project action row (host starts at 150×28) |
| `issue.actions` | Issue page, under the header |
| `issue.page` | Issue page, at the bottom |
| `issue.toolbar` | Compact slot at the end of Issue actions (host starts at 150×28) |

Open the standalone page at `/plugins/<plugin-id>`. In xIssue, plugins are
trusted operator-installed extensions: by default the iframe is same-origin
and can use `parent.document` and `/api/*`. Settings → General →
**插件 UI 沙盒模式** enables a same-origin-blocking sandbox for less trusted
plugins; then only the `postMessage` bridge works.

Bridge messages:

| Direction | Message |
|---|---|
| plugin → host | `{type:"xissue:ready"}` |
| host → plugin | `{type:"xissue:context", slot, modal, context}` |
| plugin → host | `{type:"xissue:notify", kind:"info"\|"success"\|"error", message}` |
| plugin → host | `{type:"xissue:open", path:"/issues/1"}` |
| plugin → host | `{type:"xissue:reload"}` |
| plugin → host | `{type:"xissue:resize", height?: 320, width?: 180}` |
| plugin → host | `{type:"xissue:open-modal", title:"Merge note", height:480}` |
| plugin → host | `{type:"xissue:close-modal"}` |
| plugin → host | `{type:"xissue:ai", requestId:"1", prompt:"…", agent?, model?}` |
| host → plugin | `{type:"xissue:ai-result", requestId:"1", data?, error?}` |

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

Issue payloads now also carry the host's current metadata:

| Field | Meaning |
|---|---|
| `priority` | `low` / `normal` / `high` / `urgent` |
| `labels` | Label names, including labels selected in the Issue UI |
| `parentIssueId` | Parent task id for sub-issues (`null` for top-level issues) |
| `backlogRank` | Manual Backlog order within the project |
| `remoteNumber` / `remoteUrl` | Bound remote Issue id and URL |
| `prUrl` / `prState` | Latest associated PR and its state |

A toolbar slot starts at 150×28; it is not required to fill that box. Render
the button at the width you need and send `{type:"xissue:resize", width: 180}`
if it should be wider (60–800px). Use `xissue:open-modal` to ask the host to
open the same UI in a modal; the modal instance receives `modal:true` in its
context and can render the full panel.

### Using the host AI agent

Do not scan `/api/agents` or spawn CLIs yourself. The host exposes the default
agent in two ways:

```js
// Trusted (non-sandbox) iframe:
const info = await fetch('/api/plugins/ai').then(r => r.json());
const res = await fetch('/api/plugins/ai', {
  method: 'POST',
  headers: {'Content-Type': 'application/json', 'X-XIssue': '1'},
  body: JSON.stringify({prompt: 'Summarize this issue: ...'}),
}).then(r => r.json());
console.log(res.text);
```

Sandboxed iframes use the bridge:

```js
parent.postMessage({type:'xissue:ai', requestId:'1', prompt:'Summarize...'}, '*');
window.addEventListener('message', (e) => {
  if (e.data?.type === 'xissue:ai-result' && e.data.requestId === '1') {
    console.log(e.data.data?.text ?? e.data.error);
  }
});
```

`agent` and `model` are optional; omit them to use the global default and its
default model. Calls run in a throwaway workspace with all tool permissions
rejected: the agent can generate text, but cannot read files or run commands.

Plugins can also call the host API from their UI. In the default trusted mode
the iframe is same-origin, so `fetch('/api/issues/<id>')` works. When the global
sandbox is enabled, use the `postMessage` bridge or implement a backend plugin
script instead.

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
| `create_issue`, `trigger_run`, `merge_pr` | `branch_push`, `pr_comment`, `pr_review` only |
| `pull_local`, `set_issue_status` | `branch_push`, `pr_comment`, `pr_review`, `pr_merged` |

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
