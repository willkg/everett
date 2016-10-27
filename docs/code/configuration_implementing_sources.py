from everett import NO_VALUE
from everett.manager import listify


class NoOpEnv(object):
    def get(self, key, namespace=None):
        # The namespace is either None, a string or a list of
        # strings. This converts it into a list.
        namespace = listify(namespace)

        # FIXME: Your code to extract the key in namespace here.

        # At this point, the key doesn't exist in the namespace
        # for this environment, so return a ``NO_VALUE``.
        return NO_VALUE
