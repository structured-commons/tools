Example Structured Commons utilities
====================================

This repository provides an example implementation of the `Structured
Commons`__ [#]_ [#]_ [#]_, an alternative publication and dissemination
model for scientific works.

This directory contains a **Python library** ``sc`` for manipulating
Structured Commons objects and fingerprints; and two front-end
**command-line utilities**:

**objtool.py**
   Convert between object representations and compute object fingerprints.

**fptool.py**
   Convert between fingerprint representations and compare fingerprints.

Installation
------------

Requirements: Python 2 or 3 (the code was tested with Python 2.7 and 3.3)

The utilities can be run directly from the source directory without
"installing" them elsewhere.

For a separate installation::

     python setup.py build
     python setup.py install

This installs to the default ``site-packages`` directory for that
version of the Python interpreter. To change the target directory, add
the argument ``--prefix=DIR`` after ``install``.

Usage: objtool.py
-----------------

Examples
````````

To compute the fingerprint of the single file named "``1404.7753v2.pdf``"::

     $ python objtool.py fs:1404.7753v2.pdf
     fp:FvYPWVbnhezNY5vdtqyyef0wpvj149A7SquozxdVe3jigg

To compute the "long" fingerprint of an entire Python source tree
starting at directory "``sc``", excluding compiled bytecode objects,
with verbose reporting::

     $ python objtool.py -i '*.pyc' -i __pycache__ -v fs:sc fp:long
     dictionary, entering:
     entry u'__init__.py': file, sz 33 (fp:nquSc-41kbl6K2QfhiYQxJZFgKO4YPpeS6iz3SmlY1Dkhw)
     entry u'fp.py': file, sz 13731 (fp:Uxs7Oczd4boiEoqCdFDgCKnBXDo3K4h2rY5wu9LnDLdjSw)
     entry u'fs.py': file, sz 3857 (fp:uIuqi_hOvEhd9in2LPcNrVXubrRcv13dR52FteK9fJSqqA)
     entry u'pyrepr.py': file, sz 2593 (fp:xivrx77SyVJyWvVTwm2wialKuRprZB47uuRSgn6WGoPrxg)
     leaving dictionary (fp:C49RMXE36qDzdc9r61JiwfCl9_KCOdVlrgQ-sy9DiKkaAw)
     fp::BOHV-CMLR-G7VK-B43V-Z5V6-WUTC-YHYK-L57S-QI45-KZNO-AQ7L-GL2D-RCUR-UAY

To convert an object from its filesystem representation to a representation
as Python dictionary tree::

     $ python objtool.py -i '*.pyc' -i __pycache__ -v fs:sc py:-
     {u'fs.py': u'#! /usr/ .... '}


Command-line syntax
```````````````````

The general syntax for ``objtool.py`` is the following::

     objtool.py [OPTIONS] [SOURCE] [DESTINATION]

Where ``SOURCE`` is any of the following:

``fs:PATH``
   Filesystem representation starting from ``PATH``.

``raw:FILE`` or ``raw:-``
   Read a single file object as byte stream from ``FILE`` or stdin.

``utf8:FILE`` or ``utf8:-``
   Read a single file object as an UTF-8 encoded byte stream from ``FILE`` or stdin.

``pickle:FILE`` or ``pickle:-``
   Read a pickled Python object from ``FILE`` or stdin.

``json:FILE`` or ``json:-``
   JSON syntax read as associative arrays / strings / numbers from ``FILE`` or stdin.

and ``DESTINATION`` is any of the following:

``fp:FORMAT``
   Compute and print the input object's fingerprint using ``FORMAT``. See
   the description of ``fptool.py`` below for possible formats.

``fs:PATH``
   Write the filesystem representation starting from ``PATH`` (which must not exist yet).

``json:FILE`` or ``json:-``
   Emit the JSON syntax as associative arrays / strings to ``FILE`` or stdout.

``raw:FILE`` or ``raw:-``
   Write a single file object as byte stream to ``FILE`` or stdout.

``utf8:FILE`` or ``utf8:-``
   Write a single file object as UTF-8 encoded byte stream to ``FILE`` or stdout.

``py:FILE`` or ``py:-``
   Write an quivalent Python syntax  to  ``FILE`` or stdout.


The defaults for ``SOURCE`` and ``DESTINATION`` are ``raw:-`` and ``fp:compact``, respectively.

Command-line options:

``-h``
   Print a command-line help and exit.

``-v``
   Explore recursive structures verbosely.

``-i PAT``
   Ignore filesystem names matching the pattern ``PAT`` (fnmatch syntax).

``-a``
   Also include filesystem names starting with a dot (by default, they are ignored).

``-b``
   Use Base64 encoding when outputting JSON.

Usage: fptool.py
----------------

Examples
````````

To convert a fingerprint to long format (eg. for easier communication over the phone)::

     $ python fptool.py -f long fp:FvYPWVbnhezNY5vdtqyyef0wpvj149A7SquozxdVe3jigg
     fp::C33A-6WKW-46C6-ZTLD-TPO3-NLFS-PH6T-BJXY-6XR5-AO2K-VOUM-6F2V-PN4O-FAQ

To show all possible representations of a fingerprint::

     $ python fptool.py -a fp:FvYPWVbnhezNY5vdtqyyef0wpvj149A7SquozxdVe3jigg
     Argument: 'fp:FvYPWVbnhezNY5vdtqyyef0wpvj149A7SquozxdVe3jigg' (compact)
       compact: fp:FvYPWVbnhezNY5vdtqyyef0wpvj149A7SquozxdVe3jigg
       long:    fp::C33A-6WKW-46C6-ZTLD-TPO3-NLFS-PH6T-BJXY-6XR5-AO2K-VOUM-6F2V-PN4O-FAQ
       hex:     16f60f59-56e785ec-cd639bdd-b6acb279-fd30a6f8-f5e3d03b-4aaba8cf-17557b78
       dec:     10385632981549898505027615664606801012501301866546186765965067533389527350136

Recognized options:

``-h``
   Print a help text and exit.

``-a``
   Print all representations of a fingerprint.

``-f FMT``
   Print a particular representation.

Recognized formats:

======= ================================= ========================================
Name    Format / Encoding                 Target use
======= ================================= ========================================
binary  32 bytes (256 bits), no encoding  Binary storage, network protocols
compact 46 characters, Base64 + checksum  Print and hypertext media
long    55 characters, Base32 + checksum  Mouth-to-ear, analog phone/radio
hex     64 characters, hexadecimal        Databases w/o proper support for binary
dec     1-78 decimal digits               Academic / teaching
carray  C char array definition           Academic / teaching
======= ================================= ========================================


References
----------

.. __: http://www.structured-commons.org/

.. [#] `Academia 2.0: removing the publisher middle-man while retaining
   impact`__. Poss, R.; Altmeyer, S.; Thompson, M.; and Jelier, R.  In
   Proc 1st ACM SIGPLAN Workshop on Reproducible Research
   Methodologies and New Publication Models in Computer Engineering
   (TRUST'14), Edinburgh, UK, June 2014. ACM

.. [#] http://arxiv.org/abs/1404.7753

.. [#] http://science.raphael.poss.name/aca2-draft-spec.html

.. __: http://www.bibbase.org/network/publication/poss-altmeyer-thompson-jelier-academia20removingthepublishermiddlemanwhileretainingimpact-2014
