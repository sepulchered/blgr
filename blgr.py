#!/usr/bin/python3.4
import argparse
import json


class Command(type):
    def __init__(cls, *args, **kwargs):
        if not hasattr(cls, 'commands'):
            cls.commands = {}
        else:
            cls.commands[cls._command] = cls()


class BlgrCommand(metaclass=Command):
    def __init__(self):
        super().__init__()
        self.parser = None
        self.config = None

    def add_args(self):
        raise NotImplementedError

    def prepare(self):
        raise NotImplementedError

    def execute(self):
        raise NotImplementedError


class Create(BlgrCommand):
    _command = 'create'

    def add_args(self):
        self.parser.add_argument('type', metavar='TYPE', help='type of item to create',
                                 choices=['post', 'page'])

    def prepare(self):
        pass

    def execute(self):
        pass


class Generate(BlgrCommand):
    _command = 'generate'

    def add_args(self):
        pass

    def prepare(self):
        pass

    def execute(self):
        pass


class BlgrCli():
    def __init__(self):
        self._read_config()
        self._process()

    def _read_config(self):
        config = None
        with open('config.json', 'r') as conf:
            config = json.load(conf)

        self.config = config

    def _process(self):
        parser = argparse.ArgumentParser(description='blgr cli')

        subparsers = parser.add_subparsers(help='command')
        for name, cmd in BlgrCommand.commands.items():
            cmd.parser = subparsers.add_parser(name)
            cmd.add_args()
            cmd.parser.set_defaults(cmd=cmd)
        args = parser.parse_args()
        cmd = args.cmd
        parser.parse_args(namespace=cmd)

        cmd.config = self.config
        cmd.prepare()
        cmd.execute()

if __name__ == '__main__':
    blgr = BlgrCli()
