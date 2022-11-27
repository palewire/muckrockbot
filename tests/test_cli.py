from click.testing import CliRunner

from muckrockbot import download, transform


def test_download_cli(tmp_path):
    """Test a single download run."""
    runner = CliRunner()
    result = runner.invoke(download.cli, [])
    assert result.exit_code == 0


def test_transform_cli(tmp_path):
    """Test a single transform run."""
    runner = CliRunner()
    result = runner.invoke(transform.cli, [])
    assert result.exit_code == 0
