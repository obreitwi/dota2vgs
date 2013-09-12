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

from .logcfg import log

class ScriptCommand(object):
    """
        Makes creating commands writting to file easier.

        Automatically inserts ';' between several commands, escapes quotation
        marks.
    """

    template = "{key} {function}"

    seperator = "; "
    to_escape = [ "\"" ]

    def __init__(self, key):
        self.key = key
        self.content = []

    def add(self, command):
        """
            Add another command to the function.
        """
        for esc in self.to_escape:
            command = command.replace(esc, "\\" + esc)

        self.content.append(command)

    def get(self):
        """
            Return the full command.
        """
        return self.template.format(key=self.key,
                function=self.seperator.join(self.content))

    @property
    def name(self):
        return self.key


class Alias(ScriptCommand):
    template = "alias \"{key}\" \"{function}\""

class Bind(ScriptCommand):
    template = "bind \"{key}\" \"{function}\""

