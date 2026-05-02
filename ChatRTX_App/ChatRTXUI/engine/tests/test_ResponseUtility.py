import pytest
import os
from unittest.mock import patch
import ntpath
import posixpath

# Ensure we can import the module correctly
import sys
import os.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ResponseUtility import getLocalLinksMarkdown, getImagesMarkdown

def test_getLocalLinksMarkdown_empty_list():
    assert getLocalLinksMarkdown([]) == '<div class="links-list"></div>'

def test_getLocalLinksMarkdown_single_path():
    with patch('os.path.split', posixpath.split):
        paths = ['/path/to/my/document.txt']
        expected = '<div class="links-list"><a data-link=\'/path/to/my/document.txt\'>document.txt</a></div>'
        assert getLocalLinksMarkdown(paths) == expected

def test_getLocalLinksMarkdown_multiple_paths():
    with patch('os.path.split', posixpath.split):
        paths = ['/path/to/my/document.txt', '/another/path/image.png']
        expected = '<div class="links-list"><a data-link=\'/path/to/my/document.txt\'>document.txt</a><a data-link=\'/another/path/image.png\'>image.png</a></div>'
        assert getLocalLinksMarkdown(paths) == expected

def test_getLocalLinksMarkdown_windows_paths():
    with patch('os.path.split', ntpath.split):
        paths = ['C:\\Users\\test\\Documents\\file.pdf', 'D:\\data\\info.csv']
        expected = '<div class="links-list"><a data-link=\'C:\\Users\\test\\Documents\\file.pdf\'>file.pdf</a><a data-link=\'D:\\data\\info.csv\'>info.csv</a></div>'
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
