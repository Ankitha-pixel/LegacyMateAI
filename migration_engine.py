
import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def migrate_c_to_python(c_code):
    """
    Prototype migration engine for simple C integer assignments,
    arithmetic expressions, and printf statements.
    """

    if "int main" not in c_code:
        raise ValueError("Could not find a C main function.")

    # Extract simple integer variable assignments.
    assignments = re.findall(
        r"\bint\s+([A-Za-z_]\w*)\s*=\s*(-?\d+)\s*;",
        c_code
    )

    if not assignments:
        raise ValueError(
            "No supported integer assignments were found."
        )

    python_lines = []
    variables = set()

    for name, value in assignments:
        python_lines.append(f"{name} = {value}")
        variables.add(name)

    # Convert simple arithmetic assignments such as result = a + b.
    arithmetic = re.findall(
        r"\bint\s+([A-Za-z_]\w*)\s*=\s*"
        r"([A-Za-z_]\w*|\d+)\s*"
        r"([+\-*/])\s*"
        r"([A-Za-z_]\w*|\d+)\s*;",
        c_code
    )

    for name, left, operator, right in arithmetic:
        if left in variables or left.lstrip("-").isdigit():
            if right in variables or right.lstrip("-").isdigit():
                python_lines.append(
                    f"{name} = {left} {operator} {right}"
                )
                variables.add(name)

    # Support simple printf statements with a single variable.
    printf_match = re.search(
        r'printf\s*\(\s*"([^"]*)"\s*,\s*'
        r'([A-Za-z_]\w*)\s*\)\s*;',
        c_code
    )

    if printf_match:
        format_string, variable = printf_match.groups()

        if variable not in variables:
            raise ValueError(
                f"Cannot print undefined variable: {variable}"
            )

        format_string = format_string.replace(r"\n", "")
        format_string = format_string.replace("%d", "{}")

        python_lines.append(
            f'print({format_string!r}.format({variable}))'
        )
    else:
        # Support printf with a plain string and no arguments.
        plain_print = re.search(
            r'printf\s*\(\s*"([^"%]*)"\s*\)\s*;',
            c_code
        )

        if plain_print:
            message = plain_print.group(1).replace(r"\n", "")
            python_lines.append(f"print({message!r})")
        else:
            raise ValueError(
                "This prototype requires a supported printf statement."
            )

    generated_code = "\n".join(python_lines) + "\n"

    # Validate generated Python syntax before returning it.
    ast.parse(generated_code)

    return generated_code


def verify_python_output(python_code):
    """
    Execute generated Python with a timeout and capture its output.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = Path(temp_dir) / "migrated.py"
        script_path.write_text(python_code, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, "-I", str(script_path)],
                capture_output=True,
                text=True,
                timeout=3,
                cwd=temp_dir,
                check=False
            )
        except subprocess.TimeoutExpired:
            return False, "", "Execution timed out."

        if result.returncode != 0:
            return False, result.stdout, result.stderr.strip()

        return True, result.stdout.strip(), ""


if __name__ == "__main__":
    sample_c = """
    #include <stdio.h>
    int main() {
        int a = 10;
        int b = 20;
        int result = a + b;
        printf("Sum = %d\\n", result);
        return 0;
    }
    """

    try:
        converted = migrate_c_to_python(sample_c)
        print("Generated Python code:")
        print(converted)

        passed, output, error = verify_python_output(converted)

        print("Verification:", "PASS" if passed else "FAIL")
        print("Output:", output)

        if error:
            print("Error:", error)

    except (ValueError, SyntaxError) as error:
        print("Migration failed:", error)
