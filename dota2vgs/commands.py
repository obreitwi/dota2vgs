#!/usr/bin/env python
# encoding: utf-8

# Copyright (c) 2013-2014 Oliver Breitwieser
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
    # to_escape = [ "\"" ]
    to_escape = []

    def __init__(self, key, lineending="\r\n"):
        self.LE = lineending
        self.key = key
        self.content = []

    def add(self, command, escape_command=True):
        """
            Add another command to the function.

            escape_command: Needs to be disabled when Aliases create aliases.
        """
        if escape_command:
            command = self._prepare_command(command)
        self.content.append(command)

    def prepend(self, command, escape_command=True):
        """
            Like `add` but prepends it to the commands.
        """
        if escape_command:
            command = self._prepare_command(command)
        self.content.insert(0, command)

    def _prepare_command(self, command):
        for esc in self.to_escape:
            command = command.replace(esc, "\\" + esc)
        return command

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
                chunks[-1].add(self.content[j], escape_command=False)

            # add the nameof the following alias
            if i < len(chunk_idx)-2:
                chunks[-1].add(self.get_rep_name(i+1), escape_command=False)

        return self.LE.join(c.get() for c in chunks)


    def get_rep_name(self, idx):
        """
            Returns the replacement name.
        """
        return self.name + self.possible_suffixes[idx]


    def make_chunks(self, content):
        """
            Make a list containing where the content should
            be chunked.

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


class StatefulAlias(Alias):
    """
        Stateful Alias

        Automatically creates two aliases for on and off.
    """

    token_state_on = "+"
    token_state_off = "-"
    token_cmd_split = ";"

    def get(self):
        # we contain state, apply all non-state toggles in plus
        # all state toggles go in both

        # for that we create two aliases on and off
        alias_on_name = self.name
        alias_off_name = alias_on_name.replace(self.token_state_on,
                self.token_state_off)

        alias_on = Alias(alias_on_name)
        alias_off = Alias(alias_off_name)

        for c in self.content:
            alias_on.add(c, escape_command=False)
            if self.contains_state(c):
                alias_off.add(c.replace(self.token_state_on,
                    self.token_state_off), escape_command=False)

        return self.LE.join([alias_on.get(), alias_off.get()])

    @property
    def name(self):
        orig_name = super(StatefulAlias, self).name
        return self.token_state_on + orig_name

    @classmethod
    def contains_state(cls, entry):
        return any(cmd.strip().startswith(cls.token_state_on)
                    for cmd in entry.split(cls.token_cmd_split))

    @classmethod
    def check_content_for_state(cls, content):
        return any(cls.containts_state(entry) for entry in content)

    def contains_state_at_all(self):
        return self.check_content_for_state(self.content)


