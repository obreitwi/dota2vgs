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

__all__ = ["Composer"]

from .logcfg import log
from .cfg_parser import BindParser
from .lst_parser import LST_Hotkey_Parser
from .commands import Bind, Alias, StatefulAlias
from .overlay import GroupWriter
from .misc import load_data

import string
import itertools as it

class ParseError(Exception):
    pass

class Composer(object):
    """
       Composes and write the VGS system.
    """
    # allowed letters for names
    desired_letters = string.ascii_letters\
            + "_" + string.digits


    # prefix for aliases
    prefix = "vgs_"
    prefix_original = "ori_"
    prefix_current = "cur_"
    prefix_group = "grp_"
    prefix_phrase = "phr_"

    designator_groups = "groups"
    designator_cmds = "phrases"

    @property
    def recursive_elements(self):
        return [self.designator_groups, self.designator_cmds]

    def __init__(self, cfg_files, lst_files, layout_file,
            output_file=None, ignore_keys=None, silent=False,
            lineending="\r\n" # windows style by default
            ):
        """
            `cfg_files` is a list of filenames from which to read the
            original configuration that is to be preserved.

            `layout_file` yaml file with layout infomration of the VGS.
        """
        self.silent = silent
        # aliases to be included in the final script
        self.aliases = {}
        self.LE = lineending

        # read existing binds
        self.existing_binds = {}
        for cfg_file in cfg_files:
            b = BindParser(cfg_file, silent=self.silent)
            for k,v in b.get().items():
                self.existing_binds[k.lower()] = v

        self.layout = load_data(layout_file)
        self.check_layout_names()
        self._determine_used_keys()
        self.key_stateful = set([])
        self.duplicates = {}

        if ignore_keys is not None:
            self.used_keys -= set(ignore_keys)

        # see if any of the used keys have a mapping in the lst file (dota 2
        # options)
        for lst_file in lst_files:
            h =  LST_Hotkey_Parser(lst_file, silent=self.silent)
            mapping = h.get_hotkey_functions(self.used_keys)
            self.existing_binds.update(mapping)

        # adjust the existing binding for the start hotkey only
        self.existing_binds[self.layout["hotkey"]] =\
                self.get_aname_group("start")
        self._setup_aliases_existing_binds()
        self._setup_aliases_restore()

        if self.layout.get("vgs_console_menu_enabled", False):
            self.setup_menu()
            self.has_menu = True
        else:
            self.has_menu = False

        self.layout["name"] = "start"
        self.setup_aliases_group(self.layout)

        self.additional_commands()

        if output_file is not None:
            self.write_script_file(output_file)

        if not self.silent:
            log.info("Please go to the Dota 2 options menu and delete the "
                    "bindings to the following keys: {}".format(self.used_keys))

    def setup_menu(self):
        writer_kwargs = {}

        def add_if_exists(layout_name, kwarg_name):
            if layout_name in self.layout:
                writer_kwargs[kwarg_name] = self.layout[layout_name]

        add_if_exists("vgs_menu_lines_offset", "lines_offset")
        add_if_exists("vgs_menu_show_lines", "lines_write_area")
        add_if_exists("vgs_menu_notify_time", "notify_time")
        add_if_exists("vgs_menu_hotkeys_min_width", "hotkey_min_width")

        self.console_writer = GroupWriter(**writer_kwargs)
        self.console_writer.add_stop_commands_to_alias(self.aliases["restore"])
        self.console_writer.set_footer(["",
            self.console_writer.format_hotkey(self.layout["hotkey_cancel"], "Cancel..")])

    def add_alias(self, name, type_=Alias):
        new_alias = type_(self.get_alias_name(name), lineending=self.LE)
        self.aliases[name] = new_alias
        return new_alias

    def get_cmd_alias(self, a_from, a_to):
        return "alias {} {}".format(a_from, a_to)

    def get_alias_name(self, name):
        # make sure name contains prefix
        if not name.startswith(self.prefix):
            name = self.prefix + name

        return name

    def get_aname_current(self, key, off_state=False):
        """
            `off_state` = True will return the off_state alias name for a
            stateful alias.
        """
        if self.is_key_stateful(key):
            if not off_state:
                prefix = StatefulAlias.token_state_on
            else:
                prefix = StatefulAlias.token_state_off
        else:
            prefix = ""
        return prefix + self.get_alias_name(self.prefix_current + key)

    def get_aname_original(self, key, off_state=False):
        """
            `off_state` = True will return the off_state alias name for a
            stateful alias.
        """
        if self.is_key_stateful(key):
            if not off_state:
                prefix = StatefulAlias.token_state_on
            else:
                prefix = StatefulAlias.token_state_off
        else:
            prefix = ""
        return prefix + self.get_alias_name(self.prefix_original + key)

    def get_aname_group(self, name):
        return self.get_alias_name(self.prefix_group + name)

    def get_aname_phrase(self, name):
        return self.get_alias_name(self.prefix_phrase + name)

    def is_key_stateful(self, key):
        return key in self.key_stateful

    def _determine_used_keys(self):
        # self.used_keys = set()

        # for now just add all ascii keys
        self.used_keys = set(string.lowercase)

        self.used_keys.add(self.layout["hotkey"])
        self.used_keys.add(self.layout["hotkey_cancel"])

        queue = []
        queue.extend(self.layout[self.designator_groups])

        while len(queue) > 0:
            item = queue.pop()

            if "hotkey" in item:
                self.used_keys.add(item["hotkey"])

            for k in self.recursive_elements:
                if k in item:
                    queue.extend(item[k])

    def _setup_aliases_existing_binds(self):
        """
            Sets up aliases containing the original key function.
        """
        for k in self.used_keys & set(self.existing_binds.keys()):
            existing_bind = self.existing_binds[k]

            alias_type = Alias

            if StatefulAlias.contains_state(existing_bind):
                # the bind contains state, we need to account for that
                alias_type = StatefulAlias

            alias = self.add_alias(self.get_aname_original(k), type_=alias_type)

            if StatefulAlias.contains_state(existing_bind):
                self.key_stateful.add(k)

            alias.add(existing_bind)

    def add_clear_aliases(self, alias, hotkeys):
        """
            Adds aliases that disable all aliases for the keys in hotkeys.
        """
        for h in hotkeys:
            alias.add("alias {}".format(self.get_aname_current(h)))
            if self.is_key_stateful(h):
                alias.add("alias {}".format(self.get_aname_current(h,
                    off_state=True)))


    def _setup_aliases_restore(self):
        """
            Sets up the alias resetting all used keys to their original state.
        """
        restore = self.add_alias("restore")
        self.restore_alias_name = restore.name
        for k in self.used_keys:
            restore.add("alias {current} {original}".format(
                current=self.get_aname_current(k),
                original=self.get_aname_original(k),
                ))
            if self.is_key_stateful(k):
                restore.add("alias {current} {original}".format(
                    current=self.get_aname_current(k, off_state=True),
                    original=self.get_aname_original(k, off_state=True),
                    ))

    def setup_aliases_group(self, dct):
        """
            Set up the starting alias.
        """
        self.assure_no_duplicate_hotkeys(dct)

        alias = self.add_alias(self.get_aname_group(dct["name"]))
        alias.add(self.get_cmd_alias(
            self.get_aname_current(self.layout["hotkey_cancel"]),
            self.restore_alias_name))

        # clear all other keys to prevent accidentatl keypresses
        clear_hotkeys = self.used_keys - set(self.get_concurrent_hotkeys(dct))
        clear_hotkeys -= set([self.layout["hotkey_cancel"],
            self.layout["hotkey"]])

        self.add_clear_aliases(alias, clear_hotkeys)

        for phrase in dct.get(self.designator_cmds, []):
            phrase_name = self.setup_phrase(phrase["name"], phrase["id"])
            hotkey_name = self.get_aname_current(phrase["hotkey"])

            alias.add(self.get_cmd_alias(hotkey_name, phrase_name))

        for group in dct.get(self.designator_groups, []):
            self.setup_aliases_group(group)

            group_name = self.get_aname_group(group["name"])
            hotkey_name = self.get_aname_current(group["hotkey"])

            alias.add(self.get_cmd_alias(hotkey_name, group_name))

        if self.has_menu:
            self.console_writer.write_group_info_to_alias(dct, alias)

    def assure_no_duplicate_hotkeys(self, dct):
        hotkeys = self.get_concurrent_hotkeys(dct)
        set_hotkeys = set(hotkeys)

        if len(hotkeys) != len(set_hotkeys):
            duplicate_hotkeys = self.duplicates.setdefault(dct["name"], [])
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

        for elem in self.recursive_elements:
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
        alias.add(self.restore_alias_name)
        return alias.name

    def write_script_file(self, f):
        self.write_aliases(f)
        self.write_bindings(f)
        if self.has_menu:
            self.write_menu_prelude(f)
        f.write(self.restore_alias_name + self.LE)
        f.write("echo \"VGS successfully loaded!\"" + self.LE)

    def write_menu_prelude(self, f):
        for cmd in self.console_writer.start_commands():
            f.write(cmd + self.LE)

    def write_bindings(self, file):
        for k in self.used_keys:
            b = Bind(k)
            b.add(self.get_aname_current(k))
            file.write(b.get() + self.LE)

    def write_aliases(self, file):
        for a in self.aliases.values():
            file.write(a.get() + self.LE)

    def check_layout_names(self, grp=None):
        if grp is None:
            grp = self.layout

        name = grp.get("name", "")
        if any((l not in self.desired_letters for l in name)):
            raise ParseError("Illegal character in {}.".format(name))

        for g in it.chain(
                grp.get(self.designator_groups, []),
                grp.get(self.designator_cmds, [])):
            self.check_layout_names(g)

    def additional_commands(self):
        """
            Other commands outside of the regular rebinding
        """
        if self.layout.get("indicate_vgs_mode_via_minimap", False):
            self.set_indicator()

    def set_indicator(self):
        start = self.aliases[self.get_aname_group("start")]
        start.add("dota_minimap_hero_size {}".format(
            self.layout.get("minimap_hero_size_vgs_mode", 1200)))

        restore = self.aliases["restore"]
        restore.add("dota_minimap_hero_size {}".format(
            self.layout.get("minimap_hero_size_regular", 600)))


