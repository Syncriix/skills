---
name: retcon
description: Predestination for conversations. Writes the message that replaces an earlier one after a rewind, so the past already knows what the future did. Pass the message you'll rewind to.
argument-hint: "[message to rewind to]"
disable-model-invocation: true
license: BEERWARE-MIT (github.com/Syncriix/skills)
---

# Retcon

A rewind resets the conversation, not the world. The user is about to jump back to an earlier message, the **target**, and send your reply in its place. Everything after the target leaves the context; everything done in the world since (files, code, notes, messages sent, decisions acted on) stays done.

Your reply is the **retcon**: the message that closes that gap for your **past self**, you as you were at the target. Give it what it needs for its **next move** and can't know: what was learned, decided, done or changed since. Everything else stays behind, however much work it was. Size follows the gap: three words, two sentences or ten lines.

Why the user rewinds shapes what matters:

- **An experiment**: carry the finding, not the experiment.
- **One save point, several jobs**: what this run finished, so it isn't done twice, and which job is next.
- **A side quest that changed things**: the changes the next move touches; what your past self read that is now stale gets re-read.
- **Freeing up context**: the thread's live state, compressed.

Other reasons follow the same rule.

Write it in the user's voice, as they would have sent it at the target, and keep their words for whatever of it still stands. Every name in the retcon must be one your past self knew at the target or one the retcon introduces. The next move stands alone as the last line, after a blank line, so the user can spot, edit or delete it; what was learned, decided, done or changed goes above it.

The target is a message in this conversation, found by reading back through it; there is nothing to look up. The user names it when invoking. Without a name, it is the user's last request before the detour began: the experiment, the finished job, the side quest, or the stretch of thread being cleared away. When two messages fit, ask.

## Output

The retcon or questions, never both: the user copies your whole reply.

- **Retcon**: only the text to paste, first word to last, as plain text outside any code block or quotes.
- **Questions**: when the target or the next move is unclear. Ask only what blocks the retcon.

## Examples

Target: "Now send the invoice, then draft the reminder mail."
Retcon:
> Invoice is out.
>
> Now draft the reminder mail.

Target: "Great outline. Now draft the intro for the board talk."
Since then: Q3 revenue turned out to be 4.6M, not 4.1M; the user dropped the hiring slide; a competitor spreadsheet got built.
Retcon:
> Great outline. Meanwhile: Q3 revenue is 4.6M, not 4.1M, and the hiring slide is out.
>
> Now draft the intro for the board talk.

The spreadsheet stays behind: the intro doesn't touch it.
