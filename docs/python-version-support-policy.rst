.. title: Python version support policy
.. slug: python-version-support-policy
.. date: 2024-01-13 10:00:00 UTC
.. author: The Nikola Team

Nikola is written in Python. New Python versions are released
`every year in October.`__ New Python versions bring new language and standard
library features, but they also often remove things the Python development team
considered old/deprecated/uncool, and some libraries with C dependencies often
cause issues (they fail to build or they lack binary wheels on PyPI) for
shortly after a new Python version. The Python team supports a release for 5
years after the initial release (3.x.0).

__ https://peps.python.org/pep-0602/

Nikola is used by both Python developers who are using the latest-and-greatest
Python release, and more casual Python users that use whatever release is
provided by their Unix-like operating system of choice. Some of them may be
using rolling-release or often-updated Linux distributions, like Arch Linux or
Fedora; others might be on Ubuntu LTS or Debian stable.

In order to support the largest group of users, while also keeping the list
of supported Python releases manageable, and minimizing the number of cases
where legacy or worse code must be used to support old versions, the following
Python version support policy is adopted.

Policy
======

1. Nikola *must* support all Python versions for which at least one of those criteria is true:

   a. It is `supported by the Python core team`__ (5 years since release).
   b. It is `included`__ in the oldest `Ubuntu LTS release`__  still within standard support (LTS releases are supported for 5 years since release).
   c. It is included in `Debian stable`__.
   d. It is included in `Debian oldstable`__, if the that Debian release became oldstable in the past 3 months.

2. Nikola *should* support all Python versions for which at least one of those criteria is true:

   a. It is `the newest Python release supported by PyPy`__.
   b. It is included in Debian oldstable, if that Debian release has been oldstable since more than 3 months.

3. If a Python version is covered only by the optional criteria, the Nikola maintainers may decide to drop support for it if it is not feasible to maintain.

4. Nikola should also support Python versions that are intermediate versions between the oldest supported version and the latest version.
   For example, if the latest Python version is 3.9, the oldest officially supported version is 3.7, the but the oldest Ubuntu LTS and Debian stable both have 3.4, then Python 3.5 and 3.6 should *also* be supported.

5. CI pipelines on Linux should be run for all supported Python versions. CI pipelines for Windows and macOS should be run for the latest Python version.

6. In the event Nikola does not support the newest Python release, the relevant issues should be resolved or reported upstream as soon as possible, in consideration of rolling-release distributions that package Nikola.

7. If all mandatory criteria stop applying to a Python version, it may be dropped after a grace period of 3 months. (This means that Debian oldstable is guaranteed support for a total of 6 months.)

8. If all optional criteria stop applying to a Python version, and all mandatory criteria were already inapplicable, it may be dropped after a grace period of 6 weeks.

9. Removing support for a Python version does not require any form of advance warning to Nikola users and may be done in a patch version.

10. Maintainers may choose to support a Python version, even if it does not fit any of the above criteria or rules, if there exist other significant groups of Python users that may benefit from support for that version, as long as that version would not add undue burden.

Support Matrix
==============

Criteria
--------

Data as of January 2024.

* Python Core Team: Python 3.7 supported until 2023-06, Python 3.8 supported until 2024-10, Python 3.9 supported until 2025-10, Python 3.10 supported until 2026-10
* Ubuntu LTS: Python 3.8 supported by Ubuntu 20.04 until 2025-05, Python 3.10 supported by Ubuntu 22.04 until 2027-05, Python 3.12 supported by Ubuntu 24.04 until 2029-05
* Debian stable: Python 3.11 in bookworm
* Debian oldstable: Python 3.9 in bullseye, became oldstable in 2023-06
* PyPy: latest supported version is 3.10

Applied to Python versions
--------------------------

* Python 3.7: no criteria apply since 2023-09, support dropped in 2024-01
* Python 3.8: expected to be supported until at least 2025-08 via Ubuntu 20.04 LTS
* Python 3.9: expected to be supported until at least 2026-01 via Python Core Team (+ possibly Debian oldstable)
* Python 3.10: expected to be supported until at least 2027-08 via Ubuntu 20.04 (+ possibly PyPy)
* Python 3.11: until at least 2028-01, might be extended by Debian stable (bookworm)
* Python 3.12: current release; supported until at least 2029-08 via Ubuntu 24.04 (noble)

__ https://devguide.python.org/versions/
__ https://packages.ubuntu.com/search?suite=all&exact=1&searchon=names&keywords=python3
__ https://wiki.ubuntu.com/Releases
__ https://packages.debian.org/stable/python3
__ https://packages.debian.org/oldstable/python3
__ https://www.pypy.org/
