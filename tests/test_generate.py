import os
import json
import shutil
import datetime
from unittest import mock

import jinja2
from bs4 import BeautifulSoup

from blgr.blgr import Generate


def test_prepare():
    generate = Generate()

    with mock.patch.object(generate, '_generate_out_path') as mock_out_path:
        with mock.patch.object(generate, '_generate_posts_dict') as mock_posts_dict:
            with mock.patch.object(generate, '_generate_pages_dts') as mock_pages_dts:
                generate.prepare()

    mock_out_path.assert_called_once_with()
    mock_posts_dict.assert_called_once_with()
    mock_pages_dts.assert_called_once_with()

    assert hasattr(generate, 'prj_path')
    assert generate.prj_path
    assert hasattr(generate, 'tmpl_env')
    assert isinstance(generate.tmpl_env, jinja2.Environment)


def test_out_path():
    generate = Generate()
    conf = {'output': {'path': './output'}}
    generate.config = conf

    generate._generate_out_path()
    assert os.path.exists(generate.out_path)
    shutil.rmtree(generate.out_path)

    os.makedirs(generate.out_path)
    generate._generate_out_path()
    assert os.path.exists(generate.out_path)
    shutil.rmtree(generate.out_path)


def test_posts_dict():
    generate = Generate()
    conf = {'posts': {'path': './posts'}}
    generate.config = conf

    # prepare fake post
    dt = datetime.datetime.now()
    ts = dt.isoformat()
    fake_post_path = os.path.join(conf['posts']['path'], 'test-post')
    fake_post_meta = {'title': 'fake post', 'slug': 'fake-post', 'category': 'fake category',
                      'set_link': False, 'comments': False, 'dt': ts}
    fake_post = {fake_post_path: fake_post_meta}
    os.makedirs(fake_post_path)
    with open(os.path.join(fake_post_path, 'meta.json'), 'w') as meta_file:
        json.dump(fake_post_meta, meta_file)

    generate._generate_posts_dict()

    assert generate.posts
    assert fake_post_path in generate.posts
    for k in fake_post_meta:
        assert k in generate.posts[fake_post_path]
        assert fake_post_meta[k] == generate.posts[fake_post_path][k]

    # clean test data
    shutil.rmtree(conf['posts']['path'])


def test_pages_dts():
    generate = Generate()

    dt1 = datetime.datetime.now()
    dt2 = dt1 - datetime.timedelta(400)  # another year
    dt3 = dt1 + datetime.timedelta(35)  # another month

    fake_posts = {
        'fake_path1': {
            'dt': dt1.isoformat(),
            'set_link': False
        },
        'fake_path2': {
            'dt': dt2.isoformat(),
            'set_link': False
        },
        'fake_path3': {
            'dt': dt3.isoformat(),
            'set_link': True
        }
    }

    generate.posts = fake_posts

    generate._generate_pages_dts()

    assert len(generate.pages) == 1
    assert 'fake_path3' in generate.pages

    # for we don't include page in dts dt3 is not in generate.dts
    assert dt1.year in generate.dts
    assert dt2.year in generate.dts
    assert dt1.month in generate.dts[dt1.year]
    assert dt2.month in generate.dts[dt2.year]
    assert dt1.day in generate.dts[dt1.year][dt1.month]
    assert dt2.day in generate.dts[dt2.year][dt2.month]
    assert 'fake_path1' in generate.dts[dt1.year][dt1.month][dt1.day]
    assert 'fake_path2' in generate.dts[dt2.year][dt2.month][dt2.day]


def test_main_index():
    out_path = 'output/'
    os.makedirs(out_path)

    template_path = 'templates/'
    os.makedirs(template_path)
    with open(os.path.join(template_path, 'index.html'), 'w') as main_index_template:
        main_index_template.write('{{header}}-{{posts}}-{{pages}}')

    fake_vars = {'header': 'fake_header', 'posts': 'fake_posts', 'pages': 'fake_pages'}

    generate = Generate()
    generate.out_path = out_path
    jloader = jinja2.FileSystemLoader(searchpath=template_path)
    generate.tmpl_env = jinja2.Environment(loader=jloader)
    generate.menu_pages = fake_vars['pages']

    generate._generate_main_index(fake_vars['posts'], header=fake_vars['header'])
    assert os.path.exists(os.path.join(out_path, 'index.html'))
    rendered = False
    with open(os.path.join(out_path, 'index.html'), 'r') as rtmpl:
        rendered = rtmpl.read()
    assert rendered == '{header}-{posts}-{pages}'.format(**fake_vars)

    if os.path.exists(template_path):
        shutil.rmtree(template_path)
    if os.path.exists(out_path):
        shutil.rmtree(out_path)


def test_pages():
    generate = Generate()

    dt1 = datetime.datetime.now()
    dt2 = dt1 - datetime.timedelta(400)  # another year
    dt3 = dt1 + datetime.timedelta(35)  # another month
    fake_pages = {
        'fake_path1': {
            'dt': dt1.isoformat(),
            'set_link': True,
            'slug': 'fake_slug1'
        },
        'fake_path2': {
            'dt': dt2.isoformat(),
            'set_link': True,
            'slug': 'fake_slug2'
        },
        'fake_path3': {
            'dt': dt3.isoformat(),
            'set_link': True,
            'slug': 'fake_slug3'
        }
    }
    generate.posts = fake_pages
    generate.pages = [path for path in fake_pages]
    # generate.config = {'output': {'path': 'output/'}}
    generate.out_path = 'output/'
    os.makedirs(generate.out_path)
    for path in fake_pages:
        os.makedirs(path)
        with open(os.path.join(path, 'fake_post.ipynb'), 'w') as fake_post:
            fake_post.write('fake_data')

    with mock.patch.object(generate, '_process_ipynb') as mock_ipynb:
        generate._generate_pages()

    mock_ipynb.assert_called()

    if os.path.exists(generate.out_path):
        shutil.rmtree(generate.out_path)
    for path in fake_pages:
        if os.path.exists(path):
            shutil.rmtree(path)


def test_comments():
    template_path = 'templates/'
    config = {'disqus': 'fake_disqus_id'}

    generate = Generate()
    jloader = jinja2.FileSystemLoader(searchpath=template_path)
    generate.tmpl_env = jinja2.Environment(loader=jloader)
    generate.config = config

    os.makedirs(template_path)
    with open(os.path.join(template_path, 'comments.html'), 'w') as comments_template:
        comments_template.write('{{disqus}}')

    generate._generate_comments()

    assert generate.comments == config['disqus']

    if os.path.exists(template_path):
        shutil.rmtree(template_path)


def test_menu():
    template_path = 'templates/'
    os.makedirs(template_path)
    with open(os.path.join(template_path, 'menu.html'), 'w') as comments_template:
        comments_template.write("{% for page in pages %}{{page['slug']}}{% endfor %}")

    fake_posts = {
        'fake_path1': {
            'set_link': True,
            'slug': 'fake_slug1'
        }
    }
    fake_pages = [k for k in fake_posts]

    generate = Generate()
    generate.posts = fake_posts
    generate.pages = fake_pages

    jloader = jinja2.FileSystemLoader(searchpath=template_path)
    generate.tmpl_env = jinja2.Environment(loader=jloader)

    generate._generate_menu()

    for data in fake_posts.values():
        data['url'] = '/{}/'.format(data['slug'])
    assert generate.menu_pages == [data for data in fake_posts.values()]
    assert generate.menu == ''.join((data['slug'] for data in fake_posts.values()))

    if os.path.exists(template_path):
        shutil.rmtree(template_path)


def test_year_index():
    template_path = 'templates/'
    os.makedirs(template_path)
    with open(os.path.join(template_path, 'index.html'), 'w') as comments_template:
        comments_template.write("{{header}}{% for post in posts %}{{post['slug']}}{% endfor %}")

    year = 2015
    header = 'header'
    output_path = 'output/'
    year_path = os.path.join(output_path, '{}/'.format(year))
    os.makedirs(year_path)
    fake_posts = [
        {
            'slug': 'fake_slug1'
        }
    ]

    generate = Generate()
    jloader = jinja2.FileSystemLoader(searchpath=template_path)
    generate.tmpl_env = jinja2.Environment(loader=jloader)

    generate._generate_year_index(year_path, fake_posts, year, header)

    assert os.path.exists(os.path.join(year_path, 'index.html'))

    data = None
    fake_data = '{header}{slug}'.format(header=header, slug=fake_posts[0]['slug'])
    with open(os.path.join(year_path, 'index.html'), 'r') as year_indx_template:
        data = year_indx_template.read()

    assert data is not None
    assert data == fake_data

    if os.path.exists(template_path):
        shutil.rmtree(template_path)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)


def test_month_index():
    template_path = 'templates/'
    os.makedirs(template_path)
    with open(os.path.join(template_path, 'index.html'), 'w') as comments_template:
        comments_template.write("{{header}}{% for post in posts %}{{post['slug']}}{% endfor %}")

    year = 2015
    month = 5
    header = 'header'
    output_path = 'output/'
    month_path = os.path.join(output_path, '{}/{}/'.format(year, month))
    os.makedirs(month_path)
    fake_posts = [
        {
            'slug': 'fake_slug1'
        }
    ]

    generate = Generate()
    jloader = jinja2.FileSystemLoader(searchpath=template_path)
    generate.tmpl_env = jinja2.Environment(loader=jloader)

    generate._generate_month_index(month_path, fake_posts, (year, month), header)

    assert os.path.exists(os.path.join(month_path, 'index.html'))

    data = None
    fake_data = '{header}{slug}'.format(header=header, slug=fake_posts[0]['slug'])
    with open(os.path.join(month_path, 'index.html'), 'r') as month_indx_template:
        data = month_indx_template.read()

    assert data is not None
    assert data == fake_data

    if os.path.exists(template_path):
        shutil.rmtree(template_path)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)


def test_day_index():
    template_path = 'templates/'
    os.makedirs(template_path)
    with open(os.path.join(template_path, 'index.html'), 'w') as comments_template:
        comments_template.write("{{header}}{% for post in posts %}{{post['slug']}}{% endfor %}")

    year = 2015
    month = 5
    day = 17
    header = 'header'
    output_path = 'output/'
    day_path = os.path.join(output_path, '{}/{}/{}/'.format(year, month, day))
    os.makedirs(day_path)
    fake_posts = [
        {
            'slug': 'fake_slug1'
        }
    ]

    generate = Generate()
    jloader = jinja2.FileSystemLoader(searchpath=template_path)
    generate.tmpl_env = jinja2.Environment(loader=jloader)

    generate._generate_day_index(day_path, fake_posts, (year, month, day), header)

    assert os.path.exists(os.path.join(day_path, 'index.html'))

    data = None
    fake_data = '{header}{slug}'.format(header=header, slug=fake_posts[0]['slug'])
    with open(os.path.join(day_path, 'index.html'), 'r') as day_indx_template:
        data = day_indx_template.read()

    assert data is not None
    assert data == fake_data

    if os.path.exists(template_path):
        shutil.rmtree(template_path)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)


def test_category_index():
    template_path = 'templates/'
    os.makedirs(template_path)
    with open(os.path.join(template_path, 'index.html'), 'w') as comments_template:
        comments_template.write("{{header}}{% for post in posts %}{{post['slug']}}{% endfor %}")

    header = 'header'
    category = 'fake_cat'
    output_path = 'output/'
    cat_path = os.path.join(output_path, '{}'.format(category))
    os.makedirs(cat_path)
    fake_posts = [
        {
            'slug': 'fake_slug1'
        }
    ]

    generate = Generate()
    jloader = jinja2.FileSystemLoader(searchpath=template_path)
    generate.tmpl_env = jinja2.Environment(loader=jloader)

    generate._generate_category_index(category, cat_path, fake_posts, header)

    assert os.path.exists(os.path.join(cat_path, 'index.html'))

    data = None
    fake_data = '{header}{slug}'.format(header=header, slug=fake_posts[0]['slug'])
    with open(os.path.join(cat_path, 'index.html'), 'r') as cat_indx_template:
        data = cat_indx_template.read()

    assert data is not None
    assert data == fake_data

    if os.path.exists(template_path):
        shutil.rmtree(template_path)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)


def test_generate_categories():
    generate = Generate()
    config = {'output': {'path': 'output/'}}
    os.makedirs(config['output']['path'])
    generate.config = config
    categories = {'fake_cat1': None, 'fake_cat2': None, 'fake_cat3': None}
    cats = (os.path.join(config['output']['path'], cat) for cat in categories)

    with mock.patch.object(generate, '_generate_category_index') as mock_gen_cat:
        generate._generate_categories(categories)

    mock_gen_cat.assert_called()

    for cat in cats:
        assert os.path.exists(cat)

    if os.path.exists(config['output']['path']):
        shutil.rmtree(config['output']['path'])


def test_process_ipynb():
    generate = Generate()
    generate.prj_path = os.path.dirname(os.path.abspath(__file__))

    out_path = os.path.join(generate.prj_path, 'output/')
    os.makedirs(out_path)
    posts_path = os.path.join(generate.prj_path, 'post/')
    os.makedirs(posts_path)
    post_path = os.path.join(posts_path, 'post.ipynb')
    ipynb = {
        "metadata": {
            "name": "",
            "signature": ""
        },
        "nbformat": 3,
        "nbformat_minor": 0,
        "worksheets": [
            {
                "cells": [],
                "metadata": {}
            }
        ]
    }
    with open(post_path, 'w') as post:
        json.dump(ipynb, post)

    with mock.patch.object(generate, '_append_html') as mock_append_html:
        generate._process_ipynb(out_path, post_path, True)
    mock_append_html.assert_called_once_with(os.path.join(out_path, 'index.html'), True)

    assert os.path.exists(os.path.join(out_path, 'index.html'))

    if os.path.exists(out_path):
        shutil.rmtree(out_path)
    if os.path.exists(posts_path):
        shutil.rmtree(posts_path)


def test_append_html():
    generate = Generate()
    fake_comments = 'fake_comments'
    comments = '<div id="fake_comments">%s</div>' % fake_comments
    fake_menu = 'fake_menu'
    menu = '<div id="fake_menu">%s</div>' % fake_menu
    generate.comments = comments
    generate.menu = menu

    out_path = 'output/'
    os.makedirs(out_path)
    path = os.path.join(out_path, 'test.html')
    with open(path, 'w') as fake_html:
        fake_html.write('<!doctype html><html><body><div id="notebook-container"></div></body></html>')

    generate._append_html(path, False)
    with open(path, 'r') as fake_html:
        soup = BeautifulSoup(fake_html)
        menu = soup.find(id='fake_menu')
        comments = soup.find(id='fake_comments')

        assert menu is not None
        assert menu.string.strip() == fake_menu
        assert comments is None

    generate._append_html(path, True)
    with open(path, 'r') as fake_html:
        soup = BeautifulSoup(fake_html)
        menu = soup.find(id='fake_menu')
        comments = soup.find(id='fake_comments')

        assert menu is not None
        assert menu.string.strip() == fake_menu
        assert comments is not None
        assert comments.string.strip() == fake_comments

    if os.path.exists(out_path):
        shutil.rmtree(out_path)


def test_generate_post():
    generate = Generate()

    fake_post1 = 'fake_post1'
    fake_post2 = 'fake_post2'
    fake_day_path = 'output/day/'
    fake_prj_path = 'output'
    fake_slug = 'fake_slug'
    fake_category = 'fake_category'
    fake_posts = {
        fake_post1: {'slug': fake_slug, 'category': fake_category, 'comments': False},
        fake_post2: {'slug': fake_slug, 'comments': True}
    }
    fake_date = {'year': 2015, 'month': 3, 'day': 22}
    fake_categories = {}
    os.makedirs(fake_day_path)
    os.makedirs(fake_post1)
    os.makedirs(fake_post2)
    ipynb = {
        "metadata": {
            "name": "",
            "signature": ""
        },
        "nbformat": 3,
        "nbformat_minor": 0,
        "worksheets": [
            {
                "cells": [],
                "metadata": {}
            }
        ]
    }

    with open(os.path.join(fake_post1, 'test.ipynb'), 'w') as nb:
        json.dump(ipynb, nb)
    with open(os.path.join(fake_post2, 'test.ipynb'), 'w') as nb:
        json.dump(ipynb, nb)

    generate.posts = fake_posts
    generate.prj_path = fake_prj_path

    with mock.patch.object(generate, '_process_ipynb') as mock_process_ipynb:
        pd = generate._generate_post(fake_post1, fake_day_path, fake_categories, **fake_date)

    mock_process_ipynb.assert_called_once_with(os.path.join(fake_day_path, fake_slug),
                                               os.path.join(fake_prj_path, fake_post1, 'test.ipynb'),
                                               False)
    assert pd['url'] == '/{}/{}/{}/{}/'.format(fake_date['year'], fake_date['month'],
                                               fake_date['day'], fake_slug)
    assert fake_category in fake_categories.keys()

    with mock.patch.object(generate, '_process_ipynb') as mock_process_ipynb:
        pd = generate._generate_post(fake_post2, fake_day_path, fake_categories, **fake_date)

    mock_process_ipynb.assert_called_once_with(os.path.join(fake_day_path, fake_slug),
                                               os.path.join(fake_prj_path, fake_post2, 'test.ipynb'),
                                               True)
    assert pd['url'] == '/{}/{}/{}/{}/'.format(fake_date['year'], fake_date['month'],
                                               fake_date['day'], fake_slug)
    assert 'uncategorized' in fake_categories.keys()

    if os.path.exists(fake_day_path):
        shutil.rmtree(fake_day_path)
    if os.path.exists(fake_post1):
        shutil.rmtree(fake_post1)
    if os.path.exists(fake_post2):
        shutil.rmtree(fake_post2)


def test_generate_posts():
    fake_out_path = 'output/'
    fake_dts = {
        2014: {
            1: {
                1: {
                    'fake_post': {}
                }
            },
            2: {
                1: {
                    'fake_post': {}
                },
                2: {
                    'fake_post': {}
                }
            },
        },
        2015: {
            1: {
                1: {
                    'fake_post': {}
                }
            }
        }
    }

    generate = Generate()
    generate.out_path = fake_out_path
    generate.dts = fake_dts

    with mock.patch.object(generate, '_generate_post') as mock_gen_post:
        with mock.patch.object(generate, '_generate_day_index') as mock_gen_day_index:
            with mock.patch.object(generate, '_generate_month_index') as mock_gen_month_index:
                with mock.patch.object(generate, '_generate_year_index') as mock_gen_year_index:
                    with mock.patch.object(generate, '_generate_categories') as mock_gen_categories:
                        with mock.patch.object(generate, '_generate_main_index') as mock_gen_main_index:
                            generate._generate_posts()

    mock_gen_post.assert_called()
    mock_gen_day_index.assert_called()
    mock_gen_month_index.assert_called()
    mock_gen_year_index.assert_called()
    mock_gen_categories.assert_called()
    mock_gen_main_index.assert_called()

    years = os.listdir(fake_out_path)
    for year in fake_dts:
        assert str(year) in years
        year_path = os.path.join(fake_out_path, str(year))
        months = os.listdir(year_path)
        for month in fake_dts[year]:
            assert str(month) in months
            month_path = os.path.join(year_path, str(month))
            days = os.listdir(month_path)
            for day in fake_dts[year][month]:
                assert str(day) in days

    if os.path.exists(fake_out_path):
        shutil.rmtree(fake_out_path)


def test_execute():
    generate = Generate()
    with mock.patch.object(generate, '_generate_menu') as mock_menu:
        with mock.patch.object(generate, '_generate_comments') as mock_comments:
            with mock.patch.object(generate, '_generate_pages') as mock_pages:
                with mock.patch.object(generate, '_generate_posts') as mock_posts:
                    generate.execute()

    mock_menu.assert_called_once_with()
    mock_comments.assert_called_once_with()
    mock_pages.assert_called_once_with()
    mock_posts.assert_called_once_with()
