---
name: retcon
description: Predestination for conversations. Writes the replacement message for an earlier point in the chat so rewinding drops the transcript without losing world state, insights, or decisions from the future.
argument-hint: "[target message, and optionally where to steer next]"
disable-model-invocation: true
license: BEERWARE-MIT (github.com/Syncriix/skills)
---

# Retcon

Rewinding a conversation snaps the agent's context back to an earlier message `T` (`Pre-T` stays verbatim; `T..Now` vanishes), while **the outside world** and **the user's mind** stay at `Now`. Write the message the user will paste at `T` so the `T`-agent has every fact, insight, and constraint from `T..Now` that matters for continuing from `T`, with none of the dead ends or transcript noise it took to get them.

## 1. Three Response Modes (The `/copy` Contract)

When the retcon is ready, the user copies your entire reply with `/copy`. Your reply must be **either** pre-copy clarification (Modes 1–2) **or** the raw pasteable retcon (Mode 3)—never mix commentary with paste text, and never wrap Mode 3 in preambles, outer quotes, or code fences:

1. **Target picker** *(when `T` is unspecified and multiple cut points are plausible)*: Emit a numbered list of the candidate messages from the chat, quoting each candidate's opening words and what rewinding there keeps vs. cuts.
2. **Clarifying questions** *(when intent, scope, or unresolved state in `T..Now` blocks the retcon—e.g. whether an explored approach was accepted or ruled out, how to treat leftover disk edits, or where to steer)*: Ask short, direct questions covering only what is ambiguous (combining with the target picker if both `T` and scope are unclear).
3. **Pasteable retcon** *(when `T` and the carry-back are clear, or on the turn immediately after the user answers Mode 1 or 2)*: Start with the very first character of the paste text—zero conversational acknowledgement (*never "Got it, here's #2:"*).

## 2. Addressee, Horizon & Self-Identification

- **Absorb `Now`-banter silently:** Everything in the `/retcon` invocation is a backstage note to you at `Now`. When the user includes banter, praise, complaints, or meta-notes in the call, never answer or echo them inside the retcon—doing so leaks ghost references to deleted turns. Every word of Mode 3 is spoken at `T` to the agent at `T`.
- **Tell the `T`-agent this is its own `/retcon` output:** Because this skill is user-invoked, the `T`-agent does not see `retcon` in its system prompt and does not know a rewind occurred unless told. Open the carried-back state block with a self-identifying header:
  `[retcon — rewound from a later turn; treat the state, insights, and decisions below as already settled with you:]`
  This tells the `T`-agent why future artifacts and decisions already exist, stops it from re-litigating settled calls, and gives stale-file warnings immediate authority.
- **Cold-read horizon:** Never summarize `Pre-T` (the `T`-agent still has it). Every file, SHA, decision, or concept from `Post-T` must make sense cold to an agent whose memory stops at `T`.
- **Transcript first:** `T` is a message in this conversation, never a git branch or session-tree node on disk. Use read-only tools only when live external state (such as out-of-band file edits) is uncertain from the transcript. Never mutate state.

## 3. Resolving `T` & Composable Modes

**Geometry of `T`:**
- *User `T` (detour opener):* Rescue any surviving opening reaction to `T-1` (e.g. `"good review!"`) as the **landmark** on line 1 so the user can spot which message to replace in `/rewind`, then follow with the `[retcon — ...]` block.
- *User `T` (main ask):* Rewrite or augment `T` directly.
- *User `T` (existing hub retcon):* `T` already holds a `[retcon — ...]` block from earlier passes—merge and accumulate; never drop prior passes recorded in `T`.
- *Assistant `T`:* Rewind lands in an empty prompt after `T`; write the next user turn directly.

**Composable modes across `T..Now`** (carry back only what serves the thread continuing from `T`; explicit user directives in the argument override inferred filtering and steering):
- **Detour prune** *(branched off `A` to do `B`, returning to `A`)*: Carry only world changes, stale-read warnings, and insights from `B` that touch `A`. Leave orthogonal work in `B` out completely.
- **Phase squash** *(`T..Now` completed a phase of main-thread work)*: `T`'s original ask is now done—do not re-ask it. Collapse the back-and-forth into settled decisions, governing reasons, created artifacts, and what remains open.
- **Sharpened retry** *(`T..Now` exposed why `T`'s ask or approach failed)*: Fold the discovered constraints and framing straight into a clean rewrite of prompt `T` without narrating the failed run—adding a `[retcon — ...]` warning only if leftover disk changes from the aborted run still sit on disk.
- **Hub & spoke** *(returning to a multi-item save point `T`)*: Keep completed spokes already recorded in `T`, add the spoke just finished plus any shared-file mutations, and advance steering to the next spoke.
- **Insight harvest** *(thinking, research, or plan shift with few or no disk edits)*: Carry the reframing, changed plan, and **anti-relitigation anchor**—what was ruled out and the decisive reason why, so the `T`-agent does not re-propose dead paths.

## 4. State Polarity

Never lump all `Post-T` disk activity together; state each by its actual status at `Now`:

1. **Accepted state:** Completed work and decisions that stand → state as fact with exact paths, SHAs, numbers, URLs, and names.
2. **Stale `Pre-T` state:** Files `Pre-T` read or assumptions `Pre-T` made that `Post-T` changed → plant an explicit invalidation (`re-read <path> before editing`, updated value).
3. **Leftover / superseded state:** Files or commits written during a discarded attempt in `T..Now` that still sit on disk → warn the `T`-agent that they exist on disk and must be overwritten or reverted.

## 5. Voice & Two-Zone Layout

- **Plain human prompt sentences:** Write in first person as the user typing a prompt—short, direct sentences and flat bullets when listing multiple items. Watch for the LLM reflex to write polished, multi-clause synthesis paragraphs with the user's slang glued on top; strip the essay transitions and state the points plainly. Keep all identifiers, paths, hashes, and numbers exact.
- **Two-zone layout (Context above, Gate-locked Steering below):**
  1. **Context block:** Surviving opening landmark from `T` (if any), then the `[retcon — ...]` block holding synced state, insights, and invalidations. *(In a clean-disk Sharpened retry, the rewritten prompt is the entire message.)*
  2. **Blank line + Steering line:** One standalone instruction on the final line so the user can edit or delete it in a single keystroke. Lock this line to the **exact decision or review gate `T` is paused at** (e.g. reviewing a design, answering an open question, or starting the next spoke)—never fast-forward to final execution unless the user's `/retcon` call explicitly asked to skip the gate. If the next step is genuinely open, omit the steering line and end after the context block.
