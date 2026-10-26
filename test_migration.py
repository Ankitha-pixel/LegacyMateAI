
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "migrated.py"],
    capture_output=True,
    text=True,
    check=True
)

expected = "Sum = 30"
actual = result.stdout.strip()

print("Expected:", expected)
print("Actual:", actual)

if actual == expected:
    print("PASS: Migration test successful!")
else:
    print("FAIL: Output does not match!")
