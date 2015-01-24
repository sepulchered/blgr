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

    def _prepare_post(self):
        resp = None
        while resp not in ('y', 'n', ''):
            resp = input('Would you like to provide post metadata now {y/[n]}')

        if resp == 'y':
            self._ask_post_meta()

        self._create_post()

    def _ask_post_meta(self):
        post_data = {}
        post_data['title'] = input('Post title: ')
        post_data['slug'] = input('Post slug: ')
        post_data['category'] = input('Post category: ')
        self.post_data = post_data

    def _create_post(self):
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
                       'category': self.post_data.setdefault('category'),
                       'dt': dt.isoformat()}, meta)

    def _prepare_page(self):
        pass

    def prepare(self):
        if self.type == 'post':
            self._prepare_post()
        elif self.type == 'page':
            self._prepare_page()

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
