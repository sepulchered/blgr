import os
import json
import shutil
import datetime
from unittest import mock

import jinja2

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

    generate._generate_month_index(month_path, fake_posts, year, header)

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
    pass


def test_category_index():
    pass


def test_generate_categories():
    pass


def test_process_ipynb():
    pass


def test_append_html():
    pass


def test_generate_posts():
    pass


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
