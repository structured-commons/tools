"""Example code to convert Structured Commons objects to Python objects."""

from __future__ import print_function

import sys
from sc import fp

class pyrepr_visitor(object):
   """Convert an abstract object tree to a Python concrete object.

   - object files are transformed to bytearray
   - object dictionaries are transformed to Python dictionaries, with
     names transformed to unicode strings
   - fingerprint references in dictionaries are transformed to
     fingerprint objects.

   This visitor is suitable to process an object that implements
   the ``fingerprintable`` interface.

   pyrepr_visitor :: Fingerprintable a => a -> PyObject

   """

   def enter_file(self, sz):
      self._sz = sz
      self._cnt = 0
      self._value = bytearray()

   def visit_data(self, b):
      assert isinstance(b, bytearray) or isinstance(b, bytes)
      self._cnt += len(b)
      self._value += b

   def leave_file(self):
      assert self._sz == self._cnt

   def enter_dict(self):
      self._value = {}

   def visit_entry(self, name, t, obj):

      fp.validate_name(name)
      assert name not in self._value, "duplicate name %r" % name

      if t == 'l' and isinstance(obj, fp.fingerprint):
         self._value[name] = obj

      elif isinstance(obj, fp.fingerprintable):
         v = pyrepr_visitor()
         obj.visit(v)
         self._value[name] = v.value()

      else:
         raise TypeError("invalid object type: %r" % obj)

   def leave_dict(self):
      pass

   def value(self):
      """Returns the Python object computed by this visitor."""
      return self._value

class pyrepr_wrap(fp.fingerprintable):
   """Wrap a Python concrete dictionary tree in the fingerprintable
interface.

   This wrapper can then be provided to compute fingerprints,
   (fp.compute_visitor), save to filesystem (fs.encode_visitor), etc.

   """

   def __init__(self, obj):
      self._obj = obj

   def visit(self, v):
      if isinstance(self._obj, dict):
         v.enter_dict()
         for k, val in self._obj.items():
            if isinstance(val, str) or isinstance(val, type(u'')) \
             or isinstance(val, bytes) or isinstance(val, bytearray):
                v.visit_entry(k, 's', pyrepr_wrap(val))
            elif isinstance(val, dict):
                v.visit_entry(k, 't', pyrepr_wrap(val))
            elif isinstance(val, fp.fingerprint):
               v.visit_entry(k, 'l', val)
            else:
               raise TypeError("invalid object type: %r" % val)
         v.leave_dict()
      else:
         buf = self._obj
         if not (isinstance(buf, bytearray) or isinstance(buf, bytes)):
            buf = buf.encode('utf-8')
         v.enter_file(len(buf))
         v.visit_data(buf)
         v.leave_file()

def decode(obj):
    """Return a fingerprintable interface to the object given as argument."""
    return pyrepr_wrap(obj)

def encode(obj):
    """Encode a fingerprintable object to a Python object tree."""
    assert isinstance(obj, fp.fingerprintable)
    v = pyrepr_visitor()
    obj.visit(v)
    return v.value()
