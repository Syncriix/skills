#!/usr/bin/env python3
"""Validate this skills repo and vendor skills from upstream repos.

  skills.py check
  skills.py vendor init SOURCE URL --dest DIR [--ref REF] [--commit SHA] [--license PATH]
  skills.py vendor add SOURCE UPSTREAM_PATH...
  skills.py vendor remove SOURCE NAME...
  skills.py vendor sync [SOURCE...]

A vendored skill is a plain copy you own and edit. `sync` merges the upstream
changes since each skill's pinned commit into your copy with `git apply --3way`;
where you and upstream changed the same lines, you get ordinary conflict
markers. It follows a skill that moved to another upstream folder, and lists
skills upstream added since the last sync. State lives in vendor.json; every
skill folder must be listed in .claude-plugin/plugin.json.

Needs Python 3.9+ and git; stdlib only.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
LOCK = ROOT / "vendor.json"
SKILLS = ROOT / "skills"
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class Fail(Exception):
    pass


def git(*args, stdin=None, check=True):
    """Run git in the repo root; bytes in, bytes out."""
    result = subprocess.run(["git", "-C", str(ROOT), *args], input=stdin, capture_output=True)
    if check and result.returncode:
        raise Fail(f"git {' '.join(args)}: {result.stderr.decode().strip()}")
    return result


def out(*args):
    return git(*args).stdout.decode().strip()


def load(path, default=None):
    if not path.exists():
        if default is not None:
            return default
        raise Fail(f"missing {rel(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def manifest_entry(path):
    return "./" + rel(path)


def frontmatter(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise Fail(f"{rel(path)}: no frontmatter")
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        raise Fail(f"{rel(path)}: unterminated frontmatter")
    fields, key = {}, None
    for line in lines[1:end]:
        match = re.match(r"([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match and not line[:1].isspace():
            key, value = match[1], match[2].strip()
            fields[key] = "" if value in (">", "|", ">-", "|-") else value.strip("\"'")
        elif key and line.strip():
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def skill_dirs():
    """Every folder under skills/ that holds a SKILL.md; skill folders are not searched further."""
    found = []

    def walk(folder):
        if (folder / "SKILL.md").is_file():
            found.append(folder.resolve())
            return
        for child in sorted(p for p in folder.iterdir() if p.is_dir()):
            walk(child)

    if SKILLS.is_dir():
        walk(SKILLS)
    return found


def check(_args=None):
    problems = []
    manifest = load(MANIFEST)
    listed = {(ROOT / entry).resolve(): entry for entry in manifest.get("skills", [])}
    dirs = skill_dirs()
    for folder in dirs:
        if folder not in listed:
            problems.append(f"{rel(folder)}: not listed in plugin.json")
    for path, entry in listed.items():
        if path not in dirs:
            problems.append(f"plugin.json lists {entry}, which holds no SKILL.md")
    names = {}
    for folder in dirs:
        try:
            fields = frontmatter(folder / "SKILL.md")
        except Fail as exc:
            problems.append(str(exc))
            continue
        name, description = fields.get("name", ""), fields.get("description", "")
        where = rel(folder)
        if name != folder.name:
            problems.append(f"{where}: name '{name}' must equal the folder name")
        if not NAME.fullmatch(name) or len(name) > 64:
            problems.append(f"{where}: name '{name}' must be lowercase letters, digits and single hyphens, max 64")
        if not description:
            problems.append(f"{where}: description missing")
        elif len(description) > 1024:
            problems.append(f"{where}: description is {len(description)} characters, max 1024")
        if name in names:
            problems.append(f"{where}: name '{name}' already used by {names[name]}")
        names[name] = where
    plugins = [p.get("name") for p in load(MARKETPLACE).get("plugins", [])]
    if manifest.get("name") not in plugins:
        problems.append(f"marketplace.json does not list plugin '{manifest.get('name')}'")
    for source, cfg in load(LOCK, {}).items():
        for name in cfg["skills"]:
            folder = (ROOT / cfg["dest"] / name).resolve()
            if folder not in dirs or folder not in listed:
                problems.append(f"vendor.json: {source}/{name} has no listed skill folder at {cfg['dest']}/{name}")
    for problem in problems:
        print(problem)
    print(f"{len(dirs)} skills, {len(problems)} problems")
    return 1 if problems else 0


def fetch(source, cfg):
    git("fetch", "--quiet", "--no-tags", cfg["url"], f"+{cfg['ref']}:refs/vendor/{source}")
    return out("rev-parse", f"refs/vendor/{source}")


def has_object(spec):
    return git("cat-file", "-e", spec, check=False).returncode == 0


def upstream_skills(commit):
    names = out("ls-tree", "-r", "--name-only", commit).splitlines()
    return {str(PurePosixPath(n).parent) for n in names if PurePosixPath(n).name == "SKILL.md"}


def source_cfg(lock, source):
    if source not in lock:
        raise Fail(f"unknown source '{source}'; run `vendor init` first")
    return lock[source]


def vendor_init(args):
    lock = load(LOCK, {})
    if args.source in lock:
        raise Fail(f"source '{args.source}' already exists")
    cfg = {"url": args.url, "ref": args.ref, "dest": args.dest, "license": args.license,
           "synced": None, "skills": {}}
    head = fetch(args.source, cfg)
    commit = out("rev-parse", "--verify", f"{args.commit}^{{commit}}") if args.commit else head
    cfg["synced"] = commit
    lock[args.source] = cfg
    save(LOCK, lock)
    print(f"{args.source}: {args.url} pinned at {commit[:12]}")
    return 0


def write_tree(commit, upstream, dest):
    entries = git("ls-tree", "-r", "-z", f"{commit}:{upstream}").stdout.decode().split("\0")
    for entry in filter(None, entries):
        meta, path = entry.split("\t", 1)
        mode, kind, sha = meta.split()
        if kind != "blob":
            continue
        target = dest / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git("cat-file", "blob", sha).stdout)
        if mode == "100755":
            target.chmod(0o755)


def write_license(cfg, commit, dest):
    if cfg.get("license") and has_object(f"{commit}:{cfg['license']}"):
        (dest / "LICENSE").write_bytes(git("show", f"{commit}:{cfg['license']}").stdout)


def vendor_add(args):
    lock = load(LOCK, {})
    cfg = source_cfg(lock, args.source)
    commit = cfg["synced"]
    if not has_object(commit):
        fetch(args.source, cfg)
    manifest = load(MANIFEST)
    for upstream in args.paths:
        upstream = upstream.strip("/")
        name = PurePosixPath(upstream).name
        dest = ROOT / cfg["dest"] / name
        if name in cfg["skills"] or dest.exists():
            raise Fail(f"{cfg['dest']}/{name} already exists")
        if not has_object(f"{commit}:{upstream}/SKILL.md"):
            raise Fail(f"{upstream} has no SKILL.md at {commit[:12]}")
        write_tree(commit, upstream, dest)
        write_license(cfg, commit, dest)
        cfg["skills"][name] = {"path": upstream, "commit": commit}
        manifest.setdefault("skills", []).append(manifest_entry(dest))
        print(f"added {cfg['dest']}/{name} from {upstream} at {commit[:12]}")
    save(LOCK, lock)
    save(MANIFEST, manifest)
    return 0


def vendor_remove(args):
    lock = load(LOCK, {})
    cfg = source_cfg(lock, args.source)
    manifest = load(MANIFEST)
    for name in args.names:
        if name not in cfg["skills"]:
            raise Fail(f"{args.source} has no vendored skill '{name}'")
        del cfg["skills"][name]
        dest = ROOT / cfg["dest"] / name
        entry = manifest_entry(dest)
        manifest["skills"] = [e for e in manifest.get("skills", []) if e != entry]
        shutil.rmtree(dest, ignore_errors=True)
        print(f"removed {cfg['dest']}/{name}")
    save(LOCK, lock)
    save(MANIFEST, manifest)
    return 0


def vendor_sync(args):
    lock = load(LOCK, {})
    if out("status", "--porcelain"):
        raise Fail("working tree not clean; commit or stash first, sync merges into it")
    attention = False
    for source in args.sources or list(lock):
        cfg = source_cfg(lock, source)
        head = fetch(source, cfg)
        available = upstream_skills(head)
        print(f"{source}: {cfg['synced'][:12]} -> {head[:12]}")
        for name, skill in cfg["skills"].items():
            old, path = skill["commit"], skill["path"]
            dest = f"{cfg['dest']}/{name}"
            new_path = path
            if path not in available:
                moved = [p for p in available if PurePosixPath(p).name == PurePosixPath(path).name]
                if len(moved) != 1:
                    print(f"  {name}: gone upstream ({path}); your copy stays pinned at {old[:12]}")
                    attention = True
                    continue
                new_path = moved[0]
                print(f"  {name}: moved upstream {path} -> {new_path}, following")
            patch = git("diff", "--binary", "--full-index", f"{old}:{path}", f"{head}:{new_path}").stdout
            if patch:
                result = git("apply", "--3way", f"--directory={dest}", "-", stdin=patch, check=False)
                conflicted = out("ls-files", "--unmerged", "--", dest)
                if result.returncode and not conflicted:
                    print(f"  {name}: could not apply, stays pinned at {old[:12]}\n"
                          f"    {result.stderr.decode().strip()}")
                    attention = True
                    continue
                if conflicted:
                    files = sorted({line.split("\t", 1)[1] for line in conflicted.splitlines()})
                    print(f"  {name}: merged with conflicts in {', '.join(files)}")
                    attention = True
                else:
                    print(f"  {name}: merged")
            skill["commit"], skill["path"] = head, new_path
        old_license = cfg.get("license") and has_object(f"{cfg['synced']}:{cfg['license']}") \
            and out("rev-parse", f"{cfg['synced']}:{cfg['license']}")
        new_license = cfg.get("license") and has_object(f"{head}:{cfg['license']}") \
            and out("rev-parse", f"{head}:{cfg['license']}")
        if old_license != new_license:
            for name in cfg["skills"]:
                write_license(cfg, head, ROOT / cfg["dest"] / name)
            print(f"  upstream {cfg['license']} changed; rewrote it in every vendored skill")
            attention = True
        vendored = {s["path"] for s in cfg["skills"].values()}
        added = sorted(available - upstream_skills(cfg["synced"]) - vendored)
        for path in added:
            print(f"  new upstream: {path}  (vendor add {source} {path})")
        cfg["synced"] = head
    save(LOCK, lock)
    print("review with `git diff --cached` and `git diff`, resolve conflicts, run `check`, commit")
    return 1 if attention else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="validate manifest, frontmatter and vendor.json").set_defaults(run=check)
    vendor = commands.add_parser("vendor", help="vendor skills from upstream repos")
    actions = vendor.add_subparsers(dest="action", required=True)
    init = actions.add_parser("init", help="register an upstream repo")
    init.add_argument("source")
    init.add_argument("url")
    init.add_argument("--dest", required=True, help="folder that holds this source's skills, e.g. skills/matt")
    init.add_argument("--ref", default="main")
    init.add_argument("--commit", help="pin an older commit instead of the ref's head")
    init.add_argument("--license", default="LICENSE", help="upstream licence file copied into each skill")
    init.set_defaults(run=vendor_init)
    add = actions.add_parser("add", help="copy upstream skill folders in at the source's pin")
    add.add_argument("source")
    add.add_argument("paths", nargs="+", metavar="UPSTREAM_PATH")
    add.set_defaults(run=vendor_add)
    remove = actions.add_parser("remove", help="drop vendored skills")
    remove.add_argument("source")
    remove.add_argument("names", nargs="+", metavar="NAME")
    remove.set_defaults(run=vendor_remove)
    sync = actions.add_parser("sync", help="merge upstream changes into your copies")
    sync.add_argument("sources", nargs="*", metavar="SOURCE")
    sync.set_defaults(run=vendor_sync)
    args = parser.parse_args()
    try:
        return args.run(args)
    except Fail as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
