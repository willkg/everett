import os
import subprocess
import sys


def main():
    for fn in os.listdir('code/'):
        if not fn.endswith('.py'):
            continue

        print 'Running %s...' % fn
        subprocess.check_output(['python', 'code/%s' % fn])


if __name__ == '__main__':
    sys.exit(main())
