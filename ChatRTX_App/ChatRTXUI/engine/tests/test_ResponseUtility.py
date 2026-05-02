import pytest
import os
from unittest.mock import patch
import ntpath
import posixpath

# Ensure we can import the module correctly
import sys
import os.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ResponseUtility import getLocalLinksMarkdown

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
