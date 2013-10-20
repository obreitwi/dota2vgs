#!/usr/bin/env python:
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
    Parses the lst files containing dota key bindings.
"""

import re
from .logcfg import log


class LST_Error(Exception):
    pass


class ParentDict(dict):
    """
        A dict that knows about its parent.
    """

    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        super(ParentDict, self).__init__(*args, **kwargs)


class LST_Parser(object):

    matchers = {
        "keyval"  :
            re.compile("^\s*\"(?P<key>[^\"]+)\"\s*\"(?P<value>[^\"]+)\"\s*$"),
        "keyname" :
            re.compile("^\s*\"(?P<key>[^\"]+)\"\s*$"),
        "dict-begin" :
            re.compile("^\s*{\s*$"),
        "dict-end" :
            re.compile("^\s*}\s*$"),
    }

    def __init__(self, f, silent=False):
        self.silent = silent

        f.seek(0)
        self.content = {}

        current = self.content
        next_name = None

        for line in f.readlines():
            line = line.strip()

            # try to find a key-value pair
            keyval = self.matchers["keyval"].search(line)
            if keyval is not None:
                keyval = keyval.groupdict()
                current[keyval["key"]] = keyval["value"]
                continue

            keyname = self.matchers["keyname"].search(line)
            if keyname is not None:
                next_name = keyname.groupdict()["key"]
                continue

            begin = self.matchers["dict-begin"].search(line)
            if begin is not None:
                current[next_name] = ParentDict(current)
                current = current[next_name]
                continue

            end = self.matchers["dict-end"].search(line)
            if end is not None:
                current = current.parent

    def get(self):
        return self.content


class LST_Hotkey_Parser(LST_Parser):

    def get_hotkey_functions(self, hotkeys):
        """
            Return a dict containing the functions for the supplied hotkeys.
        """

        mappings = {}
        try:
            read_hotkeys = self.content["KeyBindings"]["Keys"]

            for k,v in read_hotkeys.items():
                # also ignore if there is no keybinding or a modifier in place
                if "Key" not in v or "Modifier" in v:
                    continue

                if not self.check_validity(k, v):
                    continue

                key = v["Key"]
                function = v["Action"]

                # single keys are always lowercase in cfg -> keep it consistent
                if len(key) == 1:
                    key = key.lower()

                if key in hotkeys:
                    mappings[key] = function
        except KeyError:
            raise LST_Error("No hotkey information found in specified .lst file!")

        return mappings


    def check_validity(self, k, v):
        """
            Determine if the entry `v` is valid to be included in the functions.

            Needed for some legacy stuff.
        """
        ignore_prefixes = ["Heroes", "Spectator"]

        if any((k.startswith(pref) for pref in ignore_prefixes)):
            return False

        elif k.startswith("Shop"):
            # we ignore all shop keys except for the toggle
            return v["Name"] == "ShopToggle"

        elif v["Action"].split()[0] == "dota_ability_execute":
            # we need to make sure to only cound PrimaryAction -> the rest is
            # legacy
            if v.get("Panel", "") == "#DOTA_KEYBIND_MENU_ABILITIES" and\
                    v.get("SubPanel", "") == "#DOTA_KEYBIND_ABILITY_HERO":
                return True
            else:
                return False

        else:
            # so far we have no other special rules, so the entry is valid
            return True

