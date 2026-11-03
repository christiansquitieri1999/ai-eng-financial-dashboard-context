"""Validation for the documentation, config and deployment rules.

Each check prints the claim it tests, the evidence found in the repo, and a
VERDICT. Run from the repository root:

    python .agents/rules/_validation/val_docs_config.py
"""
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
results: list[tuple[str, str, bool]] = []


def check(rule: str, claim: str, ok: bool, evidence: str) -> None:
    results.append((rule, claim, ok))
    verdict = "CONFIRMED" if ok else "NOT REPRODUCED"
    print(f"[{verdict}] {rule}")
    print(f"  claim   : {claim}")
    print(f"  evidence: {evidence}")
    print()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


# ---------------------------------------------------------------- R23
readme = read(ROOT / "README.md")
compose = read(ROOT / "docker-compose.yml")
app_tsx = read(ROOT / "frontend" / "src" / "App.tsx")

compose_ports = re.findall(r'"(\d+):(\d+)"', compose)
host_ports = [p[0] for p in compose_ports]
readme_ports = sorted(set(re.findall(r"localhost:(\d+)", readme)))

check(
    "R23",
    "README states a backend port that contradicts the port Compose publishes",
    bool(host_ports) and set(readme_ports) != set(host_ports),
    f"compose publishes host {host_ports}; README mentions localhost ports {readme_ports}",
)

app_port = re.search(r'localhost:(\d+)', app_tsx)
check(
    "R23",
    "README claims the Vite proxy is the default while App.tsx uses an absolute origin",
    bool(app_port) and bool(re.search(r"proxy", readme, re.I)),
    f"App.tsx absolute origin port = {app_port.group(1) if app_port else 'none'}; "
    f"README mentions proxy = {bool(re.search(r'proxy', readme, re.I))}",
)

missing_refs = [
    name
    for name in ("verification.md", "rules-proposed.md")
    if name not in readme
]
check(
    "R23",
    "Repository analysis artifacts are not reachable from the README",
    bool(missing_refs),
    f"not referenced by README: {missing_refs or 'none -- already linked'}",
)

# ---------------------------------------------------------------- R15
agents_md = read(ROOT / "AGENTS.md")
agents_refs = re.findall(r"\./\.agents/(?:rules|skills)|\./memory-bank", agents_md)
absent = sorted({ref for ref in agents_refs if not (ROOT / ref.replace("./", "")).exists()})
check(
    "R15",
    "AGENTS.md references paths that do not exist",
    bool(absent),
    f"referenced = {sorted(set(agents_refs))}; absent on disk = {absent or 'none'}",
)
# Per-path optionality: split AGENTS.md into bullets and inspect each bullet on
# its own, instead of slicing the whole document (which finds the marker that
# belongs to a *different* path).
bullets = [b.strip() for b in re.split(r"\n\s*-\s+", agents_md) if b.strip()]
optionality: dict[str, bool] = {}
for path in ("./.agents/rules", "./.agents/skills", "./memory-bank"):
    bullet = next((b for b in bullets if path in b), "")
    optionality[path] = "if the directory exists" in bullet.lower()
check(
    "R15",
    "AGENTS.md qualifies ./memory-bank as optional but not ./.agents/skills",
    optionality["./memory-bank"] and not optionality["./.agents/skills"],
    f"per-bullet optional marker: {optionality}",
)

# ---------------------------------------------------------------- R8
dockerignores = {
    str(p.relative_to(ROOT)): p.exists()
    for p in (ROOT / ".dockerignore", ROOT / "backend" / ".dockerignore", ROOT / "frontend" / ".dockerignore")
}
backend_ignore = set(read(ROOT / "backend" / ".dockerignore").splitlines())
frontend_ignore = set(read(ROOT / "frontend" / ".dockerignore").splitlines())
copy_all = {
    name: bool(re.search(r"COPY\s+\.\s+\.", read(ROOT / name)))
    for name in ("backend/Dockerfile", "frontend/Dockerfile")
}
gitignore = read(ROOT / ".gitignore")
env_gitignored = [ln for ln in gitignore.splitlines() if ".env" in ln]
required_backend_excludes = {"__pycache__/", "*.py[cod]", ".pytest_cache/", ".env", ".env.*"}
required_frontend_excludes = {"node_modules/", "dist/", "coverage/", ".env", ".env.*"}
check(
    "R8",
    "Both Docker build contexts exclude local dependencies, caches, and env files",
    dockerignores["backend\\.dockerignore"]
    and dockerignores["frontend\\.dockerignore"]
    and required_backend_excludes.issubset(backend_ignore)
    and required_frontend_excludes.issubset(frontend_ignore)
    and all(copy_all.values()),
    f"backend exclusions present = {required_backend_excludes.issubset(backend_ignore)}; "
    f"frontend exclusions present = {required_frontend_excludes.issubset(frontend_ignore)}; "
    f"COPY . . = {copy_all}",
)
check(
    "R8",
    "Frontend local env files are excluded from Git and Docker while the example remains included",
    bool(env_gitignored)
    and {".env", ".env.*", "!.env.example"}.issubset(frontend_ignore),
    f".gitignore .env rules = {env_gitignored or 'none'}; "
    f"frontend .dockerignore env rules = "
    f"{sorted(entry for entry in frontend_ignore if entry.startswith('!') or entry == '.env' or entry.startswith('.env.'))}",
)

# ---------------------------------------------------------------- R9
frontend_dockerfile = read(ROOT / "frontend" / "Dockerfile")
lockfile = (ROOT / "frontend" / "package-lock.json").exists()
uses_install = bool(re.search(r"npm\s+install", frontend_dockerfile))
uses_ci = bool(re.search(r"npm\s+ci", frontend_dockerfile))
check(
    "R9",
    "A lockfile is committed but the image resolves deps with npm install instead of npm ci",
    lockfile and uses_install and not uses_ci,
    f"package-lock.json present = {lockfile}; npm install = {uses_install}; npm ci = {uses_ci}",
)

# ---------------------------------------------------------------- R10
requirements = read(ROOT / "backend" / "requirements.txt")
dev_tools = [
    t for t in ("pytest", "pytest-cov", "debugpy") if re.search(rf"^\s*{re.escape(t)}", requirements, re.M)
]
pinned = [ln.strip() for ln in requirements.splitlines() if ln.strip() and "==" in ln]
unpinned = [
    ln.strip()
    for ln in requirements.splitlines()
    if ln.strip() and not ln.strip().startswith("#") and "==" not in ln
]
check(
    "R10",
    "Runtime requirements contain test and debugger tooling",
    bool(dev_tools),
    f"dev tooling in requirements.txt = {dev_tools}",
)
check(
    "R10",
    "requirements.txt is unpinned, so image builds are not reproducible",
    bool(unpinned),
    f"unpinned entries = {unpinned}; pinned = {pinned or 'none'}",
)

# ---------------------------------------------------------------- R16
vite_config = read(ROOT / "frontend" / "vite.config.ts")
# The file uses double quotes; accept either so the check does not depend on style.
proxy_target = re.search(r"""target:\s*['"]([^'"]+)['"]""", vite_config)
target = proxy_target.group(1) if proxy_target else "none"
target_host = urlparse(target).hostname
has_backend_service = bool(re.search(r"(?m)^\s{2}backend:\s*$", compose))
publishes_backend = ("8001", "8000") in compose_ports
check(
    "R16",
    "The Vite proxy uses the Compose service address, distinct from the host-published backend port",
    target_host == "backend" and has_backend_service and publishes_backend,
    f"vite proxy target = {target}; backend service declared = {has_backend_service}; "
    f"host publishes 8001:8000 = {publishes_backend}",
)

# ---------------------------------------------------------------- C6 / C7
check(
    "C6",
    "The repository has a .gitignore covering build output",
    "node_modules" in gitignore,
    f".gitignore covers node_modules = {'node_modules' in gitignore}",
)
compose_healthcheck = "healthcheck" in compose
check(
    "C7",
    "docker-compose.yml declares depends_on without a healthcheck",
    "depends_on" in compose and not compose_healthcheck,
    f"depends_on = {'depends_on' in compose}; healthcheck = {compose_healthcheck}",
)

# ---------------------------------------------------------------- summary
print("=" * 72)
confirmed = sum(1 for _, _, ok in results if ok)
print(f"CONFIRMED {confirmed}/{len(results)}")
for rule, claim, ok in results:
    if not ok:
        print(f"  NOT REPRODUCED: {rule} -- {claim}")
sys.exit(0 if confirmed == len(results) else 1)
