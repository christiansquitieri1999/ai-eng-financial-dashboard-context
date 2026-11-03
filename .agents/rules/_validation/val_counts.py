import random

rng = random.Random(1234)


def draw(n=3):
    return [random.randint(0, 1000) for _ in range(n)]


import sys

sys.path.insert(0, r"C:\Users\chris\ai-eng-financial-dashboard-context\backend")
from app.routes import generate_mock_movements  # noqa: E402

random.seed(999)
draw()
undisturbed = draw()

random.seed(999)
draw()
generate_mock_movements(seed=42)
disturbed = draw()

print(f"undisturbed next 3 draws : {undisturbed}")
print(f"after a request call     : {disturbed}")
print(f"R6: global stream disturbed by generate_mock_movements -> {undisturbed != disturbed}")

print()
print("=== R18 token count, three methods ===")
import pathlib

root = pathlib.Path(r"C:\Users\chris\ai-eng-financial-dashboard-context")
glob_sets = {
    "backend/app/*.py": list(root.glob("backend/app/*.py")),
    "frontend/src/lib/*.ts": list(root.glob("frontend/src/lib/*.ts")),
    "frontend/src/components/dashboard/*.tsx": list(root.glob("frontend/src/components/dashboard/*.tsx")),
}
grand = 0
for label, files in glob_sets.items():
    subtotal = sum(f.read_text(encoding="utf-8").lower().count("outcome") for f in files)
    grand += subtotal
    print(f"{label:<45} {subtotal} occurrences across {len(files)} file(s)")
print(f"{'TOTAL substring occurrences':<45} {grand}")

print()
print("Whole-word 'outcome' (not outcome_total / totalOutcome):")
import re

pattern = re.compile(r"\boutcome\b")
grand_words = 0
for files in glob_sets.values():
    for f in files:
        grand_words += len(pattern.findall(f.read_text(encoding="utf-8")))
print(f"{'TOTAL whole-word occurrences':<45} {grand_words}")

print()
print("=== Frontend files only ===")
fe = sum(
    f.read_text(encoding="utf-8").lower().count("outcome")
    for files in list(glob_sets.values())[1:]
    for f in files
)
print(f"frontend substring total: {fe}")
