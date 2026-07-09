# Plan: roguelike deck-builder (pygame-ce), CC0 assets

## Context

We want a roguelike deck-building game loosely in the spirit of Slay the Spire 2:
turn-based single-character combat, a branching map through one act, cards,
relics, potions, a shop and rest sites, seeded reproducible runs, and save/resume.
The repo is a greenfield "agent workshop kit": no application code, a strict
red/green TDD pipeline (`CLAUDE.md`, `PROCESS.md`), enforcement hooks, and a
roguelike-aware `python-debt-audit` skill. Python 3.11.2 is available (`python3`
only, PEP 668, so a `.venv` is mandatory); pygame installs from a wheel that
bundles SDL2; no test or lint tooling exists yet.

The user's explicit concern is sourcing textures and other art in a way that has
no copyright or security implications. This plan therefore treats the asset
pipeline as a first-class deliverable, not an afterthought: a CC0-only policy, a
provenance manifest, and concrete download/vetting controls.

Intended outcome: a playable single-character vertical slice with real (CC0) art,
a deterministic headless-testable game core, and a project that satisfies this
repo's definition of done (full pytest suite, ruff, mypy, all green).

## Confirmed direction (from the user)

| Decision | Choice |
|---|---|
| Presentation / framework | 2D desktop, pygame-ce (the maintained community fork; imports as `pygame`) |
| First milestone | Single-character vertical slice |
| Art workflow | Source real art up front (behind an abstraction layer) |
| Licence policy | CC0 only (strictest): no CC-BY, CC-BY-SA, CC-NC, OFL, "free for non-commercial" |

## Implementation defaults taken (open to challenge at review)

- Package codename `ascent`. Do not use the "Slay the Spire" name, characters,
  card names, logo, or any of its art/audio anywhere: repo, package, or filenames.
  Trademark and copyright are separate from the CC0 asset policy and are not
  waived by it. "Loosely inspired" is a flavour brief only.
- Content defined as JSON, validated into frozen stdlib dataclasses. No pydantic
  (keep the dependency surface small).
- RNG via seeded `random.Random` streams; never module-level `random.*`.
- Save granularity: node boundaries only for the MVP (combat is atomic).
  Mid-combat resume is a documented stretch goal.
- Binaries committed directly to git, not git-lfs (git-lfs is not installed and
  `sudo` is blocked; slice assets are single-digit MB).
- Core/pygame layering enforced by a plain import-guard test (zero extra deps).

## Architecture

Three layers with a one-way dependency rule: `ui` depends on `core` and `data`;
`core` never imports pygame. That rule is the single most important invariant and
is enforced by a test, not just convention. It is also exactly what the
`python-debt-audit` skill rewards (game-loop/render separation, seedable RNG,
data-driven content, no per-entity copy-paste).

### Package layout (src layout)

```
ascent/                        # repo root
  pyproject.toml                  # deps + ruff/mypy/pytest config, entry point
  conftest.py                     # root fixtures: seeded RngGroup, loaded ContentDB
  assets/                         # vendored CC0 binaries + provenance (see below)
  src/ascent/
    __main__.py                   # `python3 -m ascent`: wire ContentDB + Game
    core/                         # HEADLESS, deterministic. MUST NOT import pygame
      ids.py                      # enums: CardType, Target, IntentKind, StatusKind, NodeType
      rng.py                      # RngGroup: named, independent, seedable streams
      entities.py                 # Combatant, PlayerCombatant, EnemyCombatant (runtime)
      statuses.py                 # status/power defs + damage modifier pipeline
      effects/primitives.py       # EffectSpec dataclasses (Damage, GainBlock, ApplyStatus, Draw...)
      effects/handlers.py         # registry: primitive -> state mutation + domain event
      effects/context.py          # EffectContext(source, target, combat, rng, card)
      events.py                   # domain event types + EventBus (trigger dispatch)
      piles.py                    # draw/hand/discard/exhaust + deterministic reshuffle
      combat.py                   # CombatState + turn/phase engine + effect-queue driver
      intents.py                  # data-driven, seeded enemy AI -> Intent
      map.py                      # seeded branching-map generation + Node/Edge
      rewards.py  shop.py         # reward generation; shop inventory + purchase rules
      run.py                      # Run aggregate (the save root)
      save.py                     # versioned to_dict/from_dict + migrations
      content/schema.py           # frozen CardDef, RelicDef, EnemyDef, PotionDef...
      content/loader.py           # JSON -> validated ContentDB
      content/registry.py         # ContentDB: id -> def + referential validate()
    data/                         # DESIGNER-EDITABLE content JSON, no code
      cards.json relics.json enemies.json potions.json characters.json maps/act1.json
    ui/                           # pygame-ce ONLY here
      game.py scene.py input.py view.py render.py assets.py theme.py
      scenes/{title,map_scene,combat_scene,reward_scene,shop_scene,rest_scene,event_scene,game_over}.py
  tests/{core,content,ui}/
```

Content JSON lives inside the package (`src/ascent/data/`, resolved via
`importlib.resources`) so path resolution is deterministic. Binary art lives in
`assets/` at the repo root and is reached only through logical keys (below).

### Domain model and the load-bearing effect pattern

Two tiers: immutable definitions loaded from data (`*Def`, frozen dataclasses) and
mutable runtime state (`Combatant`, `CombatState`, `Run`). `CombatState` is a plain
mutable dataclass; determinism comes from threading RNG explicitly, not from
immutability. The pygame layer reads a derived immutable snapshot
(`combat.to_view()`) plus a log of domain events; it never mutates core state.

Card and relic behaviour uses effect primitives (composition) plus an event bus,
not per-card subclasses and not a bespoke DSL. Cards carry a typed list of small
`EffectSpec` dataclasses (`Damage`, `GainBlock`, `ApplyStatus`, `Draw`, ...). A
bounded registry of ~15-25 handlers is the only place effects mutate state; each
handler emits a domain event, and the `EventBus` fires subscribed relics/powers
that may enqueue further effects. All damage maths (Strength, Vulnerable, Weak,
Frail, an affliction-style debuff) lives in one ordered pipeline in the Damage
handler, tested in one place. This keeps content data-driven and hand-written code
bounded and shared, which is what the audit skill checks for.

### Determinism

`RngGroup(seed)` derives named independent streams (`map`, `shuffle`, `enemy_ai`,
`card_reward`, `relic`, `potion`, `treasure`, `event`, `shop`, `monster_hp`) so
consuming randomness in one subsystem never shifts another. Stream seeds derive via
`hashlib.sha256(f"{seed}:{name}")`, never the builtin `hash()` (salted by
`PYTHONHASHSEED`). Per-combat streams re-derive from `(seed, "shuffle", encounter_index)`
so a test can build one combat in isolation with a known shuffle. Streams serialise
via `Random.getstate()/setstate()`. Never iterate a `set`/`dict` for gameplay
without sorting by a stable key; no wall-clock, `uuid4`, or `time` in `core`.

### Scenes and save

`SceneManager` owns a scene stack (`handle_event`/`update(dt)`/`render`). `Game`
owns the `Run`, the `ContentDB`, the scene manager, the clock, and the display
surface. A scene translates input into a core command, calls the core API, reads
the resulting view, and consumes new domain events to enqueue animations.

Save serialises the `Run` aggregate to JSON with a top-level integer
`save_version`: seed, per-stream RNG states, character id, hp, gold, deck as
`{def_id, upgraded, uid}`, relics with counters, potions, and the generated map.
Because saves reference content by id, a content update cannot corrupt a save
unless an id disappears, which the loader detects. Explicit `to_dict`/`from_dict`
(not `dataclasses.asdict`, which mishandles enums and RNG state); a `migrations`
registry maps `n -> n+1`; an unknown/newer version raises `SaveVersionError`.

## Asset pipeline (CC0 only)

### Sources and the traps to avoid

| Game need | CC0 source | Note |
|---|---|---|
| Card frames / backs | Kenney Playing Cards + Boardgame packs | First-party CC0 |
| ~20 card illustrations | OpenGameArt, CC0 filter, one coherent set | Verify each file |
| Ability / status / relic icons | Kenney "Game Icons" pack (CC0) | NOT game-icons.net |
| Enemy sprites (~8) | OpenGameArt, CC0 filter | Avoid CC-BY-SA LPC sets |
| Player portrait, backgrounds | Kenney or OpenGameArt (CC0 filter) | Verify licence field |
| UI (buttons, panels, bars), map-node icons | Kenney UI / RPG UI packs | CC0, matched style |
| UI font | Kenney Fonts (CC0) | OFL fonts are NOT CC0 |
| SFX | sfxr / jsfxr / bfxr (self-generated) | You own the output; cleanest provenance |
| Music (optional) | Kenney CC0 loops or self-generated | CC0 music is scarce; keep optional |

Traps that will bite, called out deliberately:
- game-icons.net is CC-BY 3.0 by default, so it is OUT despite the obvious name.
  Use the Kenney "Game Icons" CC0 pack, which is a different thing.
- OFL (most attractive game fonts, most Google Fonts) is not CC0. Prefer Kenney
  CC0 fonts. Any OFL use is a human-approved, manifest-documented exception.
- OpenGameArt is mixed-licence and assets can carry several licences at once. Take
  only files whose licence set explicitly includes CC0; avoid the CC-BY-SA/GPL LPC
  family. "Free" / "credit appreciated" wording is not CC0.

### Verification workflow (before any file is vendored)

1. Reach the first-party author page, not an aggregator repost.
2. Read the licence verbatim; accept only CC0 1.0 / public domain / no rights reserved.
3. On OpenGameArt, inspect every licence checkbox; CC0 must apply to the exact file.
4. For fonts, open the bundled licence and confirm CC0, not OFL.
5. Save proof (page text + screenshot) into `assets/licences/<source-slug>.txt`.
6. Record the asset in `assets/manifest.json` with its sha256.

### Provenance manifest (source of truth and runtime index)

`assets/manifest.json` doubles as the provenance record and the logical-key index
the game loads. Required per entry: `key`, `path`, `name`, `source_url`, `author`,
`licence` (must equal `CC0-1.0`), `retrieved`, `sha256`. Recommended: `source_pack`,
`licence_url`, `licence_proof`, `notes`.

```json
{ "schema_version": 1, "policy": "CC0-1.0-only",
  "assets": [
    { "key": "icon.status.poison", "path": "assets/icons/status/poison.png",
      "name": "Poison status icon", "source_url": "https://kenney.nl/assets/game-icons",
      "author": "Kenney", "licence": "CC0-1.0",
      "licence_proof": "assets/licences/kenney-game-icons.txt",
      "retrieved": "2026-07-09", "sha256": "..." } ] }
```

Directory layout under `assets/`: `images/{cards,card_art,backgrounds,portraits}`,
`icons/{status,relics,abilities,map}`, `ui/{buttons,panels,bars}`, `fonts/`,
`audio/{sfx,music}`, `licences/`.

### Asset abstraction (`src/ascent/ui/assets.py`)

Game code never opens a path; it asks `AssetManager` for a logical key
(`card.frame.attack`, `icon.status.poison`, `sfx.card_play`, `font.ui`). The manager
reads the manifest once, maps key to path, and lazily loads and caches pygame
objects. `image(key)`, `font(key, size)`, `sound(key)` where sound degrades to a
no-op `NullSound` if the mixer cannot init (so logic and tests never depend on audio
hardware). A missing key or file raises a clear error naming it: no silent fallback
that hides a broken swap. Swapping any asset is then a one-line manifest edit.

## Security controls for third-party assets

1. HTTPS only, host allowlist: `curl -fL --proto '=https' --tlsv1.2 -o <file> <url>`.
2. Never pipe an installer or archive to a shell (the hook blocks `curl | sh`; do
   not work around it). Always download to a file, then act on the file.
3. Stage downloads and extraction in the session scratchpad, never straight into
   `assets/`. Do not commit the downloaded archives.
4. Compute and record sha256 for every vendored file; the manifest is the pinned
   snapshot and `sha256sum -c` plus a test re-check it.
5. Inspect archives before extracting: `unzip -l` and reject any entry with a
   leading `/` or `..` (zip-slip). Extract into the isolated staging dir only.
6. Verify true file type with `file`: a PNG must report PNG, a font TrueType/OpenType.
   Reject anything that is actually a script, HTML, or executable.
7. Prefer raster PNG over SVG (SVG can embed scripts/external refs). If only SVG
   exists, rasterise offline as a deliberate human-approved step.
8. No runtime network dependency: the game reads only from `assets/` on disk, so
   there is zero supply-chain surface at play time. This is the biggest control.
9. Vendor only the individual files used, never whole packs, to keep the repo small.
10. Stage into git per file by explicit path (the hook blocks bulk `git add`), so
    only manifest-recorded files are committed.

## Project tooling

Single `pyproject.toml` as the source of truth (ruff, mypy, pytest all read it):

- Runtime dep: `pygame-ce>=2.5` (do not also install `pygame`; they conflict).
- Dev deps: `pytest>=8`, `ruff>=0.5`, `mypy>=1.10`.
- ruff lint select `E,F,W,I,N,UP,B,SIM,C4,PTH,RUF`; ruff also formats.
- mypy `strict`, with a `[[tool.mypy.overrides]]` for `pygame.*`
  (`ignore_missing_imports = true`) to absorb any stub gaps.
- pytest `addopts = "-ra -q"` with NO `-x`/`--maxfail` (the hook blocks fail-fast
  and the definition of done requires the full suite).
- Entry point `ascent = "ascent.__main__:main"`.

Bootstrap: `python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"`.

Headless tests: `tests/conftest.py` sets `SDL_VIDEODRIVER=dummy` and
`SDL_AUDIODRIVER=dummy` before pygame is imported, and a session fixture calls
`pygame.display.set_mode((1,1))` so a real Surface exists (for `convert_alpha`)
without opening a window.

Add `.venv/` to `.gitignore` (the Python section does not currently ignore it).

## TDD work breakdown

Ordered so the fully unit-testable core lands before the pygame shell; each item is
one independently shippable issue with a testable outcome, sized to one red/green
cycle. Asset sourcing (Epic 5) can proceed in parallel once the skeleton exists.

Epic 0 - Tooling and scaffold
1. `pyproject.toml` (src layout, deps, ruff/mypy/pytest), `.gitignore` `.venv/`,
   `tests/conftest.py`. Outcome: on a clean `.venv`, `pytest`, `ruff check`, and
   `mypy` exit 0, and `python3 -m ascent --version` prints a version and exits 0.

Epic 1 - Deterministic core primitives
2. Seedable RNG group. Outcome: two groups from the same seed yield identical
   sequences on a stream; a stream restored from saved state continues identically.
3. Combatant and block model. Outcome: 8 damage against 5 block loses 3 HP and
   clears block; block resets at turn start.
4. Status modifier pipeline. Outcome: a +2-Strength attack into a Vulnerable target
   deals `ceil((base+2)*1.5)`; Weak reduces dealt attack damage by 25%; the
   affliction debuff behaves per spec.
5. Effect primitives and resolver. Outcome: resolving `[Damage 6, GainBlock 5]`
   drops enemy HP by 6, gives 5 block, and emits `DamageDealt` then `BlockGained`.

Epic 2 - Combat engine
6. Card pile model. Outcome: drawing from an empty draw pile reshuffles the discard
   deterministically and draws the top card; exhaust removes a card for the combat.
7. Turn engine and energy. Outcome: playing a 1-cost card with 3 energy leaves 2 and
   moves it to discard; ending the turn clears block, resolves intents, draws 5,
   restores energy to 3.
8. Enemy intent system (data-driven, seeded). Outcome: an enemy with AI `[attack6,
   block5]` telegraphs Attack(6) then Block reproducibly for a seed; a telegraphed
   Attack(6) into 0 block removes 6 HP.
9. Trigger/event bus and combat end. Outcome: a relic granting 1 block per attack
   played adds block each attack; combat wins when the last enemy hits 0 HP and
   loses when the player does.

Epic 3 - Content pipeline
10. Schema, loader, referential validation. Outcome: a card whose effect references
    an unknown status raises `ContentError` naming card and status; a well-formed
    set loads into a queryable `ContentDB`.
11. Ship MVP content. Outcome: at least 15 cards, 8 enemies (6 normal, 1 elite, 1
    boss), 8 relics, and potions; an integrity test asserts every effect and intent
    resolves against the effect vocabulary.

Epic 4 - Run structure
12. Seeded map generation. Outcome: a map from seed S has one boss reachable from
    every entry, and regenerating from S is identical.
13. Run aggregate and progression. Outcome: clearing a combat node advances to a
    connected node and awards gold from the reward stream; hp and gold persist.
14. Rewards, card upgrade, shop, rest, potions. Outcome: a reward offers 3 distinct
    card choices; buying a 75-gold card with 100 leaves 25; a rest heals 30% max HP;
    upgrading an attack raises its damage by its delta.
15. Versioned save/load. Outcome: a run round-trips through save then load
    identically; an unknown save version raises `SaveVersionError`.

Epic 5 - Asset pipeline (parallelisable after issue 16 skeleton)
16. Asset skeleton and `AssetManager`. Outcome: an empty `manifest.json` loads;
    a manifest test asserts every entry exists, is `CC0-1.0`, and matches its
    sha256 (passes vacuously when empty).
17. Source and vendor the CC0 asset set per the verification workflow, filling the
    manifest. Outcome: the manifest test passes with the full slice art present and
    every entry CC0 with a recorded sha256 and licence proof.

Epic 6 - Presentation shell
18. Pygame scene machine and headless smoke. Outcome: under `SDL_VIDEODRIVER=dummy`,
    constructing each scene and calling `render()` once does not raise; a scripted
    event sequence drives Title -> Map -> Combat -> Reward -> GameOver; and a guard
    test asserts importing `ascent.core` never loads `pygame`.
19. Wire scenes to art and the core view. Outcome: the combat scene renders cards,
    enemy intents, hp/energy/block from `combat.to_view()` using `AssetManager`
    keys, and a full slice run is playable end to end from the title screen.

## Verification

- Environment: `python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"`.
- Full suite (definition of done, no skip flags): `pytest`.
- Lint: `ruff check .` and `ruff format --check .`. Types: `mypy`.
- Layering guard (a test, run within `pytest`): importing `ascent.core` leaves
  `pygame` out of `sys.modules`.
- Asset integrity (a test): every `manifest.json` entry exists, is `CC0-1.0`, and
  matches its recorded sha256.
- Headless smoke (a test): scripted events drive the scene machine through a full
  Title -> Map -> Combat -> Reward -> GameOver path without raising, no pixel asserts.
- Manual run: `python3 -m ascent` opens a window (a display is available in the
  dev container) and a full slice run is playable from the title screen.
- Reproducibility: the same seed produces the same map, shuffles, and rewards
  (asserted by golden-value tests; Mersenne Twister sequences are stable across
  CPython versions).

## Handover to the repo pipeline

This plan is written to the plan-mode scratch file. On approval, per `PROCESS.md`:
save it to `docs/plans/ascent.md`, optionally run `/dyalog:crev docs/plans/ascent.md`
for an adversarial review, then convert it to a GitHub Epic per epic above with one
child issue per numbered item, each carrying its testable outcome as acceptance
criteria and referencing the plan document. Then `Proceed <issue>` starts the first
red/green cycle on issue 1.

## Risks and decisions to confirm

- Codename `ascent` and the absolute rule against any Slay the Spire names/art.
- mypy `strict` globally with a pygame override; relax `ui` only if stubs prove painful.
- CI must have network access to install the `pygame-ce` wheel (no compilation
  expected: manylinux wheels exist for 3.11).
- CC0 traps: game-icons.net (CC-BY), OFL fonts (not CC0), OpenGameArt mixed licences.
  Any exception is human-approved and recorded in the manifest.
- Save granularity node-boundary only for the MVP; mid-combat resume is a stretch goal.
