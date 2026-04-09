import subprocess, json, tempfile, shutil
from pathlib import Path

def test_set_translation_mode_bilingual(tmp_path):
    style = tmp_path / "style-decisions.json"
    schema = Path("style-decisions.schema.json")
    # Init first
    subprocess.run(
        ["uv", "run", "python", "scripts/style_decisions.py",
         "--style", str(style), "--schema", str(schema), "init"],
        check=True
    )
    # Set bilingual mode
    subprocess.run(
        ["uv", "run", "python", "scripts/style_decisions.py",
         "--style", str(style), "--schema", str(schema),
         "set-translation-mode", "--mode", "bilingual", "--reason", "test"],
        check=True
    )
    data = json.loads(style.read_text())
    assert data["translation_mode"]["mode"] == "bilingual"
