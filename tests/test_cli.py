import json
from logminer.cli import main

LOGS = (
    "User alice logged in from 10.0.0.1\n"
    "User bob logged in from 10.0.0.2\n"
    "Disk usage at 80 percent\n"
)


def test_cli_text_output(tmp_path, capsys):
    f = tmp_path / "app.log"
    f.write_text(LOGS)
    code = main([str(f)])
    out = capsys.readouterr().out
    assert code == 0
    assert "User <*> logged in from <IP>" in out
    assert out.splitlines()[0].lstrip().startswith("2")   # most frequent first


def test_cli_json_and_top(tmp_path, capsys):
    f = tmp_path / "app.log"
    f.write_text(LOGS)
    code = main([str(f), "--json", "--top", "1"])
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    assert len(data) == 1 and data[0]["count"] == 2


def test_cli_empty_input(tmp_path, capsys):
    f = tmp_path / "empty.log"
    f.write_text("")
    assert main([str(f)]) == 0
    assert "no log lines" in capsys.readouterr().out


def test_cli_save_writes_reloadable_model(tmp_path, capsys):
    from logminer import TemplateMiner
    f = tmp_path / "app.log"
    f.write_text(LOGS)
    model = tmp_path / "model.json"
    assert main([str(f), "--save", str(model)]) == 0
    # the saved model reloads and classifies a fresh line
    restored = TemplateMiner.from_json(model.read_text())
    assert restored.match("User dave logged in from 10.0.0.9") is not None
