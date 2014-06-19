"""Example code to convert Structured Commons objects to JSON."""

from __future__ import print_function

import sys
import json
import base64
from sc import fp

try:
   unichr(0)
except:
   unichr = chr

class pyjson_visitor(object):
   """Convert an abstract object tree to a JSON-serializable Python concrete object.

   - object files are transformed to either unicode strings or an array
     containing one string containing the base64-encoded data.
   - object dictionaries are transformed to Python dictionaries, with
     names transformed to unicode strings
   - fingerprint references in dictionaries are transformed to
     an arrays containing one string containing the fingerprint compact representation.

   This visitor is suitable to process an object that implements
   the ``fingerprintable`` interface.

   pyrepr_visitor :: Fingerprintable a => a -> PyObject

   """
   def __init__(self, use_base64):
      self._b64 = use_base64

   def enter_file(self, sz):
      self._sz = sz
      self._cnt = 0
      if self._b64:
         self._value = bytearray()
      else:
         self._value = u''

   def visit_data(self, b):
      assert isinstance(b, bytearray) or isinstance(b, bytes)
      self._cnt += len(b)
      if self._b64:
         self._value += b
      else:
         for c in b:
            self._value += unichr(c)

   def leave_file(self):
      assert self._sz == self._cnt
      assert len(self._value) == self._sz
      if self._b64:
         self._value = [base64.urlsafe_b64encode(self._value).decode('ascii')]

   def enter_dict(self):
      self._value = {}

   def visit_entry(self, name, t, obj):

      fp.validate_name(name)
      assert name not in self._value, "duplicate name %r" % name

      if t == 'l' and isinstance(obj, fp.fingerprint):
         self._value[name] = [obj.compact()]

      elif isinstance(obj, fp.fingerprintable):
         v = pyjson_visitor(self._b64)
         obj.visit(v)
         self._value[name] = v.value()

      else:
         raise TypeError("invalid object type: %r" % obj)

   def leave_dict(self):
      pass

   def value(self):
      """Returns the Python object computed by this visitor."""
      return self._value

class pyjson_wrap(fp.fingerprintable):
   """Wrap a JSON-serializable Python concrete dictionary tree in the fingerprintable
interface.

   This wrapper can then be provided to compute fingerprints,
   (fp.compute_visitor), save to filesystem (fs.encode_visitor), etc.
   """

   def __init__(self, obj):
      if isinstance(obj, str) or isinstance(obj, type(u'')):
         obj = bytearray((ord(c) for c in obj))
      elif isinstance(obj, list) and len(obj) == 1:
         obj = base64.urlsafe_b64decode(str(obj[0]))
      self._obj = obj

   def visit(self, v):
      if isinstance(self._obj, dict):
         v.enter_dict()
         for k, val in self._obj.items():
            if isinstance(val, str) or isinstance(val, type(u'')):
                v.visit_entry(k, 's', pyjson_wrap(val))

            elif isinstance(val, dict):
                v.visit_entry(k, 't', pyjson_wrap(val))

            elif isinstance(val, list) and len(val) == 1:
               if val[0][:3].lower() == 'fp:':
                  v.visit_entry(k, 'l', fp.fingerprint(val[0]))
               else:
                  v.visit_entry(k, 's', pyjson_wrap(val))

            else:
               raise TypeError("invalid object type: %r" % val)
         v.leave_dict()
      else:
         v.enter_file(len(self._obj))
         v.visit_data(self._obj)
         v.leave_file()

def decode(json_src):
    """Return a fingerprintable interface to the JSON object given as argument."""
    obj = json.load(json_src)
    return pyjson_wrap(obj)

def encode(obj, json_dst, use_base64 = False):
    """Encode a fingerprintable object to a JSON object."""
    assert isinstance(obj, fp.fingerprintable)
    v = pyjson_visitor(use_base64)
    obj.visit(v)
    json.dump(v.value(), json_dst)
