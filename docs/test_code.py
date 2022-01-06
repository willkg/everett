# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Tests the code in the ../examples/ directory before including it in the docs.
"""

import os
import subprocess
import sys


def main():
    # FIXME(willkg): This is written to run on my machine.
    for fn in os.listdir("../examples/"):
        if not fn.endswith(".py"):
            continue

        print("Running %s..." % fn)
        subprocess.check_output(["python", "../examples/%s" % fn])


if __name__ == "__main__":
    sys.exit(main())
