#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zipfile

def main():
    try:
        archive = zipfile.ZipFile('pyinteractive-vim.zip', 'w')

        archive.write('./plugin/python/pyinteractive.py', 'plugin/python/pyinteractive.py')
        archive.write('./doc/pyinteractive.rux', 'doc/pyinteractive.rux')
        archive.write('./doc/pyinteractive.txt', 'doc/pyinteractive.txt')
        archive.write('./plugin/pyinteractive.vim', 'plugin/pyinteractive.vim')
    finally:
        archive.close()

if(__name__ == '__main__'):
    main()
