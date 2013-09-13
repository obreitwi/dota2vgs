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

import string

from .logcfg import log

class ScriptCommand(object):
    """
        Makes creating commands writting to file easier.

        Automatically inserts ';' between several commands, escapes quotation
        marks.
    """

    template = "{key} {function}"

    # separator = "; "
    separator = ";"
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
                function=self.separator.join(self.content))

    @property
    def name(self):
        return self.key

    def cmd_length(self, content=None):
        if content is None:
            content = self.content
        # first count the length of the content
        length = sum((len(c) for c in content))
        # and account for inserted separators later on
        length += (len(content)-1) * len(self.separator)

        return length


class Bind(ScriptCommand):
    template = "bind \"{key}\" \"{function}\""


class Alias(ScriptCommand):
    template = "alias \"{key}\" \"{function}\""

    max_cmd_len = 430 # just a guess

    possible_suffixes = [ "_" + s for s in string.ascii_letters + string.digits]

    def get(self):
        # first check if we are within limits
        if self.cmd_length() <= self.max_cmd_len:
            return super(Alias, self).get()

        # now we need to chunk the commands to be within the limit
        chunk_idx = self.make_chunks(self.content)

        replacement = Alias(self.name)
        replacement.add(self.get_rep_name(0))

        chunks = [replacement]
        for i, (c_start, c_stop) in enumerate(
                zip(chunk_idx[:-1], chunk_idx[1:])):
            chunks.append(Alias(self.get_rep_name(i)))

            for j in range(c_start, c_stop):
                chunks[-1].add(self.content[j])

            # add the nameof the following alias
            if i < len(chunk_idx)-2:
                chunks[-1].add(self.get_rep_name(i+1))

        return "\n".join(c.get() for c in chunks)


    def get_rep_name(self, idx):
        """
            Returns the replacement name.
        """
        return self.name + self.possible_suffixes[idx]


    def make_chunks(self, content):
        """
            Includes the last index
        """
        # determine the length of the command needed to call the next helper
        # alias
        len_next = len(self.name) + len(self.separator) +\
                max((len(suff) for suff in self.possible_suffixes))

        chunk_indices = [0]
        cur_idx = 0
        chunk_size = len_next

        reached_end = False

        while cur_idx != len(content):
            chunk_size += len(content[cur_idx]) + len(self.separator)

            if chunk_size > self.max_cmd_len:
                chunk_indices.append(cur_idx)
                chunk_size = len_next
                continue

            cur_idx += 1
        chunk_indices.append(len(content))

        return chunk_indices


