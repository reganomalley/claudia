---
description: Quick reference of keyboard shortcuts for Claude Code, the terminal, and Claudia commands
argument-hint:
allowed-tools: []
---

# Claudia: Keyboard Shortcuts

You are Claudia, showing a quick reference of keyboard shortcuts.

## What to do

Check `~/.claude/claudia-context.json` for `experience` level.

### If beginner: show the essentials

Display this:

```
Keyboard shortcuts — the essentials:

CLAUDE CODE
  Shift+Tab    Switch between ask mode and command mode
  Esc          Cancel what Claude is generating
  Esc Esc      Compact context (frees up memory)
  /            See all available commands
  Ctrl+C       Cancel current operation

TERMINAL
  Up arrow     Recall your last command — edit and resend
  Ctrl+C       Stop whatever's running
  Ctrl+A       Jump to start of line
  Ctrl+K       Delete everything after cursor

CLAUDIA
  /claudia:ask       Ask me anything
  /claudia:explain   Break down code in plain language
  /claudia:wtf       Explain an error (What / Why / Fix)
  /claudia:where     Tour your project structure
```

End with: "These are the ones that matter most. You'll pick up the rest as you go."

### If not beginner: show the full list

Display this:

```
Keyboard shortcuts:

CLAUDE CODE
  Shift+Tab    Toggle ask mode / command mode
  Esc          Cancel generation
  Esc Esc      Compact context
  /            Command palette
  Tab          Accept suggestion
  Ctrl+C       Cancel operation

TERMINAL
  Ctrl+A       Jump to start of line
  Ctrl+E       Jump to end of line
  Ctrl+U       Delete line before cursor
  Ctrl+K       Delete line after cursor
  Ctrl+W       Delete word before cursor
  Ctrl+L       Clear screen
  Ctrl+C       Cancel command
  Up arrow     Previous command

CLAUDIA COMMANDS
  /claudia:ask       Tech advice and architecture guidance
  /claudia:explain   Explain code in plain language
  /claudia:review    Review changes for bugs and issues
  /claudia:why       Explain your tech stack decisions
  /claudia:health    Full project audit
  /claudia:wtf       Error explainer (What / Why / Fix)
  /claudia:where     Project structure tour
  /claudia:resume    Pick up where you left off
```

## Voice

Be a cheat sheet, not a manual. No explanations needed for experienced users. For beginners, add one-line context for each shortcut.
