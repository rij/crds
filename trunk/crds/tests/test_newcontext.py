"""This module contains doctests and unit tests which exercise some of the more
complex features of the basic rmap infrastructure.
"""

from __future__ import division # confidence high
from __future__ import with_statement
from __future__ import print_function

import os, os.path
from pprint import pprint as pp

from crds import rmap, log, exceptions, newcontext, diff, pysh, tests
from crds.tests import CRDSTestCase, test_config

from nose.tools import assert_raises, assert_true

# ==================================================================================

def tst_fake_name():
    """
    Fake names are only used by crds.newcontext when it is run from the command line.

    >>> old_state = test_config.setup()
    >>> os.environ["CRDS_MAPPATH_SINGLE"] = tests.TEST_DATA

    >>> newcontext.fake_name("data/hst.pmap")
    './hst_0003.pmap'
    
    >>> newcontext.fake_name("data/hst_cos_0001.imap")
    './hst_cos_0001.imap'

    >>> newcontext.fake_name("data/hst_cos_deadtab_9999.rmap")
    './hst_cos_deadtab_10000.rmap'

    >>> test_config.cleanup(old_state)
    """

def tst_new_context():
    """
    >>> old_state = test_config.setup()
    >>> os.environ["CRDS_MAPPATH_SINGLE"] = tests.TEST_DATA

    >>> newcontext.NewContextScript("newcontext.py hst.pmap data/hst_cos_deadtab_9999.rmap data/hst_acs_imphttab_9999.rmap")()
    CRDS  : INFO     Replaced 'hst_acs_imphttab.rmap' with 'data/hst_acs_imphttab_9999.rmap' for 'imphttab' in 'data/hst_acs.imap' producing './hst_acs_10000.imap'
    CRDS  : INFO     Replaced 'hst_cos_deadtab.rmap' with 'data/hst_cos_deadtab_9999.rmap' for 'deadtab' in 'data/hst_cos.imap' producing './hst_cos_0001.imap'
    CRDS  : INFO     Replaced 'data/hst_acs.imap' with './hst_acs_10000.imap' for 'ACS' in 'hst.pmap' producing './hst_0003.pmap'
    CRDS  : INFO     Replaced 'data/hst_cos.imap' with './hst_cos_0001.imap' for 'COS' in 'hst.pmap' producing './hst_0003.pmap'
    CRDS  : INFO     Adjusting name 'hst_acs_10000.imap' derived_from 'hst_acs.imap' in './hst_acs_10000.imap'
    CRDS  : INFO     Adjusting name 'hst_cos_0001.imap' derived_from 'hst_cos.imap' in './hst_cos_0001.imap'
    CRDS  : INFO     Adjusting name 'hst_0003.pmap' derived_from 'hst.pmap' in './hst_0003.pmap'
    0

    >>> pp([difference[-1] for difference in diff.mapping_diffs("data/hst.pmap", "./hst_0003.pmap")])
    ["replaced 'w3m17170j_imp.fits' with 'xb61855jj_imp.fits'",
     "replaced 's7g1700gl_dead.fits' with 's7g1700gm_dead.fits'",
     "replaced 'hst_acs_imphttab.rmap' with 'data/hst_acs_imphttab_9999.rmap'",
     "replaced 'hst_cos_deadtab.rmap' with 'data/hst_cos_deadtab_9999.rmap'",
     "replaced 'data/hst_acs.imap' with './hst_acs_10000.imap'",
     "replaced 'data/hst_cos.imap' with './hst_cos_0001.imap'"]

    >>> pysh.sh("rm \./*\.[pir]map")
    0

    >>> test_config.cleanup(old_state)
    """

class TestNewContext(CRDSTestCase):

    '''
    def test_get_imap_except(self):
        r = rmap.get_cached_mapping("hst.pmap")
        with self.assertRaises(exceptions.CrdsUnknownInstrumentError):
            r.get_imap("foo")
    '''

# ==================================================================================


def main():
    """Run module tests,  for now just doctests only."""
    from crds.tests import test_newcontext
    import unittest, doctest

    suite = unittest.TestLoader().loadTestsFromTestCase(TestNewContext)
    unittest.TextTestRunner().run(suite)

    old_state = test_config.setup()
    result = doctest.testmod(test_newcontext)
    test_config.cleanup(old_state)

    return result

if __name__ == "__main__":
    print(main())
