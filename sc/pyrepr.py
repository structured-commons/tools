"""Example code to convert Structured Commons objects to Python objects."""

from __future__ import print_function

import sys
from sc import fp

class pyrepr_visitor(object):
   """Convert an abstract object tree to a Python concrete object.

   - object files are transformed to unicode strings (UTF-8 encoded)
   - object dictionaries are transformed to Python dictionaries
   - fingerprint references in dictionaries are transformed to integers
     with the fingerprint's value.

   This visitor is suitable to process an object that implements
   the ``fingerprintable`` interface.

   pyrepr_visitor :: Fingerprintable a => a -> PyObject
   """

   def enter_file(self, sz):
      self._sz = sz
      self._cnt = 0
      self._value = u''

   def visit_data(self, b):
      self._cnt += len(b)
      self._value += b.decode('utf-8')

   def leave_file(self):
      assert self._sz == self._cnt

   def enter_dict(self):
      self._value = {}

   def visit_entry(self, name, t, obj):
      if t == 'l' and isinstance(obj, fp.fingerprint):
         self._value[name] = int(obj)
      elif isinstance(obj, fp.fingerprintable):
         v = pyrepr_visitor()
         obj.visit(v)
         self._value[name] = v._value
      else:
         raise TypeError("invalid object type")

   def leave_dict(self):
      pass

   def value(self):
      """Returns the Python object computed by this visitor."""
      return self._value

class pyrepr_wrap(fp.fingerprintable):
   """Wrap a Python concrete dictionary tree in the fingerprintable interface.

   This wrapper can then be provided to compute fingerprints,
   (fp.compute_visitor), save to filesystem (fs.encode_visitor), etc.
   """

   def __init__(self, obj):
      self._obj = obj

   def visit(self, v):
      if isinstance(self._obj, dict):
         v.enter_dict()
         for k, val in self._obj.items():
            if isinstance(val, str) or isinstance(val, type(u'')):
                v.visit_entry(k, 's', pyrepr_wrap(val))
            elif isinstance(val, dict):
                v.visit_entry(k, 't', pyrepr_wrap(val))
            else:
                v.visit_entry(k, 'l', fp.fingerprint(val))
         v.leave_dict()
      else:
         buf = self._obj
         if not isinstance(buf, bytearray):
            buf = bytearray(self._obj, 'utf-8')
         v.enter_file(len(buf))
         v.visit_data(buf)
         v.leave_file()

def encode(obj):
    """Return a fingerprintable interface to the object given as argument."""
    return pyrepr_wrap(obj)

def decode(obj):
    """Decode a fingerprintable object to a Python object tree."""
    assert isinstance(obj, fp.fingerprintable)
    v = pyrepr_visitor()
    obj.visit(v)
    return v.value()
