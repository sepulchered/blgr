#!/usr/bin/python3.4
import argparse


class Command(type):
    def __init__(cls, *args, **kwargs):
        if not hasattr(cls, 'commands'):
            cls.commands = {}
        else:
            cls.commands[cls._command] = cls


class BlgrCommand(metaclass=Command):
    def __init__(self, args):
        super().__init__()
        self._process_args(args)
        self._prepare()

    def _process_args(self, args):
        self.parser = argparse.ArgumentParser(description='blgr {}'.format(self._command))
        self._add_args()
        self.parser.parse_args(args, namespace=self)

    def _add_args(self):
        raise NotImplementedError

    def _prepare(self):
        raise NotImplementedError

    def execute(self):
        raise NotImplementedError


class Create(BlgrCommand):
    _command = 'create'

    def _add_args(self):
        self.parser.add_argument('item', metavar='ITEM', help='item to create')

    def _prepare(self):
        pass

    def execute(self):
        pass


class BlgrCli():
    def __init__(self):
        self._process_args()
        self._process_command()

    def _process_args(self):
        self.parser = argparse.ArgumentParser(description='blgr cli')
        self.parser.add_argument('command', metavar='COMMAND',
                                 help='blgr command to execute',
                                 choices=[cmd for cmd in BlgrCommand.commands])
        _, self.command_args = self.parser.parse_known_args(namespace=self)

    def _process_command(self):
        if self.command not in BlgrCommand.commands:
            self.parser.error('invalid command "{}" provided'.format(self.command))

        cmd = BlgrCommand.commands[self.command](self.command_args)
        cmd.execute()


if __name__ == '__main__':
    blgr = BlgrCli()
