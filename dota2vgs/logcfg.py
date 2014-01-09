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

import logging
import os

LOGNAME = "SEMf"
log = None

default_verbose_formatter = logging.Formatter("%(asctime)s %(levelname)s "
        "%(funcName)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%y-%m-%d %H:%M:%S")
default_formatter = logging.Formatter("%(asctime)s %(levelname)s: "
        "%(message)s", datefmt="%y-%m-%d %H:%M:%S")


formatter_in_use = default_formatter # allows switching of the global formatter
loglevel_in_use = "INFO"               # same for loglevels


log = logging.getLogger(LOGNAME)
log.setLevel(logging.DEBUG)


default_handler_stream = None
default_handler_file = None


def set_loglevel(lg, lvl):
    lg.setLevel(getattr(logging, lvl.upper()))


def set_loglevel_stream(lvl="INFO"):
    set_loglevel(default_handler_stream, lvl)


def set_loglevel_file(lvl="DEBUG"):
    set_loglevel(default_handler_file, lvl)


def add_handler(type_, handler_kwargs=None, loglevel=None,
                formatter=None):
    kwargs = {}
    if handler_kwargs is not None:
        kwargs.update(handler_kwargs)
    handler = type_(**kwargs)

    # allow dynamic defaults
    if formatter is None:
        formatter = formatter_in_use
    if loglevel is None:
        loglevel = loglevel_in_use

    handler.setFormatter(formatter)
    set_loglevel(handler, loglevel)
    log.addHandler(handler)
    return handler


def add_stream_handler(**kwargs):
    """
        Adds new stream handler.

        **kwargs are passed to `add_handler`.
    """
    return add_handler(logging.StreamHandler)


def add_file_handler(filename, mode="a", **kwargs):
    """
        Adds new file handler with specified filename and mode.

        **kwargs are passed to `add_handler`.
    """
    handler_kwargs = kwargs.setdefault("handler_kwargs", {})
    handler_kwargs["filename"] = filename
    handler_kwargs["mode"] = mode
    return add_handler(logging.FileHandler, **kwargs)


def make_verbose():
    global formatter_in_use
    formatter_in_use = default_verbose_formatter
    verbose_loglevel = "DEBUG"
    loglevel_in_use = verbose_loglevel
    set_loglevel(log, verbose_loglevel)
    for h in log.handlers:
        set_loglevel(h, verbose_loglevel)
        h.setFormatter(default_verbose_formatter)


if "DEBUG" in os.environ:
    formatter_in_use = default_verbose_formatter

default_handler_stream = add_stream_handler(
        loglevel="INFO")

if "DEBUG" in os.environ:
    make_verbose()

for i in range(3):
    log.debug("-" * 80)
