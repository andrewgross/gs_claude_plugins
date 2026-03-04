# Terminal Notifier Plugin

Native macOS notifications when Claude Code finishes responding. Clicking the notification brings your terminal to focus.

## Prerequisites

- macOS
- [uv](https://docs.astral.sh/uv/) (for inline script dependencies)
- `terminal-notifier` binary — on macOS Sonoma+ you may need to [build from source with patch](https://github.com/julienXX/terminal-notifier/pull/313) since Homebrew's version can fail silently

## Installation

```bash
# Add the marketplace
/plugin marketplace add /path/to/gs_claude_plugins

# Install the plugin
/plugin install terminal-notifier@gs-claude-plugins
```

## Configuration

On first run, a config file is created at `~/.claude_code_notification_config.json`:

```json
{
  "enabled": true,
  "sound": "default",
  "title": "Claude Code",
  "subtitle": "Task Complete",
  "activate": "auto"
}
```

| Option | Description |
|--------|-------------|
| `enabled` | Toggle notifications on/off |
| `sound` | macOS sound name, or `"none"` to disable |
| `title` | Notification title |
| `subtitle` | Notification subtitle |
| `activate` | Terminal app to focus on click: `"auto"` (detect), `"com.mitchellh.ghostty"`, `"com.googlecode.iterm2"`, `"com.apple.Terminal"` |

## Troubleshooting

- **No notifications appear**: Ensure `terminal-notifier` is installed and working (`terminal-notifier -message test`). On Sonoma+, the Homebrew version may need to be replaced with a source build.
- **Clicking notification doesn't focus terminal**: Set `activate` in the config to your terminal's bundle ID instead of `"auto"`.
- **pync import error**: Make sure `uv` is installed and on your PATH.
