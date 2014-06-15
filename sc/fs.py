"""Example code to convert Structured Commons objects to a filesystem and back."""
from __future__ import print_function

import sys
import os
import os.path
import fnmatch
import urllib
from sc import fp

try:
   # python 3
   import urllib.parse
   def quote(n):
      """Transform an object name to a filesystem name."""
      return urllib.parse.quote(n, safe='')
   def unquote(n):
      """Transform a filesystem name to an object name."""
      return urllib.parse.unquote(n)
except:
   # python 2
   def quote(n):
      """Transform an object name to a filesystem name."""
      return urllib.quote(n.encode('utf-8'), safe='')
   def unquote(n):
      """Transform a filesystem name to an object name."""
      return urllib.unquote(n).decode('utf-8')

class fs_wrap(fp.fingerprintable):
   """Wrapper for filesystem paths that enable fingerprinting."""

   def __init__(self, path, ignorelist = ['.*']):
      assert os.path.exists(path)
      self._path = path
      self._ignorelist = ignorelist

   def visit(self, v):
      """Visitor dispatch method.

      See help(fp.fingerprintable.visit) for details.
      """
      if os.path.isdir(self._path):
          v.enter_dict()
          for f in os.listdir(self._path):
             if any((fnmatch.fnmatch(f, p) for p in self._ignorelist)):
                continue
             fpath = os.path.join(self._path, f)
             name = unquote(f)
             if name[0] == '\0':
                # special: reference to fingerprint
                name = name[1:]
                t = 'l'
                with open(fpath, 'rb') as f:
                   bref = f.read()
                   if isinstance(bref, str):
                      bref = bytearray(bref) # python 2
                   obj = fp.fingerprint(bref)
             elif os.path.isdir(fpath):
                t = 't'
                obj = fs_wrap(fpath, self._ignorelist)
             else:
                t = 's'
                obj = fs_wrap(fpath, self._ignorelist)
             v.visit_entry(name, t, obj)
          v.leave_dict()

      else:
          v.enter_file(os.path.getsize(self._path))
          with open(self._path, 'rb') as f:
             while True:
                chunk = f.read(8192)
                if len(chunk) == 0: break
                v.visit_data(chunk)
          v.leave_file()

class encode_visitor(object):
   def __init__(self, path, verbose = False):
      assert not os.path.exists(path)
      self._path = path
      self._v = verbose

   def enter_file(self, sz):
      self._sz = sz
      self._cnt = 0
      self._f = open(self._path, 'wb')
      if self._v:
         print("file '%s', sz %d" % (self._path, sz), end='', file=sys.stderr)

   def visit_data(self, b):
      self._cnt += len(b)
      self._f.write(b)
      if self._v:
         print(".", end='', file=sys.stderr)

   def leave_file(self):
      assert self._sz == self._cnt
      self._f.close()
      if self._v:
         print('', file=sys.stderr)

   def enter_dict(self):
      os.mkdir(self._path)
      self._names = set()
      if self._v:
         print("dir '%s':" % self._path, file=sys.stderr)

   def visit_entry(self, name, t, obj):

      fp.validate_name(name)
      assert name not in self._names, "duplicate name %r" % name
      self._names.add(name)

      if t == 'l' and isinstance(obj, fp.fingerprint):
         fpath = os.path.join(self._path, quote('\0' + name))
         if self._v:
            print("reference '%s'" % fpath, file=sys.stderr)
         with open(fpath, 'wb') as f:
            f.write(obj.binary())

      elif isinstance(obj, fp.fingerprintable):
         fsname = quote(name)
         if fsname.startswith('.'):
            # avoid "bad" entries "." amd ".." and hidden filenames
            fsname = b'%2E' + fsname[1:]
         fpath = os.path.join(self._path, fsname)
         obj.visit(encode_visitor(fpath, self._v))

      else:
         raise TypeError("invalid object type")

   def leave_dict(self):
      del self._names
      if self._v:
         print("end dir '%s'" % self._path, file=sys.stderr)
