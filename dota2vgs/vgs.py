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
from .cfg_parser import BindParser
from .commands import Alias, Bind
from .misc import load_data


class Composer(object):
    """
       Composes and write the VGS system. 
    """

    # prefix for aliases
    prefix = "dota2vgs_"
    prefix_original = "original_"
    prefix_current = "current_"
    prefix_group = "group_"
    prefix_phrase = "phrase_"

    def __init__(self, cfg_filenames, layout_filename, output_filename=None):
        """
            `cfg_filenames` is a list of filenames from which to read the
            original configuration that is to be preserved.

            `layout_filename` yaml file with layout infomration of the VGS. 
        """
        # aliases to be included in the final script
        self.aliases = {}

        # read existing binds
        self.existing_binds = {}
        for cfg_fn in cfg_filenames:
            b = BindParser(cfg_fn)
            self.existing_binds.update(b.get())

        with open(layout_filename, "r") as f:
            self.layout = load_data(f)
        # adjust the existing binding for the start hotkey only
        self.existing_binds[self.layout["hotkey_start"]] =\
                self.get_aname_group("start")
        self._determine_used_keys()
        self._setup_aliases_existing_binds()
        self._setup_aliases_restore()
        self.layout["name"] = "start"
        self.setup_aliases_group(self.layout)

        if output_filename is not None:
            self.write_script_file(output_filename)

    def add_alias(self, name):
        new_alias = Alias(self.get_alias_name(name))
        self.aliases[name] = new_alias
        return new_alias

    def get_cmd_alias(self, a_from, a_to):
        return "alias {} {}".format(a_from, a_to)

    def get_alias_name(self, name):
        if name.startswith(self.prefix):
            return name
        else:
            return self.prefix + name

    def get_aname_current(self, name):
        return self.get_alias_name(self.prefix_current + name)

    def get_aname_original(self, name):
        return self.get_alias_name(self.prefix_original + name)

    def get_aname_group(self, name):
        return self.get_alias_name(self.prefix_group + name)

    def get_aname_phrase(self, name):
        return self.get_alias_name(self.prefix_phrase + name)


    def _determine_used_keys(self):
        self.used_keys = set()
        self.used_keys.add(self.layout["hotkey_start"])
        self.used_keys.add(self.layout["hotkey_cancel"])

        queue = []
        queue.extend(self.layout["groups"])

        recursive_elements = ["phrases", "groups"]

        while len(queue) > 0:
            item = queue.pop()

            if "hotkey" in item:
                self.used_keys.add(item["hotkey"])

            for k in recursive_elements:
                if k in item:
                    queue.extend(item[k])

    def _setup_aliases_existing_binds(self):
        """
            Sets up aliases containing the original key function.
        """
        for k in self.used_keys & set(self.existing_binds.keys()):
            alias = self.add_alias(self.get_aname_original(k))
            alias.add(self.existing_binds[k])

    def _setup_aliases_restore(self):
        """
            Sets up the alias resetting all used keys to their original state.
        """
        restore = self.add_alias("restore")
        for k in self.used_keys:
            restore.add("alias {current} {original}".format(
                current=self.get_aname_current(k),
                original=self.get_aname_original(k),
                ))

    def setup_aliases_group(self, dct):
        """
            Set up the starting alias.
        """
        self.assure_no_duplicate_hotkeys(dct)

        alias = self.add_alias(self.get_aname_group(dct["name"]))

        for phrase in dct.get("phrases", []):
            phrase_name = self.setup_phrase(phrase["name"], phrase["id"])
            hotkey_name = self.get_aname_current(phrase["hotkey"])

            alias.add(self.get_cmd_alias(hotkey_name, phrase_name))

        for group in dct.get("groups", []):
            self.setup_aliases_group(group)

            group_name = self.get_aname_group(group["name"])
            hotkey_name = self.get_aname_current(group["hotkey"])

            alias.add(self.get_cmd_alias(hotkey_name, group_name))

    def assure_no_duplicate_hotkeys(self, dct):
        hotkeys = self.get_concurrent_hotkeys(dct)
        set_hotkeys = set(hotkeys)

        if len(hotkeys) != len(set_hotkeys):
            duplicate_hotkeys = []
            for k in set_hotkeys:
                if hotkeys.count(k) > 1:
                    duplicate_hotkeys.append(k)
            log.warn("Group {} contains duplicate hotkeys for: {}".format(
                dct["name"], ", ".join(duplicate_hotkeys)))

    def get_concurrent_hotkeys(self, dct):
        """
            Returns all hotkeys used by group.

            NOTE: That it is a list and may have duplicates etc.
        """
        hotkeys = []
        recursive_elements = ["phrases", "groups"]

        for elem in recursive_elements:
            for item in dct.get(elem, []):
                hotkeys.append(item["hotkey"])

        return hotkeys

    def setup_phrase(self, name, id):
        """
            Set up the alias with name `name` and id `id`.

            Returns the name of the alias.
        """
        alias = self.add_alias(self.get_aname_phrase(name))
        alias.add("chatwheel_say {}".format(id))
        alias.add(self.prefix+"restore")
        return alias.name

    def write_script_file(self, filename):
        f = open(filename, "w")
        self.write_aliases(f)
        self.write_bindings(f)
        f.write(self.prefix+"restore")
        f.close()

    def write_bindings(self, file):
        for k in self.used_keys:
            b = Bind(k)
            b.add(self.get_aname_current(k))
            file.write(b.get()+"\n")

    def write_aliases(self, file):
        for a in self.aliases.values():
            file.write(a.get()+"\n")

