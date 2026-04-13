# nanoOctopus

Signature-based agent deconfliction in one file. No dependencies. Clone and run.

## The Problem

When multiple AI agents work on the same codebase simultaneously, they create
conflicts. Agent A adds connection pooling to `shared/database.py` while Agent B
adds query sanitisation to the same file. One overwrites the other.

Current solutions route coordination through a central point: lock managers
(bottleneck), optimistic concurrency with merge resolution (merge hell), or a
supervisor agent that sequences all work (single point of failure). Each adds
complexity and latency that scales poorly with agent count.

What if agents could avoid conflicts locally, without talking to a coordinator
at all?

## The Octopus Solution

The common octopus (*Octopus vulgaris*) has roughly 500 million neurons.
Two-thirds of them, around 350 million, reside in the eight arms rather than
the central brain. Each arm can taste, touch, and make grip decisions
independently. When an octopus manipulates objects with multiple arms at once,
the arms coordinate without constant instruction from the brain. The question
is: how do eight semi-autonomous arms avoid grabbing each other?

Nesher, Levy, Grasso and Hochner (2014) discovered the answer. Octopus skin
produces a chemical signal that the animal's own suckers recognise as "self".
When a sucker contacts skin carrying this signal, the grip reflex is inhibited.
The sucker does not grab. This is peripheral, not central: each sucker makes
the decision locally, using chemical detection alone. No neural message to the
brain, no coordination protocol between arms. The researchers showed that
suckers exhibited roughly 40% reduced grip force on extracts from the animal's
own skin compared to 95% grip on skin from another octopus.

The brain can override this mechanism when needed. Octopuses have been observed
feeding on severed arms from conspecifics, which requires gripping tissue that
carries the self-recognition chemical. The override exists, but the default is
local inhibition: avoid interference first, escalate only when necessary.

This code translates that mechanism directly. Each agent registers a
**signature**: the set of shared files it owns. Before modifying any file, the
agent checks the signature store. If another agent's signature covers that file,
the modification is skipped reflexively. No orchestrator consultation. No lock
negotiation. The agent simply moves on, just as the sucker simply does not grip.

## Quick Start

```
git clone https://github.com/Ivan2san/nanoOctopus.git
cd nanoOctopus
python octopus.py
```

Four agents, one shared codebase, zero conflicts. Now run it without
deconfliction:

```
python octopus.py --no-deconfliction
```

Same agents, same tasks, real file conflicts. The only difference is the
signature mechanism.

### Options

```
python octopus.py --help
python octopus.py --verbose           # show every deconfliction check
python octopus.py --seed 42           # reproducible run (default)
python octopus.py --agents 2          # run with fewer agents
```

## How It Works

The entire implementation lives in `octopus.py` (under 500 lines). It reads
top-to-bottom as a tutorial. Here is the structure:

### SignatureStore

The core mechanism. A thread-safe registry where agents declare ownership of
shared files before starting work.

```python
class SignatureStore:
    def register(self, agent_id, files, task):
        # "These surfaces are mine" -- broadcast chemical signal
    def check(self, agent_id, filepath):
        # Returns ("clear", None) or ("blocked", blocker_id)
        # Self-recognition: never blocks on own files
    def release(self, agent_id):
        # Chemical signal fades when the arm withdraws
```

The `check` method is where self-recognition happens. When an agent checks a
file, it iterates all registered signatures but **skips its own**. An agent
never blocks itself, just as an octopus sucker never grips its own skin.

### Agent

A simulated agent (not an LLM) that makes real file modifications on disk.
Each agent follows a scripted task: read certain files, modify certain files,
check deconfliction before each write.

```python
class Agent:
    def run(self):
        store.register(self.id, self.task["owns"], ...)
        for filepath in files_to_modify:
            status, blocker = store.check(self.id, filepath)
            if status == "blocked":
                skip(filepath)       # sucker recoils
            else:
                modify(filepath)     # sucker grips
        # signature persists until runner releases after all agents finish
```

### The Check-Before-Modify Loop

This is the entire coordination mechanism:

1. Agent reads its task definition (which files to modify, which it owns)
2. Agent registers its signature (owned shared files only)
3. For each file: check the store, then modify or skip
4. No retries, no queuing, no escalation. Blocked means skipped.

### Conflict Zones

The test repository has three shared files that multiple agents need:

| File | Agent A | Agent B | Agent C | Agent D |
|------|---------|---------|---------|---------|
| `shared/database.py` | **owns** | wants | | |
| `shared/config.py` | **owns** | | wants | |
| `shared/validation.py` | | **owns** | | wants |

With deconfliction, ownership is respected. Without it, concurrent writes race.

## Results

| Metric | Deconfliction ON | Deconfliction OFF |
|--------|-----------------|-------------------|
| Files modified | 11 | 14 |
| Files skipped | 3 | 0 |
| Conflicts | **0** | **2** |
| Coordinator messages | 0 | 0 |
| Task completeness | 78% | 100%* |

*100% completeness is misleading: all writes landed, but 2 were overwritten by
race conditions. The surviving content is corrupted.

The 78% completeness in deconfliction mode reflects the trade-off: agents skip
files they do not own rather than risk corruption. In a production system, a
second pass (or task decomposition that avoids overlapping ownership) recovers
the remaining 22%.

## The Biology

The self-recognition mechanism described by Nesher et al. (2014) is remarkable
for what it is *not*. It is not a neural signal. It is not a message passed
between arms. It is not a central decision. It is a chemical property of the
skin itself, detected locally by each sucker independently.

This matters for multi-agent systems because it demonstrates that coordination
does not require communication. The octopus solves a coordination problem
(do not interfere with yourself) using a mechanism that requires zero bandwidth
between the coordinating units. Each sucker has all the information it needs
in the chemical environment it directly contacts.

The computational translation preserves this property. The signature store is
a shared data structure, but agents only read from it. They never negotiate,
never retry, never escalate. The "chemical signal" (file ownership list) is
broadcast once at registration and checked locally before each operation.

The brain override (the ability to grip own tissue when feeding) maps to a
future `--override` flag or priority system where an agent can claim a file
despite another agent's signature. This is not implemented in v0, it is noted
here because the biological mechanism supports it.

### Key Reference

Nesher, R., Levy, G., Grasso, F. W., & Hochner, B. (2014). Self-Recognition
Mechanism between Skin and Suckers Prevents Octopus Arms from Interfering
with Each Other. *Current Biology*, 24(11), 1271-1275.

## Extending This

This is a reference implementation, not a framework. It stays at one file
forever. Some directions for people who want to build on the idea:

- **Real LLM agents**: Replace the simulated `Agent` class with Claude Code,
  Codex, or similar. The `SignatureStore` works unchanged.
- **Compression**: Add the octopus information bottleneck pattern (see the
  position paper) to reduce what agents communicate to the store.
- **Reflex loops**: Sucker-level error handling where agents retry locally
  before reporting failure.
- **MCP server**: Wrap the `SignatureStore` as an MCP tool for plug-and-play
  integration with any agent framework.
- **Dynamic ownership**: Negotiate ownership at task decomposition time rather
  than hardcoding it, addressing the 78% completeness limitation.

## Citation

If you use this in research:

```bibtex
@software{nanooctopus2026,
  author    = {Sanchez, Ivan},
  title     = {nanoOctopus: Signature-Based Agent Deconfliction},
  year      = {2026},
  url       = {https://github.com/Ivan2san/nanoOctopus},
  note      = {Reference implementation of chemical self-recognition
               for multi-agent coordination}
}
```

## References

- Nesher, R., Levy, G., Grasso, F. W., & Hochner, B. (2014). Self-Recognition
  Mechanism between Skin and Suckers Prevents Octopus Arms from Interfering
  with Each Other. *Current Biology*, 24(11), 1271-1275.

## Licence

MIT. See [LICENSE](LICENSE).
