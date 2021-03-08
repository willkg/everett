import os
import subprocess
import sys


def main():
    # FIXME(willkg): This is written to run on my machine.
    for fn in os.listdir("code/"):
        if not fn.endswith(".py"):
            continue

        # FIXME(willkg): We should do this better but it's running in the
        # environment that's running Sphinx.
        if fn.endswith("_3.py"):
            print("Skipping %s (python3)..." % fn)
            continue

        print("Running %s..." % fn)
        subprocess.check_output(["python", "code/%s" % fn])


if __name__ == "__main__":
    sys.exit(main())
