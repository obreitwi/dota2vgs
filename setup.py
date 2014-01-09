
from setuptools import setup

import os
import os.path as osp

execfile(osp.join(osp.dirname(osp.abspath(__file__)), "dota2vgs", "version.py"))

setup(
        name="dota2vgs",
        version=".".join(map(str, __version__)),
        install_requires=["docopt>=0.5", "PyYAML>=3.10"],
        packages=["dota2vgs"],
        url="http://github.com/obreitwi/dota2vgs",
        license="MIT",
        entry_points = {
            "console_scripts" : [
                    "d2vgs = dota2vgs.main:main_loop"
                ]
            },
        zip_safe=True,
    )


