#!/usr/bin/python3
import os
import json
import shutil
import datetime
import argparse
import http.server
import socketserver
from subprocess import call


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
        pass

    def prepare(self):
        self.post_data = {}
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
            sl = input('Set post link in menu {y/[n]}')
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
        out_path = self.config['output']['path']
        if os.path.exists(out_path):
            shutil.rmtree(out_path)
        os.makedirs(out_path)

        posts_path = self.config['posts']['path']

        self.posts = {}
        post_dirs = (d for d in os.listdir(posts_path) if os.path.isdir(os.path.join(posts_path, d)))
        for pd in post_dirs:
            pp = os.path.join(posts_path, pd)
            with open(os.path.join(pp, 'meta.json'), 'r') as meta_file:
                meta = json.load(meta_file)
            self.posts[pp] = meta

        self.dts = {}
        self.pages = []
        for pp, data in self.posts.items():
            if not data['set_link']:
                dt = datetime.datetime.strptime(data['dt'], '%Y-%m-%dT%H:%M:%S.%f')
                self.dts.setdefault(dt.year, {}).setdefault(dt.month, {}).setdefault(dt.day, []).append(pp)
            else:
                self.pages.append(pp)

    def _generate_pages(self):
        out_path = self.config['output']['path']
        prj_path = os.path.abspath(os.path.dirname(__file__))

        for page in self.pages:
            page_path = os.path.join(out_path, self.posts[page]['slug'])
            if not os.path.exists(page_path):
                os.mkdir(page_path)

            fls = os.listdir(page)
            psts = [pst for pst in fls if pst.endswith('.ipynb')]
            pp = os.path.join(prj_path, page, psts[0])
            os.chdir(page_path)
            call(['ipython', 'nbconvert', '--to', 'html', pp, 'index.html'])
            psts_html = os.listdir('./')
            if psts_html:
                os.rename(psts_html[0], 'index.html')
            os.chdir(prj_path)

    def _generate_year_index(self, year_path, posts):
        pass

    def _generate_month_index(self, month_path, posts):
        pass

    def _generate_day_index(self, day_path, posts):
        pass

    def _generate_category_index(self, category, posts):
        pass

    def _generate_categories(self, categories):
        for cat in categories:
            cat_path = os.path.join(self.config['output']['path'], cat)
            if not os.path.exists(cat_path):
                os.mkdir(cat_path)

            self._generate_category_index(cat, categories[cat])

    def _generate_posts(self):
        out_path = self.config['output']['path']
        prj_path = os.path.abspath(os.path.dirname(__file__))
        categories = {}
        for year in self.dts:
            year_posts = []
            year_path = os.path.join(out_path, str(year))
            if not os.path.exists(year_path):
                os.mkdir(year_path)

            for month in self.dts[year]:
                month_posts = []
                month_path = os.path.join(year_path, str(month))
                if not os.path.exists(month_path):
                    os.mkdir(month_path)

                for day in self.dts[year][month]:
                    day_posts = []
                    day_path = os.path.join(month_path, str(day))
                    if not os.path.exists(day_path):
                        os.mkdir(day_path)

                    for post in self.dts[year][month][day]:
                        slug = self.posts[post]['slug']
                        slug_path = os.path.join(day_path, slug)
                        cat = self.posts[post]['category'] if self.posts[post]['category'] else 'uncategorized'
                        categories.setdefault(cat, {})['/{}/{}/{}/{}/'.format(year, month, day, slug)] = self.posts[post]
                        if not os.path.exists(slug_path):
                            os.mkdir(slug_path)

                        fls = os.listdir(post)
                        psts = [pst for pst in fls if pst.endswith('.ipynb')]
                        pp = os.path.join(prj_path, post, psts[0])
                        os.chdir(slug_path)
                        call(['ipython', 'nbconvert', '--to', 'html', pp, 'index.html'])
                        psts_html = os.listdir('./')
                        if psts_html:
                            os.rename(psts_html[0], 'index.html')
                        os.chdir(prj_path)

                    self._generate_day_index(day_path, day_posts)
                self._generate_month_index(month_path, month_posts)
            self._generate_year_index(year_path, year_posts)
        self._generate_categories(categories)

    def execute(self):
        self._generate_pages()
        self._generate_posts()




class Serve(BlgrCommand):
    _command = 'serve'

    def add_args(self):
        self.parser.add_argument('-p', '--port', type=int, default=8080,
                                 required=False, help='port on which to start '
                                                      'serving')

    def prepare(self):
        os.chdir(self.config['output']['path'])

    def execute(self):
        handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(('', self.port), handler)
        print('serving at port {}'.format(self.port))
        httpd.serve_forever()


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
