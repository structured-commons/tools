#! /usr/bin/env python

from __future__ import print_function

from sc import fp, fs, py, js

import pickle
import sys
import getopt
import os
import os.path
import ast

def force_bytes(data):
    if isinstance(data, str) or isinstance(data, type(u'')):
        data = bytearray((ord(c) for c in data))
    return data

def usage():
    print("usage: %s [OPTIONS] [SOURCE] [DESTINATION]" % sys.argv[0])
    print("Options:\n"
          "  -a        include filenames starting with .\n"
          "  -i PAT    ignore filenames matching PAT\n"
          "  -h        display this help and exit\n"
          "  -b        use Base64 for files when printing JSON\n"
          "  -v        run verbosely\n")
    print("Valid forms for SOURCE:\n"
          "  fs:PATH      Filesystem\n"
          "  json:PATH    JSON data\n"
          "  raw:PATH     Raw bytes (simple object)\n"
          "  utf8:PATH    UTF-8 encoded bytes (simple object)\n"
          "  str:STRING   Immediate UTF-8 encoded string (simple object)\n"
          "  pickle:PATH  Python pickled object\n"
          "\n"
          "Valid forms for DESTINATION:\n"
          "  fp:FORMAT    Compute and print the fingerprint\n"
          "  fs:PATH      Filesystem\n"
          "  json:PATH    JSON data\n"
          "  raw:PATH     Raw bytes (only simple object)\n"
          "  utf8:PATH    UTF-8 encoded bytes (only simple object)\n"
          "  pickle:PATH  Python pickled object\n"
          "\n"
          "If PATH is a single hyphen '-', data is read from (resp. written to)\n"
          "the standard input (resp. output).\n")
    print("Examples:\n"
          "\t%s fs:. fp:compact\n"
          "\t%s -b fs:. json:-" % (sys.argv[0], sys.argv[0]))

opts, args = getopt.getopt(sys.argv[1:], "bvahi:", ['help'])
dopts = dict(opts)

if '-h' in dopts or '--help' in dopts:
    usage()
    sys.exit(0)

ignorelist = []
if '-a' not in dopts:
    ignorelist.append('.*')
for a, v in opts:
    if a == '-i':
        ignorelist.append(v)
verbose = ('-v' in dopts)
b64json = ('-b' in dopts)

src = 'raw:-'
dst = 'fp:compact'

if len(args) > 0:
    src = args[0]
if len(args) > 1:
    dst = args[1]

src_method, src_name = src.split(':',1)
dst_method, dst_name = dst.split(':',1)
if src_method in ['raw', 'json', 'py', 'pickle', 'utf8']:
    if src_name == '-':
        src_file = open('/dev/stdin', src_method == 'json' and 'r' or 'rb')
    else:
        src_file = open(src_name, src_method == 'json' and 'r' or 'rb')

if dst_method in ['raw', 'json', 'py', 'pickle', 'utf8']:
    if dst_name == '-':
        dst_file = open('/dev/stdout', dst_method in ['json', 'py'] and 'w' or 'wb')
    else:
        dst_file = open(dst_name, dst_method in ['json', 'py'] and 'w' or 'wb')

if src_method == 'fs':
    assert os.path.exists(src_name)
    src_obj = fs.fs_wrap(src_name, ignorelist)

elif src_method in ['raw', 'utf8', 'str', 'pickle']:

    if src_method == 'raw':
        # raw bytes, unencoded
        data = force_bytes(src_file.read())

    elif src_method == 'utf8':
        # utf-8 encoded data
        data = force_bytes(src_file.read())
        data = data.decode('utf-8')
        data = bytearray((ord(c) for c in data))

    elif src_method == 'str':
        # utf-8 encoded data in name
        data = bytearray(src_name, 'utf-8')

    elif src_method == 'pickle':
        data = pickle.load(src_file)

    src_obj = py.decode(data)

elif src_method == 'json':
    src_obj = js.decode(src_file)

else:
    print("unknown input method '%s'" % src_method, file=sys.stderr)
    sys.exit(1)


if dst_method == 'fs':
    v = fs.encode_visitor(dst_name, verbose)
    src_obj.visit(v)

elif dst_method in ['py', 'raw', 'utf8', 'pickle']:
    src_py = py.encode(src_obj)

    if dst_method == 'py':
        dst_file.write(repr(src_py))

    elif dst_method == 'raw':
        assert isinstance(src_py, bytearray)
        dst_file.write(src_py)

    elif dst_method == 'utf8':
        assert isinstance(src_py, bytearray)
        try:
            x = unichr(0)
        except:
            unichr = chr
        src_str = u''.join((unichr(x) for x in src_py))
        src_data = force_bytes(src_str.encode('utf-8'))
        dst_file.write(src_data)

    elif dst_method == 'pickle':
        pickle.dump(src_py, dst_file)

elif dst_method == 'json':
    js.encode(src_obj, dst_file, use_base64=b64json)

elif dst_method == 'fp':
    v = fp.compute_visitor(verbose)
    src_obj.visit(v)
    fp = v.fingerprint()
    if dst_name == 'compact':
        print(fp.compact())
    elif dst_name == 'hex':
        print(fp.hex())
    elif dst_name == 'long':
        print(fp.long())
    elif dst_name == 'binary':
        print(fp.binary())
    elif dst_name == 'dec':
        print(int(fp))
    else:
        print("unknown fingerprinting method '%s'" % dst_name, file=sys.stderr)
        sys.exit(1)

else:
    print("unknown output method '%s'" % dst_method, file=sys.stderr)
    sys.exit(1)
