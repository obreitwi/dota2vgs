#!/usr/bin/env python
# encoding: utf-8

# Copyright (c) 2013 Oliver Breitwieser
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
    Parses the source engine cfg-files to extract key binding information.
"""

import re
import logging

from .logcfg import log

class BindParser(object):

    matcher = re.compile(
                    r"^bind\s+\"(?P<key>[^\"]+)\"\s\"(?P<function>[^\"]+)\"")

    def __init__(self, filename):
        log.info("Parsing: {0}".format(filename))

        self.binds = {}
        with open(filename, "r") as f:
            for l in f.readlines():
                match = self.matcher.search(l)

                if match is None:
                    continue
                self.binds[match.groupdict()["key"]] = match.groupdict()["function"]

    def get(self):
        return self.binds

