"""
nanoOctopus -- Signature-Based Agent Deconfliction

Octopus arms operate semi-autonomously: ~350 million of the animal's 500
million neurons reside in the arms, not the brain. When multiple arms
manipulate objects simultaneously, a chemical self-recognition mechanism
prevents them from interfering with each other. Suckers produce a signal
that inhibits grip on the animal's own skin -- no central coordination
required (Nesher, Levy, Grasso & Hochner, 2014, Current Biology 24(11)).

This code translates that mechanism to multi-agent file coordination:
  - Each agent carries a SIGNATURE: the set of files it owns.
  - Before modifying a file, the agent checks a shared SIGNATURE STORE.
  - If another agent's signature covers that file, the modification is
    reflexively skipped. No orchestrator. No lock manager.
  - An agent never blocks on its own files (self-recognition).

Run with --no-deconfliction to see the same agents produce file conflicts.

Usage:  python octopus.py                     # with deconfliction
        python octopus.py --no-deconfliction  # without (shows conflicts)
"""
import argparse, json, os, random, subprocess, sys, threading, time
from pathlib import Path

REPO_DIR = Path(__file__).parent / "test_repo"
SIGNATURE_FILE = ".agent-signatures.json"

# ANSI colours (stdlib only). Respects https://no-color.org
_NC = os.environ.get("NO_COLOR")
G, R, Y, C, B, D, Z = (("",)*7 if _NC else
    ("\033[32m","\033[31m","\033[33m","\033[36m","\033[1m","\033[2m","\033[0m"))
_plock = threading.Lock()
def _tp(msg):
    with _plock: print(msg)

# ---------------------------------------------------------------------------
# Task definitions: what each agent does and which files it owns.
# Biological analogue: each arm has a task and a territory of skin whose
# chemical signal it recognises as 'self'. (Nesher et al., 2014)
# ---------------------------------------------------------------------------
TASKS = [
    {"agent_id": "A", "name": "Connection pooling and retry logic",
     "primary": ["auth/login.py","auth/tokens.py"],
     "shared": ["shared/database.py","shared/config.py"],
     "owns": ["shared/database.py","shared/config.py"]},
    {"agent_id": "B", "name": "Input sanitisation hardening",
     "primary": ["users/profile.py","users/permissions.py"],
     "shared": ["shared/validation.py","shared/database.py"],
     "owns": ["shared/validation.py"]},
    {"agent_id": "C", "name": "CSV export format support",
     "primary": ["reports/generate.py","reports/export.py"],
     "shared": ["shared/config.py"], "owns": []},
    {"agent_id": "D", "name": "Rate limiting for notifications",
     "primary": ["notifications/email_sender.py","notifications/sms.py"],
     "shared": ["shared/validation.py"], "owns": []},
]

# ---------------------------------------------------------------------------
# Modifications: the code each agent appends to each file. Each includes a
# marker comment for conflict detection after a run.
# ---------------------------------------------------------------------------
MODS = {
("A","auth/login.py"): """
# --- Added by Agent A: Retry logic ---
def authenticate_with_retry(username, password, max_retries=3):
    for attempt in range(max_retries):
        result = authenticate(username, password)
        if result["success"]: return result
        time.sleep(0.1 * (2 ** attempt))
    return result
""",
("A","auth/tokens.py"): """
# --- Added by Agent A: Token retry decorator ---
import functools
def with_retry(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        for i in range(get("max_retries", 3)):
            try: return func(*a, **kw)
            except Exception:
                if i == get("max_retries", 3) - 1: raise
    return wrapper
""",
("A","shared/database.py"): """
# --- Added by Agent A: Connection pooling ---
_pool, _pool_size = [], 5
def get_pooled_connection():
    return _pool.pop() if _pool else get_connection()
def release_connection(conn):
    if len(_pool) < _pool_size: _pool.append(conn)
""",
("A","shared/config.py"): """
# --- Added by Agent A: Pool and retry configuration ---
_config.update({"pool_size": 5, "retry_delay": 0.5, "connection_timeout": 30})
""",
("B","users/profile.py"): """
# --- Added by Agent B: Profile field sanitisation ---
def sanitise_profile_fields(profile):
    from shared.validation import sanitise_string
    return {k: sanitise_string(v) if isinstance(v, str) else v for k, v in profile.items()}
""",
("B","users/permissions.py"): """
# --- Added by Agent B: Role name validation ---
def validate_role_name(role):
    from shared.validation import validate_length
    clean = sanitise_string(role)
    return clean == role and validate_length(role, 2, 32)
""",
("B","shared/validation.py"): """
# --- Added by Agent B: HTML sanitisation ---
DANGEROUS_PATTERNS = [r'<script.*?>', r'javascript:', r'on\\w+\\s*=']
def sanitise_html(value):
    result = value
    for pat in DANGEROUS_PATTERNS: result = re.sub(pat, '', result, flags=re.IGNORECASE)
    return result
""",
("B","shared/database.py"): """
# --- Added by Agent B: Query parameter sanitisation ---
def sanitise_query_params(params):
    if params is None: return None
    return tuple(str(p).replace("'", "''") for p in params)
""",
("C","reports/generate.py"): """
# --- Added by Agent C: CSV report generation ---
def generate_csv_report(data, columns=None):
    if not data: return ""
    columns = columns or list(data[0].keys())
    lines = [",".join(columns)]
    for row in data: lines.append(",".join(str(row.get(c, "")) for c in columns))
    return "\\n".join(lines)
""",
("C","reports/export.py"): """
# --- Added by Agent C: Enhanced CSV export ---
def export_csv_with_options(report, filepath, delimiter=","):
    import csv
    with open(filepath, 'w', newline='') as f:
        w = csv.writer(f, delimiter=delimiter)
        if report.get("headers"): w.writerow(report["headers"])
        for row in report.get("rows", []): w.writerow(row)
    return filepath
""",
("C","shared/config.py"): """
# --- Added by Agent C: CSV export configuration ---
_config.update({"csv_delimiter": ",", "csv_quoting": "minimal"})
""",
("D","notifications/email_sender.py"): """
# --- Added by Agent D: Rate limiting ---
import time as _time
class RateLimiter:
    def __init__(self, rate=10.0, cap=10.0):
        self.rate, self.cap, self._tokens, self._t = rate, cap, cap, _time.monotonic()
    def allow(self):
        now = _time.monotonic()
        self._tokens = min(self.cap, self._tokens + (now - self._t) * self.rate)
        self._t = now
        if self._tokens >= 1.0: self._tokens -= 1.0; return True
        return False
_rate_limiter = RateLimiter()
""",
("D","notifications/sms.py"): """
# --- Added by Agent D: Rate-limited SMS sending ---
def send_sms_rated(phone, message):
    from notifications.email_sender import _rate_limiter
    if not _rate_limiter.allow(): return {"success": False, "error": "Rate limit exceeded"}
    return send_sms(phone, message)
""",
("D","shared/validation.py"): """
# --- Added by Agent D: Rate limit validation ---
def validate_rate_limit(count, max_per_minute=60):
    return 0 <= count <= max_per_minute
""",
}

# =========================================================================
#  SIGNATURE STORE
#
#  The chemical self-recognition system. In the octopus, skin produces a
#  chemical that suckers recognise as 'self', preventing the animal from
#  gripping its own body. (Nesher et al., 2014 -- suckers showed ~40%
#  reduced grip on own-skin extract vs ~95% on conspecific skin.)
# =========================================================================
class SignatureStore:
    """Thread-safe signature registry for agent file ownership."""
    def __init__(self, repo_dir):
        self._lock = threading.Lock()  # the chemical medium -- all agents sense it
        self._sigs = {}   # agent_id -> {files, task, t}
        self._log = []
        self._path = repo_dir / SIGNATURE_FILE

    def register(self, agent_id, files, task):
        """Broadcast chemical signal: 'these surfaces are mine'.
        (Nesher et al., 2014: arm skin exudes self-recognition chemical.)"""
        with self._lock:
            self._sigs[agent_id] = {"files": list(files), "task": task, "t": time.time()}
            self._log.append({"ev": "register", "ag": agent_id, "files": list(files)})
            self._persist()

    def check(self, agent_id, filepath):
        """Check whether another agent's signature covers this file.
        Returns ("clear", None) or ("blocked", blocker_id).
        Self-recognition: an agent never blocks on its own files, just as
        octopus suckers never grip their own skin. (Nesher et al., 2014)"""
        with self._lock:
            for sid, sd in self._sigs.items():
                if sid == agent_id: continue  # self-recognition
                if filepath in sd["files"]:
                    self._log.append({"ev": "blocked", "ag": agent_id, "file": filepath, "by": sid})
                    return ("blocked", sid)
            self._log.append({"ev": "clear", "ag": agent_id, "file": filepath})
            return ("clear", None)

    def release(self, agent_id):
        """Chemical signal fades when the arm withdraws. (Nesher et al., 2014)"""
        with self._lock:
            self._sigs.pop(agent_id, None)
            self._log.append({"ev": "release", "ag": agent_id})
            self._persist()

    def get_log(self):
        with self._lock: return list(self._log)

    def _persist(self):
        with open(self._path, "w") as f: json.dump(self._sigs, f, indent=2, default=str)

# =========================================================================
#  AGENT
#
#  Biological analogue: a single octopus arm with ~200 suckers, operating
#  semi-autonomously. The arm has its own task and checks chemical signals
#  before each grasp. Not an LLM -- modifications are predetermined.
# =========================================================================
class Agent:
    """Simulated agent that modifies files in a shared codebase."""
    def __init__(self, task, store, repo_dir, decon, seed, verbose):
        self.id = task["agent_id"]
        self.task = task
        self.store = store
        self.repo_dir = repo_dir
        self.decon = decon
        self.verbose = verbose
        self._rng = random.Random(seed + ord(self.id))
        self.results = {"agent": self.id, "task": task["name"],
                        "modified": [], "skipped": [], "blocked_by": {}}

    def run(self):
        """Execute the agent's task. The arm extends, contacts surfaces,
        grips (modifies) or recoils (skips) based on chemical signal."""
        active = self.task["primary"] + self.task["owns"]
        if self.decon:
            self.store.register(self.id, active, self.task["name"])
        time.sleep(self._rng.uniform(0.01, 0.05))  # stagger for interleaving

        # Deduplicated file list
        seen, files = set(), []
        for f in self.task["primary"] + self.task["shared"]:
            if f not in seen: seen.add(f); files.append(f)

        for fp in files:
            if (self.id, fp) not in MODS: continue
            # Deconfliction check -- the chemical self-recognition step
            if self.decon:
                status, blocker = self.store.check(self.id, fp)
                if status == "blocked":
                    self.results["skipped"].append(fp)
                    self.results["blocked_by"][fp] = blocker
                    _tp(f"{R}[Agent {self.id}] BLOCKED {fp} (owned by Agent {blocker}){Z}")
                    continue
            # Real file modification
            if self._modify(fp):
                self.results["modified"].append(fp)
                _tp(f"{G}[Agent {self.id}] Modified {fp}{Z}")
            time.sleep(self._rng.uniform(0.01, 0.03))

        # Signature persists until the runner releases it after all agents
        # finish. In biology: the chemical lingers on surfaces the arm has
        # contacted, fading only after the task is complete.
        return self.results

    def _modify(self, fp):
        """Append code to a file on disk. Real I/O, not simulated.
        In --no-deconfliction mode, concurrent writes race intentionally."""
        path = self.repo_dir / fp
        mod = MODS.get((self.id, fp))
        if not mod: return False
        try:
            content = path.read_text()
            # Without deconfliction the read-modify-write is non-atomic.
            # A delay between read and write widens the race window so
            # another agent can read stale content before our write lands.
            if not self.decon:
                time.sleep(self._rng.uniform(0.02, 0.06))
            path.write_text(content + mod)
            return True
        except OSError as e:
            _tp(f"{R}[Agent {self.id}] ERROR {fp}: {e}{Z}"); return False

# =========================================================================
#  RUNNER
# =========================================================================
def setup_repo(repo_dir):
    """Reset test_repo to baseline via git checkout."""
    git_dir = repo_dir / ".git"
    if not git_dir.exists():
        for cmd in [["git","init"],["git","add","-A"],
                    ["git","commit","-m","baseline"],["git","tag","baseline"]]:
            subprocess.run(cmd, cwd=repo_dir, capture_output=True)
    else:
        subprocess.run(["git","checkout","."], cwd=repo_dir, capture_output=True)
    sig = repo_dir / SIGNATURE_FILE
    if sig.exists(): sig.unlink()

def run_experiment(tasks, repo_dir, decon, seed, verbose):
    """Launch all agents concurrently. Biological analogue: octopus
    performing a complex task with all arms simultaneously."""
    setup_repo(repo_dir)
    store = SignatureStore(repo_dir)
    agents = [Agent(t, store, repo_dir, decon, seed, verbose) for t in tasks]
    mode = "DECONFLICTION ON" if decon else "DECONFLICTION OFF"
    print(f"\n{B}{'='*55}\n  nanoOctopus -- {mode}\n  Agents: {len(agents)}  |  Seed: {seed}\n{'='*55}{Z}\n")
    threads = [threading.Thread(target=a.run, name=f"Agent-{a.id}") for a in agents]
    for t in threads: t.start()
    for t in threads: t.join()
    # Release all signatures after the task completes (chemical fades)
    if decon:
        for a in agents: store.release(a.id)
    return [a.results for a in agents], store.get_log()

# =========================================================================
#  CONFLICT DETECTION
# =========================================================================
def detect_conflicts(repo_dir, tasks, all_results):
    """Check for modifications that were attempted but lost to overwrites.
    Only flags files an agent actually wrote (not files it was blocked from)."""
    conflicts = []
    # Build set of files each agent actually modified (not skipped)
    written = set()
    for r in all_results:
        for fp in r["modified"]:
            written.add((r["agent"], fp))
    shared = set()
    for t in tasks:
        for f in t["shared"]: shared.add(f)
    for fp in sorted(shared):
        path = repo_dir / fp
        if not path.exists(): continue
        content = path.read_text()
        for t in tasks:
            key = (t["agent_id"], fp)
            if key in written and f"Added by Agent {t['agent_id']}" not in content:
                conflicts.append((fp, t["agent_id"]))
    return conflicts

# =========================================================================
#  DISPLAY
# =========================================================================
def display_results(results, log, decon, repo_dir, tasks):
    """Print experiment summary."""
    modified = sum(len(r["modified"]) for r in results)
    skipped = sum(len(r["skipped"]) for r in results)
    conflicts = detect_conflicts(repo_dir, tasks, results)
    print(f"\n{B}{'='*55}\n  RESULTS\n{'='*55}{Z}")
    mode = "Signature-based deconfliction" if decon else "No deconfliction (free-for-all)"
    print(f"  Mode:              {mode}")
    print(f"  Agents:            {len(results)}")
    print(f"  Files modified:    {modified}")
    print(f"  Files skipped:     {skipped}{' (deconfliction)' if skipped else ''}")
    c_str = f"{R}{len(conflicts)}{Z}" if conflicts else f"{G}0{Z}"
    print(f"  Conflicts:         {c_str}")
    print(f"  Coordinator msgs:  0")
    if conflicts:
        print(f"\n  {R}Conflicting files (modifications lost):{Z}")
        for fp, aid in conflicts:
            print(f"    {fp} -- Agent {aid}'s changes overwritten")
    if skipped:
        print(f"\n  {Y}Deconfliction events:{Z}")
        for r in results:
            for fp in r["skipped"]:
                print(f"    Agent {r['agent']} skipped {fp} (owned by Agent {r['blocked_by'].get(fp,'?')})")
    hint = "Run without --no-deconfliction to see the signature mechanism." if not decon \
        else "Run with --no-deconfliction to compare."
    print(f"\n  {D}{hint}{Z}")
    print(f"{B}{'='*55}{Z}\n")

# =========================================================================
#  MAIN
# =========================================================================
def main():
    p = argparse.ArgumentParser(
        description="nanoOctopus: octopus-inspired signature-based agent deconfliction")
    p.add_argument("--no-deconfliction", action="store_true",
                   help="disable signature checking (agents write freely, conflicts likely)")
    p.add_argument("--agents", type=int, default=4, choices=range(1,5), metavar="N",
                   help="number of concurrent agents, 1-4 (default: 4)")
    p.add_argument("--seed", type=int, default=42,
                   help="random seed for reproducible runs (default: 42)")
    p.add_argument("--verbose", action="store_true",
                   help="print detailed per-file deconfliction checks")
    args = p.parse_args()
    decon = not args.no_deconfliction
    res, log = run_experiment(TASKS[:args.agents], REPO_DIR, decon, args.seed, args.verbose)
    display_results(res, log, decon, REPO_DIR, TASKS[:args.agents])

if __name__ == "__main__":
    main()
