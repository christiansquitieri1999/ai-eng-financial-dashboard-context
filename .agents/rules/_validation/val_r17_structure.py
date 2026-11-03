"""R17 probe: measure how much one module hosts.

Reports line count, declaration counts by kind, and the largest function spans
so the "split before adding routes" trigger can be stated with real numbers.
"""

import ast
import pathlib

PATH = pathlib.Path(__file__).resolve().parents[3] / "backend" / "app" / "routes.py"


def main() -> None:
    source = PATH.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source)

    print(f"file: {PATH.name}")
    print(f"lines: {len(lines)}")
    print()

    kinds: dict[str, int] = {}
    for node in tree.body:
        kind = type(node).__name__
        kinds[kind] = kinds.get(kind, 0) + 1
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    kinds[f"Assign:{target.id}"] = kinds.get(f"Assign:{target.id}", 0) + 1

    print("top-level declarations:")
    for kind in sorted(kinds, key=lambda k: (-kinds[k], k)):
        print(f"  {kind:24} {kinds[kind]}")
    print(f"  {'TOTAL':24} {sum(v for k, v in kinds.items() if not k.startswith('Assign:'))}")
    print()

    # Route decorators are the HTTP surface living inside the same module.
    # The app uses an APIRouter, so decorators are @router.get/@router.post,
    # not @app.get. A probe looking for "@app." finds zero and would wrongly
    # conclude there are no routes here.
    routes = [ln.strip() for ln in lines if ln.startswith("@router.")]
    print(f"route decorators (@router.*): {len(routes)}")
    for route in routes:
        print(f"  {route}")
    print()

    # Function spans, to show whether one module is also one giant function.
    spans = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            end = getattr(node, "end_lineno", node.lineno)
            spans.append((end - node.lineno + 1, node.name, node.lineno))
    spans.sort(reverse=True)
    print("largest top-level definitions:")
    for size, name, start in spans[:6]:
        print(f"  {size:4} lines  {name}  (line {start})")
    print()

    total_named = sum(s[0] for s in spans)
    print(f"lines inside named definitions: {total_named} / {len(lines)}")


if __name__ == "__main__":
    main()
