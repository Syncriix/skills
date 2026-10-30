---
name: retcon
description: Predestination for conversations. Writes the replacement message for an earlier point in the chat so rewinding drops the transcript without losing insights, changed plans, or state from the future.
argument-hint: "[target message, and optionally where to steer next]"
disable-model-invocation: true
license: BEERWARE-MIT (github.com/Syncriix/skills)
---

# Retcon

Rewinding snaps the agent's context back to an earlier message `T` (`T..Now` vanishes from chat), while the user's mind and the outside world stay at `Now`. Write the message the user will paste at `T` so the conversation continues from that point with the benefit of hindsight.

Carry back only what is **still live** for the conversation from `T` onward—insights, reframings, changed plans, ruled-out paths (and why), work from a side quest that is now done so it isn't repeated, or things that changed behind the `T`-agent's back (like a file it already read and needs to re-read)—or simply rewrite `T`'s ask itself when the excursion was figuring out what to ask. Leave out dead ends, process narration, and internals of finished side work that don't affect `T`'s thread.

## Response modes (`/copy` contract)

The user copies your entire reply with `/copy`. Emit **only one** of these—never mix commentary with paste text, and never wrap Mode 3 in preambles, acks, quotes, or code fences:

1. **Candidate picker** *(when `T` wasn't specified and multiple earlier rewind points are plausible)*: A numbered list of the candidate messages in this conversation, quoting each one's opening words and what rewinding there keeps vs. drops.
2. **Clarifying questions** *(when what to keep, drop, or steer toward is unclear)*: Short, direct questions on only what blocks the retcon.
3. **Pasteable retcon** *(when `T` and the carry-back are clear, or immediately after the user answers Mode 1 or 2)*: Raw paste text starting at character 1.

## Writing the retcon

- **Speak at `T`, not `Now`:** Write in first person in the user's natural voice. Treat the `/retcon` call itself (and any banter or meta-notes in it) as a backstage note to you now—never reply to it inside the message meant for `T`.
- **Landmark & `[retcon]` tag:** When replacing a user message `T` whose opening reaction to `T-1` still holds, start with those exact words so the user can spot `T` in `/rewind`. Prefix carried-back future context with `[retcon]` so the rewound agent recognizes its own skill output and treats the state, insights, and stale-read warnings as settled ground truth.
- **Scale & layout:** Default to a compact micro-paragraph in natural prose (use bullets only when handing back an actual list), scaled from a few words to a full block as the gap demands. If there is a clear next instruction at `T` (respecting whatever review or decision gate `T` was paused at), put it **on its own final line after a blank line** so the user can easily edit or delete it; if the next direction is open, omit it.
