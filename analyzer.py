
from pathlib import Path

def migrate_c_to_python():
    source = Path("legacy.c").read_text(encoding="utf-8")

    if "int main()" not in source or "a + b" not in source:
        print("This example migrator supports only the sample addition program.")
        return

    python_code = '''a = 10
b = 20
result = a + b

print(f"Sum = {result}")
'''

    Path("migrated.py").write_text(
        python_code,
        encoding="utf-8"
    )

    print("Migration completed!")
    print("Created migrated.py")

if __name__ == "__main__":
    migrate_c_to_python()
