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

import copy

from .misc import load_data

class ConsoleWriter(object):
    """
        Class that makes writing echos to console and displaying
        them in the top left corner via developer mode more streamlined.
    """
    cmd_echo = "echo \"| {}\""

    def __init__(self, lines_offset=5, lines_write_area=25, notify_time=30):
        """
            lines_offset: number of lines that are always empty
                          to offset the menu position.

            lines_write_area: How big is the area in which actual content
                              is written.
            notify_time: How long should notifies be visible.
        """
        self.lines_offset = lines_offset
        self.lines_area = lines_write_area

        self.lines_total = self.lines_offset + self.lines_area
        self.notify_time = notify_time

        self.footer = []

    def start_commands(self):
        """
            Returns required setup commands to enable console printing
            except for enabling developer mode so that ingame nothing
            is printed.
        """
        return [
                "con_notifytime {}".format(int(self.notify_time)),
                "contimes {}".format(int(self.lines_total)),
                # "con_filter_text \"@!.,@!\"", # highly unlikely text
                # "con_filter_enable 1",
                "developer 1"
            ]

    def write_messages(self, messages):
        """
            Write `messages` and enable developer mode.

            Returns the necessare commands.
        """
        all_messages = messages + self.footer

        # enable the developer mode to actually display the messages
        # also disable the filter so all our messages go through
        commands = [
                # "developer 1",
                # "clear",
                # "con_filter_enable 0"
                # "contimes {}".format(self.lines_offset + len(all_messages))
            ]

        # write top offset so that we are not over the menu buttons
        for i in range(self.lines_offset):
            commands.append(self.cmd_echo.format(""))

        # write messages
        for message in all_messages:
            commands.append(self.cmd_echo.format(message))

        # see if we need to add buffer messages at the button because
        # we dont have enough messages to display
        num_filler_lines = self.lines_area - len(all_messages)
        if num_filler_lines > 0:
            for i in range(num_filler_lines):
                commands.append(self.cmd_echo.format(""))

        # now enable the filter again so that the user does not see
        # any random console messages
        # commands.append("con_filter_enable 1")

        return commands

    def add_messages_to_alias(self, messages, alias):
        """
            Adds messages to alias execution
        """
        for cmd in self.write_messages(messages):
            alias.add(cmd)

    def stop_commands(self):
        """
            Return commands that resume normal console flow.
        """
        return []
        # return [
                # "developer 0", # hide debug messages again
                # "con_filter_enable 0", # disable the filter so that regular
                                       # # messages can be seen in the console
                                       # # again
            # ]

    def add_stop_commands_to_alias(self, alias):
        for cmd in self.stop_commands():
            alias.add(cmd)

    def set_footer(self, messages):
        """
            Supply an array of messages that is written below every set of
            messages displayed.
        """
        self.footer = messages


class GroupWriter(ConsoleWriter):
    """
        Class to write an overview over the group contents.
    """
    designator_groups = "groups"
    designator_cmds = "phrases"

    name_cmds = "Phrases"

    fmt_hotkey = "{hk} -> {lbl}"

    def __init__(self, hotkey_min_width=12, *args, **kwargs):
        """
            hotkey_min_width: minimum width of hotkey representation
        """
        super(GroupWriter, self).__init__(*args, **kwargs)
        self.hk_min_width = hotkey_min_width


    def format_hotkey(self, hotkey, label):
        return self.fmt_hotkey.format(hk=hotkey,
                lbl=label.replace("_", " "))

    def append_hotkeys(self, items, messages):
        for item in items:
            messages.append(self.format_hotkey(item["hotkey"], item["name"]))


    def write_group_info_to_alias(self, group, alias):
        """
            Make the group alias display an overview over all groups and
            commands when called.
        """
        messages = []
        if self.designator_groups in group:
            messages.append("Available groups:")
            messages.append("=================")
            groups = sorted(group[self.designator_groups],
                    key=lambda x:x["name"])

            self.append_hotkeys(groups, messages)

        if self.designator_cmds in group:
            if self.designator_groups in group:
                # Add separator
                messages.append("")

            messages.append("Available {}:".format(self.name_cmds))
            messages.append("===========" + "=" * len(self.name_cmds))
            cmds = sorted(group[self.designator_cmds],
                    key=lambda x:x["name"])

            self.append_hotkeys(cmds, messages)

        self.add_messages_to_alias(messages, alias)


class AutohotkeyWriter(object):
    """
        Writer that generates an Autohotkey script that will act as overlay.
    """

    default_config = {
            "root_group" : "VGS",
            "font_size" : 10,
            "font_name" : "Courier New",
            "hide_delay" : 30000,
            "xpos" : 0,
            "ypos" : 0,

            "place_left_of_minimap" : True,
            "minimap_x_ratio" : 0.172,

            "hotkey_toggle" : "^F12",
            "hotkey_sync" : "Esc",
        }

    sub_names = {
            "hide" : "HideProgress",
            "reset" : "ResetHotkeys",
            "init" : "Initialize",
            "empty" : "Empty",
            "toggle": "VGS_Toggle"
        }

    window_names = {
            "dota2" : "DOTA 2",
            "overlay" : "d2vgs_overlay",
            }

    def __init__(self):
        self.layout = None
        self.all_hotkeys = set()
        self.code = []

    def get_popup_appearance(self):
        return "b zh0 c0 fs{font_size} Hide ".format(
                font_size=self.config["font_size"])

    def set_layout(self, layout):
        layout.setdefault("overlay", {})

        # backwards compatability
        if "overlay_xpos" in layout:
            layout["overlay"]["xpos"] = layout["overlay_xpos"]

        if "overlay_ypos" in layout:
            layout["overlay"]["ypos"] = layout["overlay_ypos"]

        self.config = self.setup_config(layout["overlay"])

        layout["name"] = self.config["root_group"]

        self.layout = layout

    def setup_config(self, cfg):
        config = copy.deepcopy(self.default_config)
        config.update(cfg)
        return config

    def set_layout_from_file(self, layout_file):
        self.set_layout(load_data(layout_file))

    def generate_code(self):
        self.all_hotkeys = self.gather_hotkeys(self.layout)

        self.code = []
        self.code.append("#SingleInstance force")
        self.code.append("#IfWinActive, {}".format(self.window_names["dota2"]))
        # optimizations
        self.code.extend([
                "#NoEnv",
                "SetBatchLines -1",
                "ListLines Off",
            ])

        self.code.append(self.get_call_sub(self.sub_names["init"]))
        self.code.append(self.get_call_sub(self.sub_names["reset"]))
        self.code.append("Return")
        self.code.append("")

        groups = [self.layout]

        for group in groups:
            self.code.extend(self.get_group_subroutine(group))
            groups.extend(group.get("groups", []))

            self.code.append("")

        # add special subroutines
        self.code.extend(self.get_subroutine_hide())
        self.code.append("")
        self.code.extend(self.get_subroutine_reset())
        self.code.append("")
        self.code.extend(self.get_subroutine_empty())
        self.code.append("")
        self.code.extend(self.get_subroutine_init())
        self.code.append("")
        self.code.extend(self.get_subroutine_toggle())
        self.code.append("")

        self.code.append("")
        self.code.append("")


    def write(self, outfile, newline="\r\n"):
        self.generate_code()
        outfile.write(newline.join(self.code))

    def gather_hotkeys(self, group):
        hotkeys = set()

        for hk in ("hotkey", "hotkey_cancel"):
            if hk in group:
                hotkeys.add(group[hk])

        for phr in group.get("phrases", []):
            hotkeys.add(phr["hotkey"])

        for grp in group.get("groups", []):
            hotkeys.add(grp["hotkey"])
            hotkeys = hotkeys.union(self.gather_hotkeys(grp))

        return hotkeys

    def get_progress_popup(self, lines):
        code = ["Progress, {fmt}, {lines}, , {title}, {font_name}".format(
            fmt=self.get_popup_appearance(),
            lines="`n".join(lines),
            title=self.window_names["overlay"],
            font_name=self.config["font_name"])]
        code.append(self.get_progress_show())
        code.extend(self.get_move_command())
        return code

    def get_move_command(self):
        if self.config["place_left_of_minimap"]:
            code = [
                    "WinGetPos, dota2_X, dota2_Y, dota2_W, dota2_H, {title}"\
                            .format(title=self.window_names["dota2"]),
                    "WinGetPos, vgs_overlay_X, vgs_overlay_Y, vgs_overlay_W, "
                    "vgs_overlay_H, {title}".format(
                        title=self.window_names["overlay"]),
                    "target_X := {factor} * dota2_W + dota2_X".format(
                        factor=self.config["minimap_x_ratio"]),
                    "target_Y := dota2_Y + dota2_H - vgs_overlay_H",
                    "WinMove, {title}, , %target_X%, %target_Y%".format(
                        title=self.window_names["overlay"])
                ]
            return code

        else:
            return ["WinMove, {title}, , {xpos}, {ypos}".format(
                title=self.window_names["overlay"],
                xpos=self.config["xpos"], ypos=self.config["ypos"])]

    def get_progress_show(self):
        return "Progress, Show"

    def get_timer(self, name, delay, once=True):
        # negative delay so that the timer runs only once
        if once:
            delay *= -1
        return "SetTimer, {name}, {delay}".format(name=name, delay=delay)

    def get_hide_timer(self):
        return self.get_timer(self.sub_names["hide"],
                delay=self.config["hide_delay"])

    def get_group_subroutine(self, group):
        lines = self.get_group_displaytext(group)
        hotkeys_to_group = {v["hotkey"]:v["name"]
                for v in group.get("groups", [])}
        hotkeys_phrases = [v["hotkey"] for v in group.get("phrases", [])]
        code = [
                "{}:".format(self.get_group_subroutine_name(group["name"])),
            ]
        code.extend(self.get_progress_popup(lines))
        code.extend(self.get_rebinds(hotkeys_to_group, hotkeys_phrases))
        code.extend([self.get_hide_timer(), "Return"])

        return code

    def beautify(self, line):
        return line.replace("_", " ")

    def get_group_displaytext(self, group):
        lines = [
                self.beautify(group["name"]) + ":",
                "",
            ]
        for grp in sorted(group.get("groups", []), key=lambda x: x["name"]):
            lines.append("{key} ==> {name}".format(key=grp["hotkey"],
                name=self.beautify(grp["name"])))

        if len(group.get("groups", [])) > 0\
                and len(group.get("phrases", [])) > 0:
            lines.append("")

        for phr in sorted(group.get("phrases", []), key=lambda x: x["name"]):
            lines.append("{key} ==> {name}".format(key=phr["hotkey"],
                name=self.beautify(phr["name"])))

        lines.append("")
        lines.append("{key} ==> (Cancel hotkeys)".format(
            key=self.layout["hotkey_cancel"]))

        return lines

    def get_rebinds(self, hotkeys_to_group, hotkeys_phrases):
        hotkeys_to_subnames = {k:self.get_group_subroutine_name(v)
                for k,v in hotkeys_to_group.iteritems()}

        hotkeys_phrases.append(self.layout["hotkey_cancel"])

        # disable all hotkeys not in this group except for the global cancel
        code = map(lambda k: self.get_hotkey(k,
            hotkeys_to_subnames.get(k, self.sub_names["empty"])),
            list(self.all_hotkeys - set(hotkeys_phrases)))

        # all phrase hotkeys reset the overlay (also the cancel hotkey does)
        for k in hotkeys_phrases:
            code.append(self.get_hotkey(k, self.sub_names["reset"]))

        return code

    def get_hotkey(self, hotkey, bind):
        return "Hotkey, ~{key}, {bind}".format(key=hotkey, bind=bind)

    def get_group_subroutine_name(self, name):
        return "Group_{}".format(name)

    def get_subroutine_hide(self):
        return [
                "{}:".format(self.sub_names["hide"]),
                "Progress, Off",
                "SetTimer, {}, Off".format(self.sub_names["hide"]),
                "Return",
            ]

    def get_subroutine_init(self):
        code = ["{}:".format(self.sub_names["init"])]

        for k in self.all_hotkeys:
            code.append(self.get_hotkey(k, self.sub_names["empty"]))

        code.append("TrayTip, Dota 2 VGS Overlay, VGS Overlay for Dota 2 "
                "enabled`, please use CTRL-F12 to disable/enable the overlay "
                "when in Dota 2."
                "`n`nNote that you need to have this script running whenever "
                "you want to have the overlay enabled.")

        code.append(self.get_hotkey(self.config["hotkey_toggle"],
            self.sub_names["toggle"]))

        code.append("vgs_overlay_enabled := true")

        code.append("Return")
        return code

    def get_subroutine_toggle(self):
        code = [
                "{}:".format(self.sub_names["toggle"]),
                "If (vgs_overlay_enabled)",
                "{",
                "vgs_overlay_enabled := false",
                "TrayTip, Dota 2 VGS Overlay, VGS Overlay disabled, 10",
            ]
        for k in self.all_hotkeys:
            code.append(self.get_hotkey(k, self.sub_names["empty"]))

        code.extend([
                "}",
                "else {",
                self.get_call_sub(self.sub_names["reset"]),
                "vgs_overlay_enabled := true",
                "TrayTip, Dota 2 VGS Overlay, VGS Overlay enabled, 10",
                "}",
            ])
        code.append("Return")
        return code

    def get_subroutine_reset(self):
        code = [
                "{}:".format(self.sub_names["reset"]),
                self.get_call_sub(self.sub_names["hide"]),
            ]

        for k in self.all_hotkeys - set(self.layout["hotkey"]):
            code.append(self.get_hotkey(k, self.sub_names["empty"]))

        code.append(self.get_hotkey(self.layout["hotkey"],
            self.get_group_subroutine_name(self.config["root_group"])))

        code.append("Return")

        return code

    def get_subroutine_empty(self):
        return ["{}:".format(self.sub_names["empty"]), "Return"]

    def get_call_sub(self, subname):
        return "Gosub, {}".format(subname)


