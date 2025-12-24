
Phase 2: Session Hygiene (Medium Utility)

Focus: preventing data loss and managing clutter.

Auto-save sessions (Feature #5)

Critique: Naming files untitled1, untitledN creates a "drawer of junk" that is hard to sort through later.
Improvement:
Auto-save on every message: Don't wait for a command. Save to a temp file or the active session file after every turn to prevent data loss on crash.
Naming: Stick to the current timestamp-based naming (session_2025...) as the default "untitled" state. It sorts chronologically automatically.
Session Management Commands (Feature #6)

Critique: "Pruning" can be dangerous if not specific.
Improvement: Implement:
/delete [name]: Delete specific session.
/delete --all: Delete all (with confirmation).
/prune [days]: Delete sessions older than X days.
Phase 3: Intelligent Context (High Value / Higher Cost)
Focus: Leveraging AI to organize data.

Summarize session topic on save (Feature #3)
Critique: This requires an extra API call to OpenAI, which adds latency and cost every time you save.
Improvement:
Async/Background: Don't block the UI while generating the summary.
Trigger: Generate the summary only when the session is first saved or when it reaches a certain length, not on every minor update.
Storage: Save this summary in the JSON file so it doesn't need to be regenerated when listing /history.