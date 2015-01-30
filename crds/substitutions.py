"""This module supports conditional substitutions on reference file header parameters
at reference file submission time.  It's principle function is to expand wildcards into
explicit matching patterns in the CRDS rmaps.

CRDS defines a substitutions file with a dictionary of this form:

    { instrument : { header_key :  { condition_expr: expansion } } }

When a reference file is submitted,  the required parameters are located in the substitutions
dictionary, if applicable.   For each `header_key`,  `condition_expr` expressions are evaluated
with respect to the reference file header.  If the `condition_expr` is True,  the value of the
`header_key` is literally replaced with `expansion` for the purpose of rmap matching.  The file
is not modified,  the rmap reinterprets the file.
    
An example substitution rule is:

    { "CCDGAIN" : { "DETECTOR='WFC3' and CCDGAIN='-999'" : "1.0|2.0|4.0|8.0" }

CRDS defines a function:

   expanded_header = expand_wildcards(instrument, header)

which will interpret the rules to expand appropriate values in header.
"""

import os.path

from crds import log, utils

# ============================================================================

HERE = os.path.dirname(__file__) or "."
    
# ============================================================================    

class HeaderExpander(object):
    """HeaderExpander applies a set of expansion rules to a header.  It 
    compiles the applicability expression of each rule.
    
    >>> expansions = {
    ...  'FILTER1' : { "DETECTOR=='HRC' and FILTER1=='ANY'": 'F555W|F775W|F625W'},
    ...  'OBSTYPE' : { "DETECTOR=='HRC' and FILTER1=='G800L' and OBSTYPE=='ANY'": 'IMAGING|CORONAGRAPHIC'},
    ... }
    >>> expander = HeaderExpander(expansions)

    >>> header = { "DETECTOR":"HRC", "FILTER1":"ANY" }
    >>> expander.expand(header)
    {'DETECTOR': 'HRC', 'FILTER1': 'F555W|F775W|F625W'}

    >>> header = { "DETECTOR":"HRC", "FILTER1":"G280L", "OBSTYPE":"ANY" }
    >>> expander.expand(header)
    {'OBSTYPE': 'ANY', 'DETECTOR': 'HRC', 'FILTER1': 'G280L'}

    >>> header = { "DETECTOR":"HRC", "FILTER1":"G800L", "OBSTYPE":"ANY" }
    >>> expander.expand(header)
    {'OBSTYPE': 'IMAGING|CORONAGRAPHIC', 'DETECTOR': 'HRC', 'FILTER1': 'G800L'}
    """
    def __init__(self, expansion_mapping, expansion_file="(none)"):
        self.mapping = {}
        for var, substitutes in expansion_mapping.items():
            for expr, replacement in substitutes.items():
                self.mapping[(var, expr)] = (replacement, compile(expr, expansion_file, "eval"))  # compiled code is from static file.
        self._required_keys = self.required_keys()

    def expand(self, header):
        """Given a reference matching `header`,  evaluate all the expansion rules with respect
        to it and return a modified copy which include substitutions.
        """
        header = dict(header)
        expanded = dict(header)
        log.verbose("Unexpanded header", self.required_header(header))
        for (var, expr), (expansion, compiled) in self.mapping.items():
            try:
                applicable = eval(compiled, {}, header)  # compiled code is from static file.
            except Exception, exc:
                log.verbose_warning("Header expansion for",repr(expr), 
                            "failed for", repr(str(exc)))
                continue
            if applicable:
                log.verbose("Exapanding", repr(expr), "yields", 
                            var + "=" + repr(expansion))
                expanded[var] = expansion
            else:
                log.verbose("Expanding", repr(expr), "doesn't apply.")
        log.verbose("Expanded header", self.required_header(expanded))
        return expanded
    
    def required_keys(self):
        """Return the list of header keys required to evaluate all substitutions conditions."""
        required = []
        for (_var, expr) in self.mapping:
            required.extend(required_keys(expr))
        return sorted(set(required))
    
    def required_header(self, header):
        """Ensure all required keywords for evaluating expansions are defined in `header`, at lest
        with a value of UNDEFINED.
        """
        return sorted({ key: header.get(key, "UNDEFINED") for key in self._required_keys }.items())
        
def required_keys(expr):
    """
    >>> required_keys("VAR1=='VAL1' and VAR2=='VAL2' and VAR3=='VAL3'")
    ['VAR1', 'VAR2', 'VAR3']
    """
    return sorted(set([term.split("=")[0].strip() for term in expr.split("and")]))
    

class ReferenceHeaderExpanders(dict):
    """Container class for all expanders for all instruments of an observatory."""
    
    @classmethod
    @utils.cached
    def load(cls, observatory):
        """Load the substution rules from the observatory package directory."""
        pkg = utils.get_observatory_package(observatory)
        rules = utils.evalfile(pkg.HERE + "/substitutions.dat")
        expanders = ReferenceHeaderExpanders()
        for instrument in rules:
            expanders[instrument] = HeaderExpander(rules[instrument])
        return expanders

    def expand_wildcards(self, rmapping, header):
        """Transform header values according to expansion rules."""
        try:
            header = self[rmapping.instrument].expand(header)
        except KeyError:
            header = dict(header)
        # log.warning("Unknown instrument", repr(instrument), " in expand_wildcards().")
        return header

def expand_wildcards(rmapping, header):
    """Expand substitution values in `header` with respect to the instrument and observatory
    defined in `rmapping`.
    """
    expanders = ReferenceHeaderExpanders.load(rmapping.observatory)
    return expanders.expand_wildcards(rmapping, header)
