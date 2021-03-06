
============
Alp software
============

The Alp is a new unit meant for measuring time. To understand and use
this unit, the program included in this distribution has been
created. It's both a command-line tool, named "alp", and a Python
module.


License
=======

Alp software is free software under the terms of the GNU General
Public License version 3 (or any later version). The author of Alp
software is Niels G. W. Serup, contactable at ngws@metanohi.name. This is
version 0.1.1 of the program.

The libraries used by Alp software are GPL-compatible.


Installing
==========

The Alp program and module is contained in a single file,
``alp.py``. It is not necessary to install it, but it can make it
easier to use the Alp software.

Run this in a terminal::

  # python setup.py install

Dependencies
============

Python 2.5+ is probably a requirement.

For formatting and control codes, Alp will attempt to use ncurses. If
that fails, Alp will try to use the Python termcolor module, available
at http://pypi.python.org/pypi/termcolor/, installable using ``$ sudo
easy_install termcolor`` (released under the GPLv3+).

If present, Alp will also use the ``setproctitle`` Python module,
available at http://pypi.python.org/pypi/setproctitle/, installable
using ``$ sudo easy_install setproctitle`` (released under the New BSD
License).


Using
=====

When using the Alp software as a command-line tool, simply run
``alp``. Run ``alp --help`` to see what options you can specify.

When using it as a module, just use ``import alp`` in your Python
program. To learn how the Alp module works, run ``pydoc alp`` or
``python -c 'import alp; help(alp)'``. There are also a couple of
tests in the ``tests`` directory.


This document
=============
Copyright (C) 2010  Niels G. W. Serup

Copying and distribution of this file, with or without modification,
are permitted in any medium without royalty provided the copyright
notice and this notice are preserved.  This file is offered as-is,
without any warranty.
