# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pytest


@pytest.fixture
def datadir():
    return os.path.join(os.path.dirname(__file__), 'data')
