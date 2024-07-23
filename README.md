# Krita Python API documentation builder

This script allows to build API documentation for [Krita](https://krita.org).

_An online version of produced documentation is available at https://apidoc.krita.maou-maou.fr_
_This documentation is updated every night at ~00.30am UTC_


## Download, Install & Execute

_Instructions are provided for Linux_

To use the tool, you'll need:
- Python3 (normally available by default on most Linux distro, if not check how to install it for your distro)
- GIT (check how to install it for your distro)
- Krita Python API documentation builder
- Krita source code

### Create directories

_Instructions and examples will assume the following paths are used; adapt instructions to paths you want to use_

Create following directories:
- `~/kritadoc`
- `~/kritadoc/html`

### Download & Install _Krita Python API documentation builder_

```bash
cd ~/kritadoc
git clone https://github.com/Grum999/PyKritaAPI.git
```

### Download Krita Source code

```bash
cd ~/kritadoc
git clone https://invent.kde.org/kde/krita.git
```


## Execute script

Command to execute:

```bash
cd ~/kritadoc/PyKritaAPI
./pykritaapi.py --kritaSrc ~/kritadoc/krita --output-html ~/kritadoc/html
```

Produced HTML documentation will be available in `~/kritadoc/html` directory.

> **Note **
> During process, the script will proceed to checkout of all tags.
> If the local Krita repository provided is the one used for your developments, take care to not have any ongoing untracked/uncommited change - checkout may fails:
- Use a dedicated local repository \
or
- Stash all your changes before using the script

First execution may takes some times as script will do a checkout for all releases tags.
For next executions, only new tags are checked out.

You can force script to a complete rebuild with `--reset` option

```bash
cd ~/kritadoc/PyKritaAPI
./pykritaapi.py --kritaSrc ~/kritadoc/krita --output-html ~/kritadoc/html --reset
```

There's some additional options, use option `--help` to list them:
```bash
cd ~/kritadoc/PyKritaAPI
./pykritaapi.py --help
```

## Releases

_[2024-07-23] Version [1.2.0](./releases/tag/1.2.0)_
- For parameters and returned values for which type is a Krita API class, manage hyperlink to class


## License

### *Krita Python API documentation builder* is released under the GNU General Public License (version 3 or any later version).

*Krita Python API documentation builder* is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.

*Krita Python API documentation builder* is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should receive a copy of the GNU General Public License along with *Krita Python API documentation builder*. If not, see <https://www.gnu.org/licenses/>.


Long story short: you're free to download, modify as well as redistribute *Krita Python API documentation builder* as long as this ability is preserved and you give contributors proper credit. This is the same license under which Krita is released, ensuring compatibility between the two.
