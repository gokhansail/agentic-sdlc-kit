from budgetbook.config import DEFAULT_DATA_FILE, load_settings, parse_dotenv


def test_parse_dotenv_handles_comments_quotes_and_export():
    text = '# comment\n\nA=1\nexport B="two words"\nC=\'x\'\nnot a setting\n'
    assert parse_dotenv(text) == {"A": "1", "B": "two words", "C": "x"}


def test_defaults_without_env_file_or_variables(tmp_path):
    assert load_settings({}, tmp_path).data_file == DEFAULT_DATA_FILE


def test_env_file_is_read_from_the_given_folder(tmp_path):
    (tmp_path / ".env").write_text("BUDGETBOOK_DATA_FILE=home.json\n", encoding="utf-8")
    assert load_settings({}, tmp_path).data_file == "home.json"


def test_environment_wins_over_the_env_file(tmp_path):
    (tmp_path / ".env").write_text("BUDGETBOOK_DATA_FILE=home.json\n", encoding="utf-8")
    assert load_settings({"BUDGETBOOK_DATA_FILE": "other.json"}, tmp_path).data_file == "other.json"


def test_variables_without_the_prefix_are_ignored(tmp_path):
    (tmp_path / ".env").write_text("DATA_FILE=nope.json\n", encoding="utf-8")
    assert load_settings({"DATA_FILE": "nope2.json"}, tmp_path).data_file == DEFAULT_DATA_FILE
