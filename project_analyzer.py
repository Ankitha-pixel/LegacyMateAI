
from pathlib import Path

LANGUAGES = {
    ".c": "C",
    ".h": "C Header",
    ".cpp": "C++",
    ".hpp": "C++ Header",
    ".py": "Python",
    ".java": "Java",
    ".php": "PHP",
}

def analyze_project(folder_path="."):
    folder = Path(folder_path)

    if not folder.is_dir():
        print("Error: Invalid project folder.")
        return

    counts = {}
    total_lines = 0

    for file in folder.rglob("*"):
        if not file.is_file():
            continue

        if any(part in {".venv", ".git", "__pycache__"}
               for part in file.parts):
            continue

        language = LANGUAGES.get(file.suffix.lower())
        if not language:
            continue

        try:
            lines = file.read_text(
                encoding="utf-8", errors="ignore"
            ).splitlines()
        except OSError:
            continue

        counts[language] = counts.get(language, 0) + 1
        total_lines += len(lines)

    print("\n=== Project Analysis ===")
    for language, count in sorted(counts.items()):
        print(f"{language}: {count} file(s)")

    print(f"Total source lines: {total_lines}")

if __name__ == "__main__":
    analyze_project()
