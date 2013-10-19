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

__all__ = ["SheetMaker"]

from .logcfg import log
from .misc import load_data
from .vgs import Composer

from pprint import pformat

class SheetMaker(object):
    """
        Makes a sheet cheat for the layout file
    """

    designator_groups = Composer.designator_groups
    designator_cmds = Composer.designator_cmds
    recursive_elements = Composer.recursive_elements

    str_connector = " -> "
    str_sep_hotkey = " "
    str_space = " "

    def __init__(self, layout_file, output_file,
            sort_alphabetically=True, lineending="\r\n"):
        self.LE = lineending

        layout = load_data(layout_file)
        self.output_file = output_file
        self.sort_alphabetically = sort_alphabetically

        self.write_prelude(layout)
        self.handle_group(layout, tuple())



    def write_prelude(self, layout):
        self.write_to_file("Hotkey (start): {}".format(layout["hotkey"]))
        self.write_to_file("Hotkey (stop):  {}".format(layout["hotkey_cancel"]))

        self.write_to_file("")
        self.write_to_file("Hotkey      Phrase")
        self.write_to_file("^^^^^^^^^^^^^^^^^^")

    def handle_group(self, grp, parents):
        # only write named groups
        if "name" in grp:
            fmt_group = self.format_group(grp, parents)
            self.write_to_file(fmt_group)

        parents = parents + (grp,)

        if self.designator_cmds in grp:
            self.handle_cmds(grp[self.designator_cmds], parents)

        if self.designator_groups in grp:
            grps = grp[self.designator_groups]
            if self.sort_alphabetically:
                grps = sorted(grps, key=lambda x: x["hotkey"])
            for g in grps:
                self.handle_group(g, parents)

        self.write_to_file("")

    def handle_cmds(self, cmds, parents):
        if self.sort_alphabetically:
            cmds = sorted(cmds, key=lambda x: x["hotkey"])
        for cmd in cmds:
            fmt_cmd = self.format_cmd(cmd, parents)
            self.write_to_file(fmt_cmd)

    def format_group(self, grp, parents):
        fmt_parents = self.format_parents(parents)
        fmt_hotkey = fmt_parents + self.str_connector + grp["hotkey"]
        fmt_group = fmt_hotkey + self.str_space  + "-" * 28 + self.str_space +\
                self.str_sep_hotkey + grp["name"]

        return fmt_group

    def format_parents(self, parents):
        return self.str_connector.join(prnt["hotkey"] for prnt in parents)

    def format_cmd(self, cmd, parents):
        fmt_parents = self.format_parents(parents)
        fmt_cmd = fmt_parents + self.str_connector + cmd["hotkey"] +\
                self.str_sep_hotkey + cmd["name"]

        return fmt_cmd

    def write_to_file(self, line):
        # log.info(line)
        self.output_file.write(line + self.LE)

