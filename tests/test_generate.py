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


def test_main_indices():
    pass


def test_pages():
    pass


def test_comments():
    pass


def test_menu():
    pass


def test_year_index():
    pass


def test_month_index():
    pass


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
