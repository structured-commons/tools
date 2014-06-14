#! /usr/bin/env python
from distutils.core import setup
import sc

setup(
    name = "SC",
    version = sc.version,
    author = "Structured Commons Technical Steering Committee",
    author_email = "sc-discuss@structured-commons.org",
    url = "https://github.com/structured-commons/tools",
    license = "Unlicense (Public Domain)",
    packages = ["sc"],
    scripts = ["fptool.py", "objtool.py"]
    )
