from blgr import BlgrCli, Create


def test_reads_config():
    cli = BlgrCli()
    conf_file_path = '../blgr/config.json'
    cli.process_cli_args(['-c', conf_file_path, 'create'])
    assert isinstance(cli.cmd, Create)
    assert cli.cmd.cli_args['config_path'] == conf_file_path
    cli.read_config()
    assert cli.cmd.config
