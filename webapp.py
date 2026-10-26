
from flask import Flask, render_template_string, request, send_file
from pathlib import Path
from io import BytesIO
from datetime import datetime

from migration_engine import migrate_c_to_python, verify_python_output

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

LANGUAGES = {
    "C": [".c", ".h"],
    "C++": [".cpp", ".hpp"],
    "Python": [".py"],
    "Java": [".java"],
    "PHP": [".php"],
}

latest_report = {
    "filename": "",
    "source_lang": "",
    "target_lang": "",
    "lines": 0,
    "status": "No file analyzed",
    "code": "",
    "verification": "Not run",
    "output": "",
}

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LegacyMateAI | Migration Studio</title>
<style>
* { box-sizing: border-box; }
body {
    margin: 0; font-family: Arial, sans-serif;
    background: #0b1120; color: #e5e7eb;
}
header {
    padding: 22px 7%; border-bottom: 1px solid #263247;
    display: flex; justify-content: space-between;
    align-items: center; gap: 12px;
}
.brand { color: #60a5fa; font-size: 24px; font-weight: bold; }
.tag { color: #94a3b8; font-size: 12px; }
main { max-width: 1100px; margin: 38px auto; padding: 0 18px; }
h1 { font-size: 34px; margin-bottom: 8px; }
.sub { color: #94a3b8; line-height: 1.6; }
.panel {
    background: #131e31; border: 1px solid #293850;
    border-radius: 16px; padding: 24px; margin-top: 24px;
}
.grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 18px;
}
label { display: block; margin: 12px 0 8px; color: #cbd5e1; }
select, input[type=file] {
    width: 100%; padding: 13px; border-radius: 8px;
    border: 1px solid #394b66; background: #0b1120; color: white;
}
button, .download {
    border: 0; border-radius: 9px; padding: 13px 18px;
    background: #2563eb; color: white; cursor: pointer;
    font-weight: bold; text-decoration: none;
    display: inline-block; margin-top: 18px;
}
button:hover, .download:hover { background: #1d4ed8; }
.green { background: #15803d; }
.notice {
    background: #172b45; border-left: 4px solid #60a5fa;
    padding: 14px; border-radius: 6px; margin-top: 18px;
    line-height: 1.5;
}
pre {
    background: #080d18; padding: 18px; border-radius: 10px;
    white-space: pre-wrap; overflow-wrap: anywhere; color: #86efac;
}
.status { color: #86efac; line-height: 1.6; }
footer { color: #64748b; text-align: center; padding: 28px; }
@media(max-width: 650px) {
    .grid { grid-template-columns: 1fr; }
    h1 { font-size: 27px; }
    header { padding: 18px; flex-wrap: wrap; }
}
</style>
</head>
<body>
<header>
    <div class="brand">LegacyMateAI</div>
    <div class="tag">MIGRATION STUDIO | PROTOTYPE</div>
</header>

<main>
    <h1>Modernize your legacy code.</h1>
    <p class="sub">
        Analyze legacy code, generate a Python conversion for supported
        C examples, execute the generated Python, and download a report.
    </p>

    <section class="panel">
        <h2>01 / Source configuration</h2>

        <form method="POST" enctype="multipart/form-data">
            <label for="codefile">Upload source code</label>
            <input type="file" id="codefile" name="codefile"
                accept=".c,.h,.cpp,.hpp,.py,.java,.php" required>

            <div class="grid">
                <div>
                    <label for="source">Source language</label>
                    <select id="source" name="source" required>
                        {% for lang in languages %}
                        <option value="{{ lang }}"
                        {% if source_lang == lang %}selected{% endif %}>
                            {{ lang }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label for="target">Target language</label>
                    <select id="target" name="target" required>
                        {% for lang in languages %}
                        <option value="{{ lang }}"
                        {% if target_lang == lang %}selected{% endif %}>
                            {{ lang }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
            </div>

            <button type="submit">Analyze &amp; Migrate</button>
        </form>

        <div class="notice">
            <strong>Current support:</strong>
            The connected migration engine supports a limited set of
            simple C assignments, arithmetic expressions, and printf
            statements converted to Python. Other language pairs are
            not yet implemented.
        </div>
    </section>

    {% if message %}
    <section class="panel">
        <h2>02 / Migration results</h2>
        <p class="status">{{ message }}</p>

        {% if filename %}
        <p><strong>File:</strong> {{ filename }}</p>
        <p><strong>Source language:</strong> {{ source_lang }}</p>
        <p><strong>Target language:</strong> {{ target_lang }}</p>
        <p><strong>Lines of code:</strong> {{ lines }}</p>
        {% endif %}

        {% if code %}
        <h3>Generated Python code</h3>
        <pre>{{ code }}</pre>
        <h3>Execution verification</h3>
        <pre>{{ verification }}</pre>
        {% if output %}
        <h3>Program output</h3>
        <pre>{{ output }}</pre>
        {% endif %}
        {% endif %}

        {% if filename %}
        <a class="download green" href="/download-report">
            Download Migration Report
        </a>
        {% endif %}
    </section>
    {% endif %}
</main>

<footer>LegacyMateAI | AI-assisted legacy code modernization</footer>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    context = {
        "languages": list(LANGUAGES.keys()),
        "source_lang": "C",
        "target_lang": "Python",
        "message": None,
        "filename": None,
        "lines": None,
        "code": None,
        "verification": "Not run",
        "output": "",
    }

    if request.method == "POST":
        uploaded = request.files.get("codefile")
        source_lang = request.form.get("source", "C")
        target_lang = request.form.get("target", "Python")

        context.update({
            "source_lang": source_lang,
            "target_lang": target_lang,
        })

        if not uploaded or not uploaded.filename:
            context["message"] = "Please select a source file."
            return render_template_string(PAGE, **context)

        filename = Path(uploaded.filename).name
        extension = Path(filename).suffix.lower()

        if source_lang not in LANGUAGES or target_lang not in LANGUAGES:
            context["message"] = "Please select valid languages."
            return render_template_string(PAGE, **context)

        if extension not in LANGUAGES[source_lang]:
            context["message"] = (
                "The selected source language does not match "
                "the uploaded file extension."
            )
            return render_template_string(PAGE, **context)

        try:
            content = uploaded.stream.read().decode("utf-8")
        except UnicodeDecodeError:
            context["message"] = "Please upload a UTF-8 text file."
            return render_template_string(PAGE, **context)

        lines = len(content.splitlines())
        generated = ""
        verification = "Not run"
        output = ""

        status = (
            "File analyzed. Migration is not implemented "
            "for this language pair yet."
        )

        if source_lang == "C" and target_lang == "Python":
            try:
                generated = migrate_c_to_python(content)
                passed, program_output, error = verify_python_output(generated)

                if passed:
                    verification = "PASS"
                    output = program_output
                    status = (
                        "Python code generated and executed successfully. "
                        "This is not proof of full behavioral equivalence."
                    )
                else:
                    verification = "FAIL"
                    output = error or program_output
                    status = "Generated code failed execution verification."

            except (ValueError, SyntaxError) as error:
                verification = "NOT COMPLETED"
                status = f"Migration could not be completed: {error}"

        latest_report.update({
            "filename": filename,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "lines": lines,
            "status": status,
            "code": generated,
            "verification": verification,
            "output": output,
        })

        context.update({
            "message": status,
            "filename": filename,
            "lines": lines,
            "code": generated,
            "verification": verification,
            "output": output,
        })

    return render_template_string(PAGE, **context)


@app.route("/download-report")
def download_report():
    report_text = f"""
========================================
          LEGACYMATEAI REPORT
========================================

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Source file: {latest_report["filename"] or "No file analyzed"}
Source language: {latest_report["source_lang"] or "Not selected"}
Target language: {latest_report["target_lang"] or "Not selected"}
Lines of code: {latest_report["lines"]}
Migration status: {latest_report["status"]}
Execution verification: {latest_report["verification"]}
Program output: {latest_report["output"]}

Generated code:
{latest_report["code"] or "No code generated"}

Limitations:
This prototype supports only a limited set of C-to-Python examples.
A successful execution does not prove equivalent behavior.
Differential testing, automatic repair, and other language pairs
remain future development work.

========================================
"""

    report_file = BytesIO(report_text.encode("utf-8"))
    report_file.seek(0)

    return send_file(
        report_file,
        mimetype="text/plain; charset=utf-8",
        as_attachment=True,
        download_name="migration_report.txt",
    )


if __name__ == "__main__":
    app.run(debug=True)
