#!/usr/bin/python3
import os
import json
import shutil
import datetime
import argparse
import http.server
import socketserver
from subprocess import call

import jinja2
from bs4 import BeautifulSoup


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

        comments = None
        while comments not in ('y', 'n', ''):
            comments = input('Allow comments {[y]/n}')
        if comments == 'n':
            post_data['comments'] = False
        elif comments in ('', 'y'):
            post_data['comments'] = True
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
                       'comments': self.post_data.setdefault('comments', False),
                       'set_link': self.post_data.setdefault('set_link', False)},
                      meta)


class Generate(BlgrCommand):
    _command = 'generate'

    def add_args(self):
        pass

    def prepare(self):
        self.prj_path = os.path.abspath(os.path.dirname(__file__))
        self.out_path = self.config['output']['path']
        jinja_loader = jinja2.FileSystemLoader(searchpath=os.path.join(self.prj_path, 'data/templates/'))
        self.tmpl_env = jinja2.Environment(loader=jinja_loader)
        if os.path.exists(self.out_path):
            shutil.rmtree(self.out_path)
        os.makedirs(self.out_path)

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

    def _generate_main_indices(self, posts):
        tmpl = self.tmpl_env.get_template('index.html')
        main_indx_path = os.path.join(self.out_path, 'index.html')
        main_indx = tmpl.render({'header': 'Main index', 'posts': posts, 'pages': self.menu_pages})
        with open(main_indx_path, 'w') as indx:
            indx.write(main_indx)

    def _generate_pages(self):
        for page in self.pages:
            page_path = os.path.join(self.out_path, self.posts[page]['slug'])
            if not os.path.exists(page_path):
                os.mkdir(page_path)

            fls = os.listdir(page)
            psts = [pst for pst in fls if pst.endswith('.ipynb')]
            pp = os.path.join(self.prj_path, page, psts[0])
            self._process_ipynb(page_path, pp)

    def _generate_comments(self):
        tmpl = self.tmpl_env.get_template('comments.html')
        self.comments = tmpl.render({'disqus': self.config['disqus']})

    def _generate_menu(self):
        self.menu_pages = []
        for page in self.pages:
            pd = self.posts[page]
            pd['url'] = '/{}/'.format(pd['slug'])
            self.menu_pages.append(pd)
        tmpl = self.tmpl_env.get_template('menu.html')
        self.menu = tmpl.render({'pages': self.menu_pages})

    def _generate_year_index(self, year_path, posts, year):
        indx_path = os.path.join(year_path, 'index.html')
        tmpl = self.tmpl_env.get_template('index.html')
        indx = tmpl.render({'header': 'Year {}'.format(year), 'posts': posts})
        with open(indx_path, 'w') as cindex:
            cindex.write(indx)

    def _generate_month_index(self, month_path, posts, year_month):
        indx_path = os.path.join(month_path, 'index.html')
        tmpl = self.tmpl_env.get_template('index.html')
        indx = tmpl.render({'header': 'Year {} Month {}'.format(year_month[0], year_month[1]),
                            'posts': posts, 'pages': self.menu_pages})
        with open(indx_path, 'w') as cindex:
            cindex.write(indx)

    def _generate_day_index(self, day_path, posts, year_month_day):
        indx_path = os.path.join(day_path, 'index.html')
        tmpl = self.tmpl_env.get_template('index.html')
        indx = tmpl.render({'header': 'Year {} Month {} Day {}'.format(year_month_day[0], year_month_day[1],
                                                                       year_month_day[2]),
                            'posts': posts, 'pages': self.menu_pages})
        with open(indx_path, 'w') as cindex:
            cindex.write(indx)

    def _generate_category_index(self, category, cat_path, posts):
        indx_path = os.path.join(cat_path, 'index.html')
        tmpl = self.tmpl_env.get_template('index.html')
        indx = tmpl.render({'header': category, 'posts': posts, 'pages': self.menu_pages})
        with open(indx_path, 'w') as cindex:
            cindex.write(indx)

    def _generate_categories(self, categories):
        for cat in categories:
            cat_path = os.path.join(self.config['output']['path'], cat)
            if not os.path.exists(cat_path):
                os.mkdir(cat_path)

            self._generate_category_index(cat, cat_path, categories[cat])

    def _process_ipynb(self, out_path, post_path, comments=False):
        os.chdir(out_path)
        call(['ipython', 'nbconvert', '--to', 'html', post_path])
        psts_html = os.listdir('./')
        if psts_html:
            os.rename(psts_html[0], 'index.html')

        os.chdir(self.prj_path)
        self._append_html(os.path.join(out_path, 'index.html'), comments)

    def _append_html(self, path, comments):
        soup = BeautifulSoup(open(path))

        menu = BeautifulSoup(self.menu)
        comments_div = soup.find(id='notebook-container')
        soup.body.insert(0, menu)
        if comments:
            comments = BeautifulSoup(self.comments)
            comments_div.append(comments)
        res = soup.prettify()
        with open(path, 'w') as pg:
            pg.write(res)

    def _generate_posts(self):
        all_posts = []
        categories = {}
        for year in self.dts:
            year_posts = []
            year_path = os.path.join(self.out_path, str(year))
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
                        pd = {'url': '/{}/{}/{}/{}/'.format(year, month, day, slug)}
                        pd.update(self.posts[post])
                        categories.setdefault(cat, []).append(pd)
                        if not os.path.exists(slug_path):
                            os.mkdir(slug_path)

                        fls = os.listdir(post)
                        psts = [pst for pst in fls if pst.endswith('.ipynb')]
                        pp = os.path.join(self.prj_path, post, psts[0])
                        self._process_ipynb(slug_path, pp, pd['comments'])
                        all_posts.append(pd)


                    day_posts.append(pd)
                    month_posts.append(pd)
                    year_posts.append(pd)

                    self._generate_day_index(day_path, day_posts, (year, month, day))
                self._generate_month_index(month_path, month_posts, (year, month))
            self._generate_year_index(year_path, year_posts, year)
        self._generate_categories(categories)
        self._generate_main_indices(all_posts)

    def execute(self):
        self._generate_menu()
        self._generate_comments()
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
    def process_cli_args(self, cli_args=None):
        parser = argparse.ArgumentParser(description='blgr cli')
        parser.add_argument('-c', '--config_path', default='config.json', required=True, help='path to config file')

        subparsers = parser.add_subparsers(help='command')
        for name, cmd in BlgrCommand.commands.items():
            cmd.parser = subparsers.add_parser(name)
            cmd.add_args()
            cmd.parser.set_defaults(cmd=cmd)
        if cli_args:
            args = parser.parse_args(cli_args)
        else:
            args = parser.parse_args()
        if hasattr(args, 'cmd'):
            self.cmd = args.cmd
            self.cmd.cli_args = vars(args)

    def read_config(self):
        cfg = {}
        with open(self.cmd.cli_args['config_path'], 'r') as cfgf:
            cfg = json.load(cfgf)
        self.cmd.config = cfg

    def execute(self):
        self.cmd.prepare()
        self.cmd.execute()

if __name__ == '__main__':
    blgr = BlgrCli()
    blgr.process_cli_args()
    blgr.read_config()
    blgr.execute()

