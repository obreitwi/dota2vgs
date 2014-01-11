#!/usr/bin/env python2
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

from __future__ import print_function

import glob
import os.path as osp
import itertools
import sys

try:
    from docopt import docopt
except ImportError:
    current_dir = osp.abspath(osp.dirname(sys.argv[0]))
    sys.path.append(osp.join(current_dir, "dependencies"))
    from docopt import docopt


from . import SheetMaker, Composer, AutohotkeyWriter
from .version import __version__

__doc__ =\
"""
    Usage:
        {prgm}  vgs [-c <filename>]... [-l <filename>]...
                [-y <filename>] [-o <filename>]
        {prgm}  sheet [-y <filename>] [-o <filename>]
        {prgm}  overlay [-y <filename>] [-o <filename>]

    Modes:
        (default) :   Generate the vgs file.

        sheet :     Make a cheat sheet of all the commands present in the layout
                    file.

    Options:
        -c --cfg-file <filename>
            Specify .cfg files from which to read existing bindings. The
            files will be read in the order specified. Therefore it is
            important to match the order in which they are sourced.
            [default: autoexec.cfg config.cfg]

        -l --lst-file <filename>
            Specify .lst files from which to read existing bindings.
            Typically keybinds from the Dota 2 are saved in those The files
            will be read in the order specified. Therefore it is important
            to match the order in which they are sourced.
            [default: dotakeys_personal.lst]

        -y --layout-file <filename>
            Specify YAML-file containing the layout used to create the VGS.
            [default: layout.yaml]

        -o --output-file <filename>
            Specify output filename.

        --usage
            Print usage only.

        -h --help
            Show this help message.

""".format(prgm=osp.basename(sys.argv[0]))



def open_files(filenames, mode="r"):
    return [open(fn, mode=mode) for fn in filenames]


def main_loop():
    args = docopt(__doc__, argv=sys.argv[1:], version=__version__)

    layout_file = open(args["--layout-file"], mode="r")

    if args["sheet"]:
        sheet_filename = args["--output-file"]
        if sheet_filename is None:
            sheet_filename = "sheet.txt"

        sheet_file = open(sheet_filename, "w")
        SheetMaker(layout_file, sheet_file)

        sheet_file.close()

    elif args["overlay"]:
        overlay_filename = args["--output-file"]
        if overlay_filename is None:
            overlay_filename = "vgs_overlay.ahk"

        overlay_file = open(overlay_filename, "w")

        writer = AutohotkeyWriter()
        writer.set_layout_from_file(layout_file)
        writer.write(overlay_file)

        overlay_file.close()

    elif args["vgs"]:
        cfg_files   = open_files(args["--cfg-file"], mode="r")
        lst_files   = open_files(args["--lst-file"], mode="r")
        output_filename = args["--output-file"]
        if output_filename is None:
            output_filename = "vgs.cfg"
        output_file = open(output_filename, mode="w")
        Composer(
            cfg_files=cfg_files,
            lst_files=lst_files,
            layout_file=layout_file,
            output_file=output_file)

        for f in itertools.chain(cfg_files, lst_files, [output_file]):
            f.close()
    layout_file.close()

