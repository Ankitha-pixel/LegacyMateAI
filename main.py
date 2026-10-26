
import subprocess
import sys
from pathlib import Path

print("\n===== LegacyMateAI =====")

steps = [
    ("Migration", "analyzer.py"),
    ("Verification", "test_migration.py"),
    ("Report generation", "report.py"),
]

for step_name, script in steps:
    print(f"\n--- {step_name} ---")

    result = subprocess.run(
        [sys.executable, script],
        text=True
    )

    if result.returncode != 0:
        print(f"Workflow stopped: {step_name} failed.")
        sys.exit(result.returncode)

print("\n===== Workflow completed =====")
print("Check migrated.py and migration_report.txt")
