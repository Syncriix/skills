# skills

Agent skills I use every day and share with friends. Built for laziness that
pays off: anything I'd otherwise explain to an agent for the third time becomes
a skill. Written for agents that know nothing about me, so they work in any
harness.

## What's in here

| Folder | What |
|---|---|
| `skills/matt/` | A curated, edited cut of [Matt Pocock's skills](https://github.com/mattpocock/skills). Sharp, code-centric, MIT, his licence sits in every folder. Kept in sync with his upstream, see below. |

Every skill is a plain [Agent Skills](https://agentskills.io/specification)
folder: a `SKILL.md` with `name` and `description`, plus whatever it reads or runs.

## Install

**omp**

```
/marketplace add Syncriix/skills
/marketplace install syncriix-skills@syncriix-skills
```

**Claude Code**

```
/plugin marketplace add Syncriix/skills
/plugin install syncriix-skills@syncriix-skills
```

**Anything else**: clone the repo and symlink the skill folders you want into
your agent's skills folder (`~/.claude/skills/`, `~/.agents/skills/`, ...).
Skills are found one level deep, so link the skill folder itself, not its group.

If you have Matt's plugin installed too, uninstall it: the same names would load twice.

## Maintaining

`scripts/skills.py` keeps the repo honest. Python 3.9+ and git, nothing else.

```
scripts/skills.py check                    # manifest, frontmatter, vendor.json agree
scripts/skills.py vendor sync              # merge upstream changes into the vendored copies
scripts/skills.py vendor add matt skills/engineering/tdd
scripts/skills.py vendor remove matt tdd
```

Vendored skills are ordinary files: edit them freely. `sync` merges each
skill's upstream changes since its pinned commit into your edited copy;
where both sides changed the same lines you get normal conflict markers. It
follows skills that moved upstream and lists new ones without importing them.
`add` and `remove` keep `.claude-plugin/plugin.json` in step; `check` fails
when a skill folder and the manifest disagree.

## Licence

[BEERWARE-MIT](LICENSE): do whatever you want, keep the notice, buy me a beer if
we meet and you think it was worth it. The skills in `skills/matt/` stay under
Matt Pocock's MIT licence.
