# AI Decision Room — V2.1 UI Merge Artifact

## Objective
Merge the streaming typewriter debate theater design into `app.py`, replacing the old ROOM_HTML with a Linear-tier UI featuring:
- Streaming typewriter effect (each AI speaks in sequence, character by character)
- 7 AI agents with avatar/name/title/stance tags
- Conflict visualization bars with severity percentage
- Structured CEO decision card
- Remaining daily counter + ad unlock mechanism

## What Changed
- **app.py**: Replaced entire `ROOM_HTML` (~29,700 chars old → ~19,400 chars new)
- Merged streaming `playDebateFlow()` function with typewriter animation
- Adapted to 7 agents (V1.2 format) while keeping BOARD mapping for icons/titles
- Preserved: Linear dark theme, Inter font, remaining counter, ad unlock, mock fallback
- Backend engine (V1.2 conflict clustering + CEO verdict) untouched

## Key Design Decisions
- Typewriter speed: 20ms per character (fast enough to feel alive, slow enough to read)
- Each agent gets 300ms pause between speeches
- Mock data matches 7-agent V1.2 backend format so API replacement is seamless
- `fallback()` catches network errors → runs mock instead of breaking UI

## Commit
`3b7291f` — V2.1 UI: stream debate theater with typewriter effect + 7-agent flow + conflict bars + remaining counter

## Status
- Python syntax: ✅ OK
- Push: ⚠️ blocked (GitHub credential helper path mismatch — needs manual `git push`)
