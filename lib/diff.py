"""This module differences two CRDS reference or mapping files on the local
system.   It supports specification of the files using only the basenames or
a full path.   Currently it operates on mapping, FITS, or text files.
"""
import os

from crds import rmap, log, pysh, cmdline

# ============================================================================
        
def mapping_diffs(file1, file2):
    """Return the logical differences between CRDS mappings named `file1` 
    and `file2`.
    """
    assert rmap.is_mapping(file1), \
        "File " + repr(file1) + " is not a CRDS mapping."
    assert rmap.is_mapping(file2), \
        "File " + repr(file2) + " is not a CRDS mapping."
    assert os.path.splitext(file1)[-1] == os.path.splitext(file2)[-1], \
        "Files " + repr(file1) + " and " + repr(file2) + \
        " are not the same kind of CRDS mapping:  .pmap, .imap, .rmap"
    map1 = rmap.fetch_mapping(file1, ignore_checksum=True)
    map2 = rmap.fetch_mapping(file2, ignore_checksum=True)
    differences = map1.difference(map2)
    return differences

def diff_action(diff):
    """Return 'add', 'replace', or 'delete' based on action represented by
    difference tuple `d`.   Append "_rule" if the change is a Selector.
    """
    if "replace" in diff[-1]:
        result = "replace"
    elif "add" in diff[-1]:
        result = "add"
    elif "delete" in diff[-1]:
        result = "delete"
    elif "different classes" in diff[-1]:
        result = "class_difference"
    else:
        raise ValueError("Bad difference action: "  + repr(diff))
    if "Selector" in diff[-1]:
        result += "_rule"
    return result

def mapping_difference(observatory, file1, file2, primitive_diffs=False, check_diffs=False):
    """Print the logical differences between CRDS mappings named `file1` 
    and `file2`.  
    
    IFF primitive_differences,  recursively difference any replaced files found
    in the top level logical differences.
    
    IFF check_diffs, issue warnings about critical differences.   See
    mapping_check_diffs().
    """
    differences = mapping_diffs(file1, file2)
    if primitive_diffs:
        for pair in mapping_pairs(differences):
            log.write("="*80)
            log.write(pair)
            text_difference(observatory, pair[0], pair[1])
    for diff in differences:
        diff = unquote_diff(diff)
        if primitive_diffs:
            log.write("="*80)
        log.write(diff)
        if primitive_diffs:
            if "replaced" in diff[-1]:
                old, new = diff_replace_old_new(diff)
                difference(observatory, old, new, primitive_diffs=primitive_diffs)
    if check_diffs:
        mapping_check_diffs_core(differences)

def mapping_pairs(differences):
    """Return the sorted list of all mapping tuples found in differences."""
    pairs = set()
    for diff in differences:
        for pair in diff:
            if len(pair) == 2 and rmap.is_mapping(pair[0]):
                pairs.add(pair)
    return sorted(pairs)
        
def unquote_diff(diff):
    """Remove repr str quoting in `diff` tuple."""
    return diff[:-1] + (diff[-1].replace("'",""),)

def unquote(name):
    """Remove string quotes from simple `name` repr."""
    return name.replace("'","").replace('"','')

def diff_replace_old_new(diff):
    """Return the (old, new) filenames from difference tuple `diff`."""
    _replaced, old, _with, new = diff[-1].split()
    return unquote(old), unquote(new)
    
# ============================================================================

def mapping_check_diffs(mapping, derived_from):
    """Issue warnings for *deletions* in self relative to parent derived_from
    mapping.  Issue warnings for *reversions*,  defined as replacements which
    where the replacement is older than the original,  as defined by the names.   
    
    This is intended to check for missing modes and for inadvertent reversions
    to earlier versions of files.   For speed and simplicity,  file time order
    is currently determined by the names themselves,  not file contents, file
    system,  or database info.
    """
    mapping = rmap.asmapping(mapping, cached="readonly")
    derived_from = rmap.asmapping(derived_from, cached="readonly")
    log.info("Checking derivation diffs from", repr(derived_from.basename), "to", repr(mapping.basename))
    diffs = derived_from.difference(mapping)
    return mapping_check_diffs_core(diffs)

def mapping_check_diffs_core(diffs):
    """Perform the core difference checks on difference tuples `diffs`."""
    categorized = sorted([ (diff_action(d), d) for d in diffs ])
    for action, msg in categorized:
        if action == "add":
            log.verbose("In", _diff_tail(msg)[:-1], msg[-1])
        elif "rule" in action:
            log.warning("Rule change at", _diff_tail(msg)[:-1], msg[-1])
        elif action == "replace":
            old_val, new_val = diff_replace_old_new(msg)
            if newer(new_val, old_val):
                log.verbose("In", _diff_tail(msg)[:-1], msg[-1])
            else:
                log.warning("Reversion at", _diff_tail(msg)[:-1], msg[-1])
        elif action == "delete":
            log.warning("Deletion at", _diff_tail(msg)[:-1], msg[-1])
        else:
            raise ValueError("Unexpected difference action:", difference)

def _diff_tail(msg):
    """`msg` is an arbitrary length difference "path",  which could
    be coming from any part of the mapping hierarchy and ending in any kind of 
    selector tree.   The last item is always the change message: add, replace, 
    delete <blah>.  The next to last should always be a selector key of some kind.  
    Back up from there to find the first mapping tuple.
    """
    tail = []
    for part in msg[::-1]:
        if isinstance(part, tuple) and len(part) == 2 and isinstance(part[0], str) and part[0].endswith("map"):
            tail.append(part[1])
            break
        else:
            tail.append(part)
    return tuple(reversed(tail))

def newstyle_name(name):
    """Return True IFF `name` is a CRDS-style name, e.g. hst_acs.imap
    
    >>> newstyle_name("s7g1700gl_dead.fits")
    False
    >>> newstyle_name("hst.pmap")
    True
    >>> newstyle_name("hst_acs_darkfile_0001.fits")
    True
    """
    return name.startswith(("hst", "jwst", "tobs"))

def newer(name1, name2):
    """Determine if `name1` is a more recent file than `name2` accounting for 
    limited differences in naming conventions. Official CDBS and CRDS names are 
    comparable using a simple text comparison,  just not to each other.
    
    >>> newer("s7g1700gl_dead.fits", "hst_cos_deadtab_0001.fits")
    False
    >>> newer("hst_cos_deadtab_0001.fits", "s7g1700gl_dead.fits")
    True
    >>> newer("s7g1700gl_dead.fits", "bbbbb.fits")
    True
    >>> newer("bbbbb.fits", "s7g1700gl_dead.fits")
    False
    >>> newer("hst_cos_deadtab_0001.rmap", "hst_cos_deadtab_0002.rmap")
    False
    >>> newer("hst_cos_deadtab_0002.rmap", "hst_cos_deadtab_0001.rmap")
    True
    """
    if newstyle_name(name1):
        if newstyle_name(name2): # compare CRDS names
            result = name1 > name2
        else:  # CRDS > CDBS
            result = True
    else:
        if newstyle_name(name2):  # CDBS < CRDS
            result = False
        else:  # compare CDBS names
            result = name1 > name2
    log.verbose("Comparing filename time order:", repr(name1), ">", repr(name2), "-->", result)
    return result

# ============================================================================
        
def fits_difference(observatory, file1, file2):
    """Run fitsdiff on files named `file1` and `file2`.
    """
    assert file1.endswith(".fits"), \
        "File " + repr(file1) + " is not a FITS file."
    assert file2.endswith(".fits"), \
        "File " + repr(file2) + " is not a FITS file."
    _loc_file1 = rmap.locate_file(file1, observatory)
    _loc_file2 = rmap.locate_file(file2, observatory)
    pysh.sh("fitsdiff ${_loc_file1} ${_loc_file2}")

def text_difference(observatory, file1, file2):
    """Run UNIX diff on two text files named `file1` and `file2`.
    """
    assert os.path.splitext(file1)[-1] == os.path.splitext(file2)[-1], \
        "Files " + repr(file1) + " and " + repr(file2) + " are of different types."
    _loc_file1 = rmap.locate_file(file1, observatory)
    _loc_file2 = rmap.locate_file(file2, observatory)
    pysh.sh("diff -b -c ${_loc_file1} ${_loc_file2}")

def difference(observatory, file1, file2, primitive_diffs=False, check_diffs=False):
    """Difference different kinds of CRDS files (mappings, FITS references, etc.)
    named `file1` and `file2` against one another and print out the results 
    on stdout.
    """
    if rmap.is_mapping(file1):
        mapping_difference(observatory, file1, file2, primitive_diffs=primitive_diffs, check_diffs=check_diffs)
    elif file1.endswith(".fits"):
        fits_difference(observatory, file1, file2)
    else:
        text_difference(observatory, file1, file2)

# =============================================================================
 
class DiffScript(cmdline.Script):
    """Python command line script to difference mappings or references."""
    
    description = """Difference CRDS mapping or reference files."""
    
    def add_args(self):
        """Add diff-specific command line parameters."""
        self.add_argument("old_file",  help="Prior file of difference.""")
        self.add_argument("new_file",  help="New file of difference.""")
        self.add_argument("-P", "--primitive-diffs", dest="primitive_diffs",
            help="Include primitive differences on replaced files.", 
            action="store_true")
        self.add_argument("-K", "--check-diffs", dest="check_diffs",
            help="Issue warnings about new rules, deletions, or reversions.",
            action="store_true")

    def main(self):
        """Perform the differencing."""
        difference(self.observatory, self.args.old_file, self.args.new_file, 
                   primitive_diffs=self.args.primitive_diffs, check_diffs=self.args.check_diffs)

if __name__ == "__main__":
    DiffScript()()
