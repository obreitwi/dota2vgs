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

