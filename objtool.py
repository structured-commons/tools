#! /usr/bin/env python

from __future__ import print_function

from sc import fp, fs, pyrepr

import json
import sys
import getopt
import os
import os.path
import ast

def usage():
    print("usage: %s [OPTIONS] [FMT:SOURCE] [FMT:SINK]" % sys.argv[0])
    print("Options:\n"
          "  -a        include filenames starting with .\n"
          "  -i PAT    ignore filenames matching PAT\n"
          "  -h        display this help and exit\n"
          "  -v        run verbosely\n")
    print("Examples:\n"
          "\t%s fs:. fp:compact" % sys.argv[0])

opts, args = getopt.getopt(sys.argv[1:], "vahi:", ['help'])
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

src = 'raw:-'
dst = 'fp:compact'

if len(args) > 0:
    src = args[0]
if len(args) > 1:
    dst = args[1]

src_method, src_name = src.split(':',1)
dst_method, dst_name = dst.split(':',1)
if src_method in ['raw', 'json', 'py']:
    if src_name == '-':
        src_file = open('/dev/stdin', 'rb')
    else:
        src_file = open(src_name, 'rb')
if dst_method in ['raw', 'json', 'py']:
    if dst_name == '-':
        dst_file = open('/dev/stdout', 'wb')
    else:
        dst_file = open(dst_name, 'wb')

if src_method == 'fs':
    assert os.path.exists(src_name)
    src_obj = fs.fs_wrap(src_name, ignorelist)

elif src_method in ['raw', 'str']:
    if src_method == 'raw':
        data = src_file.read()
        if src_name == '-' and isinstance(data, str):
            data = bytearray(data, 'utf-8')
        elif isinstance(data, str):
            data = bytearray(data) # python 2
    else:
        data = bytearray(src_name, 'utf-8')

    class raw_wrap(fp.fingerprintable):
        def visit(self, v):
            v.enter_file(len(data))
            v.visit_data(data)
            v.leave_file()

    src_obj = raw_wrap()

elif src_method == 'json':
    data = src_file.read()
    data = data.decode('utf-8')
    data = json.loads(data)
    src_obj = pyrepr.pyrepr_wrap(data)

elif src_method == 'py':
    data = src_file.read()
    data = data.decode('utf-8')
    data = ast.literal_eval(data)
    src_obj = pyrepr.pyrepr_wrap(data)

else:
    print("unknown input method '%s'" % src_method, file=sys.stderr)
    sys.exit(1)

if dst_method in ['py', 'raw', 'json']:
    v = pyrepr.pyrepr_visitor()
    src_obj.visit(v)
    src_obj = v.value()

if dst_method == 'fs':
    v = fs.encode_visitor(dst_name, verbose)
    src_obj.visit(v)

elif dst_method == 'py':
    s = repr(src_obj) + '\n'
    dst_file.write(s.encode('utf-8'))

elif dst_method == 'json':
    s = json.dumps(src_obj) + '\n'
    dst_file.write(s.encode('utf-8'))

elif dst_method == 'raw':
    assert isinstance(src_obj, str) or isinstance(src_obj, type(u''))
    s = src_obj.encode('utf-8')
    dst_file.write(s)

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
