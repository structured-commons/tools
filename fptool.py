#! /usr/bin/env python

from __future__ import print_function
from sc.fp import *

import sys
import getopt

def usage():
    print("usage: %s [OPTION]... FINGERPRINT..." % sys.argv[0])
    print("Operation modes:\n"
          "  -a                   display all representations\n"
          "  -c                   compare the fingerprints\n"
          "  -f FORMAT            display a specific representation\n"
          "  -h, --help           display this help and exit\n"
          "  -s N                 split with hyphens every N characters\n"
          "\n"
          "Formats:\n"
          "  compact              Base64-encoded with checksum\n"
          "  long                 Base32-encoded with checksum\n"
          "  binary               raw bytes\n"
          "  hex                  hexadecimal bytes without checksum\n"
          "  carray               C char array definition\n"
          "  dec                  decimal (big endian)\n"
          )
    print("Examples:\n"
          "\t%s -a %s\n"
          "\t%s -f hex %s\n"
          "\t%s -f long -s 2 %s\n"
          "\t%s -f binary %s\n"
          "\t%s -f compact %s\n"
          "\t%s -c %s %s" %
          (sys.argv[0], empty_file_fp().compact(),
           sys.argv[0], empty_dict_fp().long(split=0),
           sys.argv[0], zero_fp().long(),
           sys.argv[0], ones_fp().hex(split=0),
           sys.argv[0], empty_file_fp().hex(),
           sys.argv[0], empty_file_fp().compact(), empty_dict_fp().compact()
       ))

opts, args = getopt.getopt(sys.argv[1:], "acf:hs:", ['help'])
opts = dict(opts)

if len(args) == 0 or '-h' in opts or '--help' in opts:
    usage()
    sys.exit(0)
else:
    # collect all fingerprints:
    fps = []
    has_error = False
    for s in args:
        fp, fmt, errmsg = parse(s)
        if fp is None:
            print("error: %s: unable to recognize '%s'"% (sys.argv[0], s), file=sys.stderr)
            print("error: %s: %s" % (sys.argv[0], errmsg), file=sys.stderr)
            has_error = True
        fps.append( (fp, fmt, s) )

    if has_error:
        sys.exit(1)

    if '-c' in opts:
        # mode: compare
        first = fps[0][0].binary()
        d = []
        for i, (fp, _, _) in enumerate(fps[1:]):
            if first != fp.binary():
               d.append(i+1)

        if len(d) > 0:
            print("fingerprints at positions %s differ from the first" %
                  ', '.join(('%d' % x for x in d)), file=sys.stderr)
            sys.exit(1)
        else:
            sys.exit(0)

    # general mode: re-print all input fingerprints.
    split = None
    if '-s' in opts:
        split = int(opts['-s'])

    for fp, fmt, s in fps:
        if '-a' in opts:
            print("Argument: '%s' (%s)\n"
                  "  compact: %s\n"
                  "  long:    %s\n"
                  "  hex:     %s\n"
                  "  dec:     %d\n"
                  "  carray:  %s" %
                  ( s, fmt,
                    fp.compact(),
                    fp.long(split),
                    fp.hex(split),
                    int(fp),
                    fp.carray()) )
        else:
            if '-f' in opts:
                fmt = opts['-f']

            if fmt == 'binary':
                if hasattr(sys.stdout, 'buffer'):
                   sys.stdout.buffer.write(fp.binary())
                else:
                   sys.stdout.write(fp.binary())
            elif fmt == 'hex':
                print(fp.hex(split))
            elif fmt == 'long':
                print(fp.long(split))
            elif fmt == 'compact':
                print(fp.compact())

    sys.stdout.flush()
    sys.exit(0)
