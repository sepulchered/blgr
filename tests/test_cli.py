from unittest.mock import patch
from blgr.blgr import BlgrCli, Create


def test_reads_config_from_args():
    cli = BlgrCli()
    conf_file_path = 'blgr/config.json'
    cli.process_cli_args(['-c', conf_file_path, 'create'])
    assert isinstance(cli.cmd, Create)
    assert cli.cmd.cli_args['config_path'] == conf_file_path
    cli.read_config()
    assert cli.cmd.config


def test_executes_command():
    cli = BlgrCli()
    conf_file_path = 'blgr/config.json'
    cli.process_cli_args(['-c', conf_file_path, 'create'])
    with patch.object(cli.cmd, 'prepare',  return_value=None) as mock_prepare:
        with patch.object(cli.cmd, 'execute',  return_value=None) as mock_execute:
            cli.execute()

    mock_prepare.assert_called_once_with()
    mock_execute.assert_called_once()

