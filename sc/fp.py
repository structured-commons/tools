"""Structured Commons fingerprinting utilities."""

from __future__ import print_function
import base64
import codecs
import hashlib
import re
import sys

if hasattr(int, 'from_bytes'):
    # python 3
    long = int
    def bytes_to_long(barray):
        return int.from_bytes(barray, 'big')
    def long_to_bytes(val):
        return val.to_bytes(32, 'big')
else:
    # python 2:
    def bytes_to_long(barray):
        v = codecs.encode(barray, 'hex_codec')
        return long(v, base=16)
    def long_to_bytes(val):
        v = '%064x' % val
        f = codecs.decode(v, 'hex_codec')
        assert len(f) == 32
        return bytearray(f)

def fletcher(barray):
    """Return the two Fletcher-16 sums of a byte array."""
    assert isinstance(barray, bytes) or isinstance(barray, bytearray)
    a = 0
    b = 0
    for c in barray:
        a = (a + c) % 255
        b = (a + b) % 255
    return (a, b)

def validate_name(name):
    """Ensure a name is valid.

    A valid name must be a character string, not empty and not contain
    codes between 0 and 31 inclusive.
    """
    # a name is a character string
    assert isinstance(name, str) or isinstance(name, type(u'')), \
           "name %r is not a string" % name

    assert len(name) > 0 # name must not be empty
    for c in name:
        assert ord(c) > 31, \
            "invalid character %r (code %d) found in name %r" % (c, ord(c), name)


class fingerprintable(object):

    """Base class for Python objects that can be fingerprinted."""

    def visit(self, v):
        """Visitor dispatch method to be implemented by sub-classes.

        This must call either:

        - v.enter_file(sz), followed by
          v.visit_data(b) zero or more times, followed by
          v.leave_file() once; or

        - v.enter_dict() once, followed by
          v.visit_entry(name, t, obj) zero or more times, followed by
          v.leave_dict() once.

        See the help of class ``visitor`` for details.
        """
        pass

class compute_visitor(object):
    """Visitor to compute fingerprints over abstract object trees.

    It applies to objects that implement the ``fingerprintable`` interface.

    compute_visitor :: Fingerprintable a => a -> fingerprint
    """

    def __init__(self, verbose = False):
        """Instantiate a visitor.

        If verbose is non-false, the visitor prints detail on the
        standard output.
        """
        self._v = verbose

    def _finish(self):
        s = self._h.digest()
        if isinstance(s, str): # python 2 compat
            s = bytearray(s)
        self._fp = s

    def fingerprint(self):
        """Return the fingerprint computed by this visitor."""
        return fingerprint(self._fp)

    def enter_file(self, sz):
        """Start fingerprinting an object file."""
        self._sz = sz
        self._cnt = 0
        self._h = hashlib.sha256()
        self._h.update(b's')
        self._h.update(bytearray('%d' % sz, 'ascii'))
        self._h.update(b'\0')

    def visit_data(self, b):
        """Fingerprint some more data from a file previously entered."""
        self._cnt += len(b)
        self._h.update(b)

    def leave_file(self):
        """Finish fingerprinting an object file."""
        assert self._cnt == self._sz
        self._finish()
        if self._v:
            print("file, sz %d (%s)" % (self._sz, fingerprint(self._fp).compact()), file=sys.stderr)

    def enter_dict(self):
        """Start fingerprinting an object dictionary."""
        self._ents = {}
        if self._v:
            print("dictionary, entering:", file=sys.stderr)

    def visit_entry(self, name, t, obj):
        """Fingerprint some more data from a dictionary previously entered.

        Arguments:
        name -- the entry name in the dictionary (string)
        t -- either 't', 's' or 'l' depending on the entity
        obj -- either a fingerprint or another fingerprintable object
        """

        if self._v:
            print("entry %r: " % name, end='', file=sys.stderr)

        # name must have valid form
        validate_name(name)

        # names must be unique in dictionary
        assert name not in self._ents, "duplicate name %r" % name

        if (t == 'l') and hasattr(obj, 'binary'):
            self._ents[name] = (t, obj.binary())
            if self._v:
                print("fingerprint (%s)" % obj.compact(), file=sys.stderr)

        elif t in ['s', 't'] and isinstance(obj, fingerprintable):
            fpv = compute_visitor(self._v)
            obj.visit(fpv)
            self._ents[name] = (t, fpv._fp)

        else:
            print(type(t), t, obj, type(obj), file=sys.stderr)
            raise TypeError("unknown entity type in dictionary")

    def leave_dict(self):
        """Finish fingerprinting an object dictionary."""

        keys = sorted(self._ents.keys())
        buf = bytearray()
        for k in keys:
            t, fp = self._ents[k]
            buf += bytearray(t, 'ascii')
            buf += b':'
            buf += bytearray(k, 'utf-8')
            buf += b'\0'
            buf += fp
        self._h = hashlib.sha256()
        self._h.update(b't')
        self._h.update(bytearray('%d' % len(buf), 'ascii'))
        self._h.update(b'\0')
        self._h.update(buf)
        self._finish()
        if self._v:
            print("leaving dictionary (%s)" % fingerprint(self._fp).compact(), file = sys.stderr)


class fingerprint(object):
    """fingerprint(fingerprintable) -> compute fingerprint of object
    fingerprint(str) -> parse fingerprint representation
    fingerprint(fingerprint or bytearray) -> copy fingerprint
    """

    def __init__(self, obj):
        """Initialize a fingerprint. See help(fingerprint) for signature."""

        if hasattr(obj, 'binary'): # assume already a fingerprint
            v = obj.binary()
            assert len(v) == 32
            self._value = v

        elif isinstance(obj, int) or isinstance(obj, long):
            self._value = long_to_bytes(obj)

        elif isinstance(obj, str) or isinstance(obj, type(u'')):
            fp, fmt, errmsg = parse(obj)
            if fp is None:
                raise RuntimeError(errmsg)
            self._value = fp._value

        elif (isinstance(obj, bytearray) or isinstance(obj, bytes)) and len(obj) == 32:
            self._value = bytearray(obj)

        elif isinstance(obj, fingerprintable):
            v = compute_visitor()
            obj.visit(v)
            self._value = v._fp

        else:
            raise TypeError("a string, fingerprint or fingerprintable is required")

    def __int__(self):
        """Return the binary representation of the fingerprint as a long integer."""
        return bytes_to_long(self._value)

    __long__ = __int__

    def __repr__(self):
        """Pretty print a fingerprint object."""
        return "<%s>" % self.compact()

    def __cmp__(self, other):
        """Compare two fingerprints."""
        return cmp(self._value, other._value)

    def binary(self):
        """Returns the binary representation of the fingerprint as a byte array."""
        return bytearray(self._value)

    def carray(self):
        """Returns a C array definition equivalent to the fingerprint."""
        buf = 'char fp[32] = "'
        for c in self._value:
            if c == ord('\\'):
                buf += '\\\\'
            elif c == ord('"'):
                buf += '\\"'
            elif c < 32 or c > 126:
                buf += '\\x%02x' % c
            else:
                buf += chr(c)
        buf += '";'
        return str(buf)

    def hex(self, split = None):
        """Returns the hexadecimal representaiton of the fingerprint.

        The optional 'split' argument introduces hyphens for increased
        readability.
        """
        x = self.binary()
        r = codecs.encode(x, 'hex_codec').decode('ascii')

        if split is None:
            split = 8
        if split == 0:
            split = len(r)
        r = '-'.join((r[i:i+split] for i in range(0, len(r), split)))

        return str(r)

    def _append_fletcher(self):
        x = self.binary()
        a, b = fletcher(x)
        x.append(a)
        x.append(b)
        return x


    def compact(self):
        """Returns the compact representation of the fingerprint.

        The compact representation is derived by the prefix 'fp:'
        followed by a Base64 encoding of the fingerprint byte
        representation and a Fletcher-16 checksum.
        """
        x = self._append_fletcher()
        r = base64.urlsafe_b64encode(x)
        r = r.decode('ascii').rstrip('=')
        return str('fp:' + r)

    def long(self, split = None):
        """Returns the long representation of the fingerprint.

        The long representation is derived by the prefix 'fp::'
        followed by a Base32 encoding of the fingerprint byte
        representation and a Fletcher-16 checksum.

        The optional 'split' argument introduces hyphens for increased
        readability.
        """
        x = self._append_fletcher()
        r = base64.b32encode(x)
        r = r.decode('ascii').rstrip('=')

        # insert some hyphens for clarity
        if split is None:
            split = 4
        if split == 0:
            split = len(r)
        r = '-'.join((r[i:i+split] for i in range(0, len(r), split)))

        return str('fp::' + r)

def empty_file_fp():
    """Return the fingerprint of the empty file."""
    class E(fingerprintable):
        def visit(self, fp):
            fp.enter_file(0)
            fp.leave_file()
    return fingerprint(E())

def empty_dict_fp():
    """Return the fingerprint of the empty dictionary."""
    class E(fingerprintable):
        def visit(self, fp):
            fp.enter_dict()
            fp.leave_dict()
    return fingerprint(E())

def zero_fp():
    """Return a fingerprint with all bits set to zero."""
    b = b'\0'*32
    if isinstance(b, str): # python 2 compat
        b = bytearray(b)
    return fingerprint(b)

def ones_fp():
    """Return a fingerprint with all bits set to one."""
    b = b'\xff'*32
    if isinstance(b, str): # python 2 compat
        b = bytearray(b)
    return fingerprint(b)

def _check_ck(f):
    assert isinstance(f, bytearray) or isinstance(f, bytes)
    fp = f[:-2]
    a, b = fletcher(fp)
    x, y = f[-2], f[-1]
    if (a, b) != (x, y):
        return (None, "invalid checksum (fp says %d %d, computed %d %d)" % (a, b, x, y))
    return (fingerprint(fp), None)

def _from_compact(s):
    assert isinstance(s, str)
    if not s.startswith('fp:'):
        return (None, "invalid prefix (expected 'fp:', got '%s')" % s[:3])
    s = s[3:]
    if len(s) != 46:
        return (None, "invalid length (expected 46, got %d)" % len(s))
    s = bytearray(s + '==', 'ascii')
    f = base64.urlsafe_b64decode(s)
    if isinstance(f, str): # python 2 compat
        f = bytearray(f)
    return _check_ck(f)

def _from_long(s):
    assert isinstance(s, str)
    s = s.upper()
    if not s.startswith('FP::'):
        return (None, "invalid prefix (expected 'fp::', got '%s')" % s[:4])
    s = s[4:].replace('-', '')
    if len(s) != 55:
        return (None, "invalid length (expected 55, got %d)" % len(s))
    s = bytearray(s + '=', 'ascii')
    f = base64.b32decode(bytes(s))
    if isinstance(f, str): # python 2 compat
        f = bytearray(f)
    return _check_ck(f)

def _from_hex(s):

    s = s.replace('-', '')
    if len(s) != 64:
        return (None, "invalid length (expected 64, got %d)" % len(s))

    s = bytearray(s, 'ascii')

    f = codecs.decode(s, 'hex_codec')
    if isinstance(f, str): # python 2 compat
        f = bytearray(f)

    return (fingerprint(f), None)

_rlong = re.compile(r'^[fF][pP]::[a-zA-Z2-7-]*$')
_rcompact = re.compile(r'^fp:[a-zA-Z0-9_-]*$')
_rhex = re.compile(r'^[0-9a-fA-F-]*$')

def parse(s):
    """Parse a string representation of a fingerprint.

    Returns a 3-tuple containing:
    - the fingerprint, or None if an error was encountered,
    - the representation type that was recognized (long, compact or hex)
    - an error message or None if no error was encountered.
    """
    if re.match(_rlong, s) is not None:
        fmt = "long"
        fp, errmsg = _from_long(s)

    elif re.match(_rcompact, s) is not None:
        fmt = "compact"
        fp, errmsg = _from_compact(s)

    elif re.match(_rhex, s) is not None:
        fmt = "hex"
        fp, errmsg = _from_hex(s)

    else:
        fp = None
        fmt = None
        errmsg = "unknown fingerprint format"

    return (fp, fmt, errmsg)

if __name__ == "__main__":
    print("testing...")
    l = [empty_file_fp(), empty_dict_fp(), zero_fp(), ones_fp()]

    rl = [
        'fp:s5pIIHf32iiVNH_eBGBMXtlXhMa7dI3w9KBrvHZ-v1NRAA',
        'fp::WONE-QIDX-67NC-RFJU-P7PA-IYCM-L3MV-PBGG-XN2I-34HU-UBV3-Y5T6-X5JV-CAA',
        'fp::WONEQIDX67NCRFJUP7PAIYCML3MVPBGGXN2I34HUUBV3Y5T6X5JVCAA',
        'fp::woneqidx67ncrfjup7paiycml3mvpbggxn2i34huubv3y5t6x5jvcaa',
        'b39a4820-77f7da28-95347fde-04604c5e-d95784c6-bb748df0-f4a06bbc-767ebf53',
        'fp:FvYPWVbnhezNY5vdtqyyef0wpvj149A7SquozxdVe3jigg',
        'B39A4820-77F7DA28-95347FDE-04604C5E-D95784C6-BB748DF0-F4A06BBC-767EBF53',
        81236592145469940157203126607178760648047830708351681206000552870365001334611
    ]

    for r in rl:
        if isinstance(r, str):
            fp, fmt, errmsg = parse(r)
            assert fp is not None
            l.append(fp)

        fp = fingerprint(r)
        l.append(fp)

    for f in l:
        print(f)
        s = f.compact()
        assert isinstance(s, str) and len(s) == 49 and s[:3].lower() == 'fp:'

        s = f.hex()
        assert isinstance(s, str) and len(s.replace('-','')) == 64

        s = f.long();
        assert isinstance(s, str) and len(s.replace('-','')) == 59

        s = f.binary()
        assert isinstance(s, bytearray) and len(s) == 32

        s = int(f)
        assert s >= 0 and s < (2**256)

        b1 = (f == f)
        b2 = (f != f)
        assert b1 or b2

    print("ok")
