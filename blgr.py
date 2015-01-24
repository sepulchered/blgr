#!/usr/bin/python3.4
import os
import json
import shutil
import datetime
import argparse


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
        resp = None
        while resp not in ('y', 'n', ''):
            resp = input('Would you like to provide post metadata now {y/[n]}')

        if resp == 'y':
            self._ask_post_meta()

    def _ask_post_meta(self):
        post_data = {}
        post_data['title'] = input('Post title: ')
        post_data['slug'] = input('Post slug: ')
        post_data['category'] = input('Post category: ')
        sl = None
        while sl not in ('y', 'n', ''):
            sl = input('Set post link in menu [False]')
        if sl == 'y':
            post_data['set_link'] = True
        elif sl in ('', 'n'):
            post_data['set_link'] = False
        self.post_data = post_data

    def execute(self):
        dt = datetime.datetime.now()
        ts = dt.strftime('%Y-%m-%d-%H')
        slug = self.post_data.setdefault('slug', 'post')
        post_dir = os.path.join(self.config['posts']['path'],
                                '-'.join((ts, slug)))
        post_name = '{}{}.{}'.format(slug, ts, 'ipynb')

        if not os.path.exists(post_dir):
            os.makedirs(post_dir)

        shutil.copyfile('./data/empty.ipynb', os.path.join(post_dir, post_name))
        with open(os.path.join(post_dir, 'meta.json'), 'w') as meta:
            json.dump({'title': self.post_data.setdefault('title', ''),
                       'slug': self.post_data.setdefault('slug', ''),
                       'category': self.post_data.setdefault('category', ''),
                       'dt': dt.isoformat(),
                       'set_link': self.post_data.setdefault('set_link', False)},
                      meta)


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
