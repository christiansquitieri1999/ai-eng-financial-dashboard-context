"""R20 / R4 probe: confirm the absence of persistence and config reading.

R20 says data acquisition lives inside request handlers with no persistence.
R4 says CORS is wildcard. Both are absence claims, so they need to be checked
exhaustively rather than by grepping for one guessed library name.
"""

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"

DB_MODULES = [
    "sqlite3", "sqlalchemy", "psycopg2", "psycopg", "pymongo", "redis",
    "asyncpg", "aiosqlite", "databases", "alembic", "peewee", "tortoise",
    "motor", "pymysql", "mysql", "cx_Oracle", "duckdb",
]

CONFIG_MODULES = ["os", "dotenv", "pydantic_settings", "configparser", "pathlib"]


def python_files() -> list[pathlib.Path]:
    return sorted(p for p in BACKEND.rglob("*.py") if "tests" not in p.parts)


def main() -> None:
    files = python_files()
    print(f"backend python files (excluding tests): {len(files)}")
    for f in files:
        print(f"  {f.relative_to(ROOT)}")
    print()

    imports: set[str] = set()
    trees: dict[pathlib.Path, ast.Module] = {}
    for f in files:
        tree = ast.parse(f.read_text(encoding="utf-8"))
        trees[f] = tree
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

    print("all imported top-level modules:")
    for name in sorted(imports):
        print(f"  {name}")
    print()

    found_db = sorted(imports & set(DB_MODULES))
    print(f"R20 database clients found: {found_db or 'NONE'}")
    print(f"R20 config modules found:   {sorted(imports & set(CONFIG_MODULES)) or 'NONE'}")
    print()

    # Environment reads are the other half of "no external configuration".
    env_reads = []
    for f, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in {
                "environ", "getenv", "putenv",
            }:
                env_reads.append(f"{f.relative_to(ROOT)}:{node.lineno} .{node.attr}")
    print(f"R20 os.environ / os.getenv reads: {env_reads or 'NONE'}")
    print()

    # R4: the CORS configuration as actually written.
    main_py = BACKEND / "app" / "main.py"
    print(f"R4 {main_py.relative_to(ROOT)}:")
    for i, line in enumerate(main_py.read_text(encoding="utf-8").splitlines(), 1):
        if any(k in line for k in ("CORSMiddleware", "allow_", "add_middleware")):
            print(f"  {i:3} {line.strip()}")
    print()

    # R20: data acquisition inside handlers means the generator is called from routes.
    routes_py = BACKEND / "app" / "routes.py"
    tree = ast.parse(routes_py.read_text(encoding="utf-8"))
    calls = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                    if sub.func.id == "generate_mock_movements":
                        calls.append(f"{node.name} (line {sub.lineno})")
    print(f"R20 handlers calling generate_mock_movements: {len(calls)}")
    for c in calls:
        print(f"  {c}")


if __name__ == "__main__":
    main()
