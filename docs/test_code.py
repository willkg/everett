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
