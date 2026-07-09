# Plan: roguelike deck-builder, text UI (Textual), minimal slice

## Context

Ascent is a roguelike deck-builder loosely in the spirit of Slay the Spire:
turn-based single-character combat, a short path through one act, a small deck of
cards, seeded reproducible runs, and node-boundary save/resume. The presentation
is a terminal UI built on Textual (a pure-Python TUI framework). There are no
image, audio, or font assets, so the CC0 asset pipeline from the earlier pygame
plan is dropped entirely along with its security and provenance machinery.

The repo is a greenfield "agent workshop kit" with a strict red/green TDD
pipeline (`CLAUDE.md`, `PROCESS.md`) and enforcement hooks. Python 3.11 is
available via a mandatory `.venv` (PEP 668). The scaffold (issue 1, merged)
provides the toolchain and a `python3 -m ascent --version` entry point; this plan
retargets it from pygame to Textual and builds a playable slice on top.

Working under a time constraint: scope is cut to a minimal playable slice and
tests are deliberately few and simple (one clear behaviour each, a handful per
issue, no exhaustive coverage).

## Confirmed direction (from the user)

| Decision | Choice |
|---|---|
| Presentation | Terminal text UI, Textual (`textual>=0.60`) |
| Scope | Minimal playable slice, not the full deck-builder |
| Tests | Few and simple, given the time constraint |

## Design defaults (open to challenge at review)

- Codename stays `ascent`. Do not use the "Slay the Spire" name, characters, or
  card names anywhere. "Loosely inspired" is a flavour brief only.
- Content (cards, enemies) is defined as frozen stdlib dataclasses in Python, not
  JSON. A JSON loader is deferred; it is not worth the cost at slice scope.
- Card behaviour is a short typed list of effect dataclasses resolved by one small
  function. No effect/event-bus system and no relics in the slice; both are
  deferred.
- RNG via seeded `random.Random` streams; never module-level `random.*`.
- Save granularity: node boundaries only (combat is atomic). Mid-combat resume is
  a documented stretch goal.
- Core never imports Textual. This one-way dependency is the most important
  invariant and is enforced by a test, not just convention.

## Architecture

Two layers with a one-way dependency rule: `ui` depends on `core`; `core` never
imports `textual`. The core is headless and deterministic, so almost every test
runs against it directly with no terminal involved. The Textual layer reads a
derived view from the core and translates key presses into core commands; it
never mutates core state directly.

### Package layout (src layout)

```
src/ascent/
  __init__.py                 # __version__
  __main__.py                 # `python3 -m ascent`: --version, else launch the app
  core/                       # HEADLESS, deterministic. MUST NOT import textual
    rng.py                    # RngGroup: named, independent, seedable streams
    ids.py                    # enums: CardType, Target, IntentKind, NodeType
    entities.py               # Combatant: hp, block, statuses; damage/block model
    effects.py                # effect dataclasses (Damage, GainBlock, ...) + resolver
    cards.py                  # Card runtime + the slice card set
    combat.py                 # CombatState + turn/energy engine + enemy intents
    content.py                # frozen CardDef / EnemyDef definitions (Python literals)
    map.py                    # short seeded path of nodes
    run.py                    # Run aggregate (the save root)
    save.py                   # versioned to_dict/from_dict
  ui/                         # Textual ONLY here
    app.py                    # AscentApp: owns the Run and the screen stack
    screens/                  # title, map, combat, reward, game_over
tests/
  core/                       # the bulk of the tests
  ui/                         # one Pilot smoke test
```

### Determinism

`RngGroup(seed)` derives named independent streams (`map`, `shuffle`, `enemy_ai`,
`card_reward`) so consuming randomness in one subsystem never shifts another.
Stream seeds derive via `hashlib.sha256(f"{seed}:{name}")`, never the builtin
`hash()` (salted by `PYTHONHASHSEED`), so a seed reproduces a run across
processes. Per-combat streams re-derive from `(seed, name, encounter_index)` so a
single combat can be built in isolation with a known shuffle. Streams serialise
via `Random.getstate()/setstate()`. No wall-clock, `uuid4`, or `time` in `core`.

### Combat model

`Combatant` holds hp, block, and a small status map. Damage applies to block
first, then hp; block resets at the owner's turn start. Cards carry a typed list
of effect dataclasses (`Damage`, `GainBlock`, and a minimal `ApplyStatus` for
Vulnerable/Weak). One `resolve` function is the only place effects mutate state.
`CombatState` drives turns: the player has energy, plays cards from hand to
discard, and ends the turn; enemies then act on a seeded, data-driven intent
(a fixed cycle for the slice). Drawing from an empty draw pile reshuffles the
discard deterministically. Combat is won when the last enemy reaches 0 hp and
lost when the player does.

### UI and save

`AscentApp` owns the `Run` and a Textual screen stack (Title, Map, Combat,
Reward, GameOver). A screen reads a plain view snapshot from the core, renders it
with Textual widgets, and turns key presses into core commands. Save serialises
the `Run` to JSON with a top-level integer `save_version`: seed, per-stream RNG
states, hp, gold, deck as `{def_id}`, and the current node. Explicit
`to_dict`/`from_dict` (not `dataclasses.asdict`, which mishandles enums and RNG
state); an unknown version raises `SaveVersionError`.

## Project tooling

Single `pyproject.toml` as the source of truth (already configured for
ruff/mypy/pytest by issue 1). Changes for this plan:

- Runtime dep: replace `pygame-ce` with `textual>=0.60`.
- mypy override for `pygame.*` becomes `textual.*` only if stub gaps appear;
  Textual ships type information, so no override is expected.
- Headless tests need no SDL drivers. `conftest.py` drops the pygame session
  fixture. Textual UI tests run headless through `App.run_test()` (a Pilot),
  which needs no real terminal.

## TDD work breakdown

Issue 1 (scaffold and `--version`) is merged. The remaining slice is five issues,
core first so the fully unit-testable logic lands before the Textual shell.

Issue 2 - Retarget toolchain to Textual
- Swap `pygame-ce` for `textual` in `pyproject.toml`; drop the SDL session fixture
  from `conftest.py`. Add a layering guard test.
- Outcome: on a clean `.venv`, `pytest`, `ruff check`, `ruff format --check`, and
  `mypy` exit 0; `python3 -m ascent --version` still works; and importing
  `ascent.core` leaves `textual` out of `sys.modules`.

Issue 3 - Deterministic core: RNG and combat model
- `RngGroup` (named seedable streams, save/restore) and `Combatant` (hp, block,
  damage application).
- Outcome (a few tests): two groups from one seed match on a stream and a stream
  restored from state continues identically; 8 damage into 5 block loses 3 hp and
  clears block; block resets at turn start.

Issue 4 - Cards, effects, and the turn engine
- Effect dataclasses and `resolve`; `CombatState` turn/energy engine; seeded enemy
  intent; win/lose.
- Outcome (a few tests): resolving `[Damage 6, GainBlock 5]` drops enemy hp by 6
  and grants 5 block; playing a 1-cost card with 3 energy leaves 2 and moves it to
  discard; ending the turn resolves the enemy intent and refills energy; combat is
  won when the enemy reaches 0 hp.

Issue 5 - Content, map, run, and save
- Frozen `CardDef`/`EnemyDef` content; a short seeded map; the `Run` aggregate;
  versioned save/load.
- Outcome (a few tests): a map from seed S is identical when regenerated and ends
  at a boss; clearing a combat node advances the run and awards gold; a run
  round-trips through save then load identically and an unknown version raises
  `SaveVersionError`.

Issue 6 - Textual UI shell
- `AscentApp` and the five screens, wired to the core view and commands.
- Outcome (one Pilot smoke test): under `App.run_test()`, a scripted key sequence
  drives Title -> Map -> Combat -> Reward -> GameOver without raising; and the
  layering guard from issue 2 still holds. Manual run: `python3 -m ascent` is
  playable end to end from the title screen.

## Verification

- Environment: `python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"`.
- Full suite (definition of done, no skip flags): `pytest`.
- Lint: `ruff check .` and `ruff format --check .`. Types: `mypy`.
- Layering guard (a test): importing `ascent.core` leaves `textual` out of
  `sys.modules`.
- Reproducibility: the same seed produces the same map and shuffles (asserted by a
  small golden-value test; Mersenne Twister sequences are stable across CPython
  versions).
- Headless UI smoke (a test): a scripted Pilot run drives the full screen path
  without raising, no cell-level assertions.

## Risks and decisions to confirm

- Codename `ascent`; the absolute rule against any Slay the Spire names.
- Content as Python dataclasses rather than JSON: faster now, but a later data
  format is a separate change.
- No relics, potions, shop, rest sites, or events in the slice; all deferred.
- Save granularity node-boundary only; mid-combat resume is a stretch goal.
