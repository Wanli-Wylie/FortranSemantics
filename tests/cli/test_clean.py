import sqlite3

from typer.testing import CliRunner

from forge.cli.main import app


def test_clean_resets_project_state(tmp_path, monkeypatch):
    """Ensure ``forge clean`` removes artifacts and resets the state database."""

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # Initialise project to create configuration and state database
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    forge_dir = tmp_path / ".forge"
    # Create a dummy file to emulate generated artefacts
    dummy = forge_dir / "dummy.txt"
    dummy.write_text("junk")

    # Run clean command
    result = runner.invoke(app, ["clean"])
    assert result.exit_code == 0

    # Directory should exist but dummy file removed
    assert forge_dir.is_dir()
    assert not dummy.exists()

    db_path = forge_dir / "forge.sqlite3"
    assert db_path.exists()

    # Database should contain a single project_state row in INITIALIZED state
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT project_name, fsm_status FROM project_state")
    row = cur.fetchone()
    conn.close()

    assert row == (tmp_path.name, "INITIALIZED")

    # No file records should remain
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM file_records")
    count = cur.fetchone()[0]
    conn.close()

    assert count == 0
