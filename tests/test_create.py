import os
import json
import shutil
import functools
from unittest.mock import patch

from blgr.blgr import Create


def input_mock(ret_val, prompt):
    return ret_val


def test_prepare():
    create = Create()

    input_y = functools.partial(input_mock, 'y')
    input_n = functools.partial(input_mock, 'n')
    input_enter = functools.partial(input_mock, '')

    with patch.object(create, '_ask_post_meta', return_value=None) as mock_user_interaction:
        create.prepare(input_n)
        create.prepare(input_y)
    mock_user_interaction.assert_called_once_with()

    with patch.object(create, '_ask_post_meta', return_value=None) as mock_user_interaction:
        create.prepare(input_enter)  # default behaviour
    assert not mock_user_interaction.called


def test_metadata():
    create = Create()

    input_y = functools.partial(input_mock, 'y')
    input_n = functools.partial(input_mock, 'n')
    input_enter = functools.partial(input_mock, '')
    txt_data = 'post txt data'
    input_txt = functools.partial(input_mock, txt_data)

    create._ask_post_meta(input_txt, set_link_input=input_y, comments_input=input_y)
    assert create.post_data['title'] == txt_data
    assert create.post_data['slug'] == txt_data
    assert create.post_data['category'] == txt_data
    assert create.post_data['set_link']
    assert create.post_data['comments']

    create._ask_post_meta(input_txt, set_link_input=input_n, comments_input=input_y)
    assert create.post_data['title'] == txt_data
    assert create.post_data['slug'] == txt_data
    assert create.post_data['category'] == txt_data
    assert not create.post_data['set_link']
    assert create.post_data['comments']

    create._ask_post_meta(input_txt, set_link_input=input_y, comments_input=input_n)
    assert create.post_data['title'] == txt_data
    assert create.post_data['slug'] == txt_data
    assert create.post_data['category'] == txt_data
    assert create.post_data['set_link']
    assert not create.post_data['comments']

    create._ask_post_meta(input_txt, set_link_input=input_n, comments_input=input_n)
    assert create.post_data['title'] == txt_data
    assert create.post_data['slug'] == txt_data
    assert create.post_data['category'] == txt_data
    assert not create.post_data['set_link']
    assert not create.post_data['comments']

    create._ask_post_meta(input_txt, set_link_input=input_enter, comments_input=input_enter)
    assert not create.post_data['set_link']
    assert create.post_data['comments']


def test_execute():
    create = Create()

    mock_post_data = {'title': 'famous title', 'slug': 'great slug',
                      'category': 'awesome category', 'set_link': False,
                      'comments': True}
    create.post_data = mock_post_data

    conf = {'posts': {'path': './posts'}}

    create.config = conf
    create.prj_path = 'blgr/'
    create.execute()

    posts_path = os.path.join(create.prj_path, conf['posts']['path'])
    posts = os.listdir(posts_path)
    assert len(posts)
    post_path = os.path.join(posts_path, posts[0])
    post_files = os.listdir(post_path)
    assert len(post_files) == 2  # exactly 2 files ipynb and meta
    fexts = [os.path.splitext(post_file)[1] for post_file in post_files]
    print(fexts)
    assert '.json' in fexts
    assert '.ipynb' in fexts
    assert 'meta.json' in post_files


    with open(os.path.join(post_path, 'meta.json'), 'r') as meta_file:
        meta = json.load(meta_file)

    assert meta.get('title', None) == mock_post_data['title']
    assert meta.get('slug', None) == mock_post_data['slug']
    assert meta.get('category', None) == mock_post_data['category']
    assert meta.get('set_link', None) == mock_post_data['set_link']
    assert meta.get('comments', None) == mock_post_data['comments']

    # clean up posts folder
    shutil.rmtree(os.path.join('blgr', conf['posts']['path']))
