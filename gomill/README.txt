Gomill
======

Gomill is a suite of tools, and a Python library, for use in developing and
testing Go-playing programs.

Updated versions of Gomill will be made available at
http://mjw.woodcraft.me.uk/gomill/

The documentation is distributed separately in HTML form. It can be downloaded
from the above web site, or viewed online at
http://mjw.woodcraft.me.uk/gomill/doc/

A Git repository containing Gomill releases (but not detailed history) is
available:
  git clone http://mjw.woodcraft.me.uk/gomill/git/
It has a web interface at http://mjw.woodcraft.me.uk/gitweb/gomill/


Contents
--------

The contents of the distribution directory (the directory containing this
README file) include:

  ringmaster    -- Executable wrapper for the ringmaster program
  gomill        -- Python source for the gomill package
  gomill_tests  -- Test suite  for the gomill package
  docs          -- ReST sources for the HTML documentation
  examples      -- Example scripts using the gomill library
  setup.py      -- Installation script


Requirements
------------

Gomill requires Python 2.5, 2.6, or 2.7.

For Python 2.5 only, the --parallel feature requires the external
`multiprocessing` package [1].

Gomill is intended to run on any modern Unix-like system.

[1] http://pypi.python.org/pypi/multiprocessing


Running the ringmaster
----------------------

The ringmaster executable in the distribution directory can be run directly
without any further installation; it will use the copy of the gomill package
in the distribution directory.

A symbolic link to the ringmaster executable will also work, but if you move
the executable elsewhere it will not be able to find the gomill package unless
the package is installed.


Installation
------------

Installing Gomill puts the gomill package onto the Python module search path,
and the ringmaster executable onto the executable PATH.

To install, first change to the distribution directory, then:

 - to install for the system as a whole, run (as a sufficiently privileged user)

     python setup.py install


 - to install for the current user only (Python 2.6 or 2.7), run

     python setup.py install --user

   (in this case the ringmaster executable will be placed in ~/.local/bin.)

Pass --dry-run to see what these will do.
See http://docs.python.org/2.7/install/ for more information.


Uninstallation
--------------

To remove an installed version of Gomill, run

  python setup.py uninstall

(This uses the Python module search path and the executable PATH to find the
files to remove; pass --dry-run to see what it will do.)


Running the test suite
----------------------

To run the testsuite against the distributed gomill package, change to the
distribution directory and run

  python -m gomill_tests.run_gomill_testsuite


To run the testsuite against an installed gomill package, change to the
distribution directory and run

  python test_installed_gomill.py


With Python versions earlier than 2.7, the unittest2 library [1] is required
to run the testsuite.

[1] http://pypi.python.org/pypi/unittest2/


Running the example scripts
---------------------------

To run the example scripts, it is simplest to install the gomill package
first.

If you do not wish to do so, you can run

  export PYTHONPATH=<path to the distribution directory>

so that the example scripts will be able to find the gomill package.


Building the HTML documentation
-------------------------------

To build the HTML documentation, change to the distribution directory and run

   python setup.py build_sphinx

The documentation will be generated in build/sphinx/html.

Requirements:

   Sphinx [1] version 1.0 or later
              (at least 1.0.4 recommended; tested with 1.0 and 1.1)
   LaTeX  [2]
   dvipng [3]

[1] http://sphinx.pocoo.org/
[2] http://www.latex-project.org/
[3] http://www.nongnu.org/dvipng/


Licence
-------

Gomill is copyright 2009-2012 Matthew Woodcraft

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


Contact
-------

Please send any bug reports, suggestions, patches, questions &c to

Matthew Woodcraft
matthew@woodcraft.me.uk

I'm particularly interested in hearing about any GTP engines (even buggy ones)
which don't work with the ringmaster.


Changelog
---------

See the 'Changes' page in the HTML documentation (docs/changes.rst).

                                                                mjw 2012-08-26
