from click.testing import CliRunner

from muckrockbot import download


def test_download_cli(tmp_path):
    """Test a single download run."""
    runner = CliRunner()
    result = runner.invoke(download.cli, [])
    assert result.exit_code == 0
