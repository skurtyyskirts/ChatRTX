import os
import pytest
from ResponseUtility import getLocalLinksMarkdown, getImagesMarkdown

def test_getLocalLinksMarkdown_empty_list():
    paths = []
    expected = '<div class="links-list"></div>'
    assert getLocalLinksMarkdown(paths) == expected

def test_getLocalLinksMarkdown_single_path():
    paths = ['/foo/bar/test.txt']
    expected = '<div class="links-list"><a data-link=\'/foo/bar/test.txt\'>test.txt</a></div>'
    assert getLocalLinksMarkdown(paths) == expected

def test_getLocalLinksMarkdown_multiple_paths():
    paths = ['/foo/bar/test1.txt', '/foo/baz/test2.md']
    expected = '<div class="links-list"><a data-link=\'/foo/bar/test1.txt\'>test1.txt</a><a data-link=\'/foo/baz/test2.md\'>test2.md</a></div>'
    assert getLocalLinksMarkdown(paths) == expected

def test_getLocalLinksMarkdown_no_directory():
    paths = ['test.txt']
    expected = '<div class="links-list"><a data-link=\'test.txt\'>test.txt</a></div>'
    assert getLocalLinksMarkdown(paths) == expected

def test_getImagesMarkdown_empty_list():
    paths = []
    expected = '<div class="images-list"></div>'
    assert getImagesMarkdown(paths) == expected

def test_getImagesMarkdown_single_path():
    paths = ['/foo/bar/image.png']
    expected = '<div class="images-list"><a data-link=\'/foo/bar/image.png\'><img src=\'/foo/bar/image.png\'></a></div>'
    assert getImagesMarkdown(paths) == expected

def test_getImagesMarkdown_multiple_paths():
    paths = ['/foo/bar/image1.jpg', '/foo/baz/image2.png']
    expected = '<div class="images-list"><a data-link=\'/foo/bar/image1.jpg\'><img src=\'/foo/bar/image1.jpg\'></a><a data-link=\'/foo/baz/image2.png\'><img src=\'/foo/baz/image2.png\'></a></div>'
    assert getImagesMarkdown(paths) == expected
