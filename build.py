#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
if sys.version_info.major < 3 or sys.version_info.minor < 6:
    raise RuntimeError('Python 3.6+ is required for this script. You have: {}.{}'.format(
        sys.version_info.major, sys.version_info.minor))

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'core' / 'utils'))
import downloads
import domain_substitution
import prune_binaries
import patches
from distutils.dir_util import copy_tree
from _common import ENCODING, USE_REGISTRY, ExtractorEnum, get_logger, get_breeze_version
sys.path.pop(0)

_ROOT_DIR = Path(__file__).resolve().parent
_PATCH_BIN_RELPATH = Path('third_party/git/usr/bin/patch.exe')

source_tree = _ROOT_DIR / 'build' / 'src'
downloads_cache = _ROOT_DIR / 'build' / 'downloads_cache'
domsubcache = _ROOT_DIR / 'build' / 'domsubcache.tar.gz'
breeze_core = _ROOT_DIR / 'core'

def _get_vcvars_path(name='64'):
    """
    Returns the path to the corresponding vcvars*.bat path

    As of VS 2017, name can be one of: 32, 64, all, amd64_x86, x86_amd64
    """
    vswhere_exe = '%ProgramFiles(x86)%\\Microsoft Visual Studio\\Installer\\vswhere.exe'
    result = subprocess.run(
        '"{}" -latest -property installationPath'.format(vswhere_exe),
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        universal_newlines=True)
    vcvars_path = Path(result.stdout.strip(), 'VC/Auxiliary/Build/vcvars{}.bat'.format(name))
    if not vcvars_path.exists():
        raise RuntimeError(
            'Could not find vcvars batch script in expected location: {}'.format(vcvars_path))
    return vcvars_path


def _run_build_process(*args, **kwargs):
    """
    Runs the subprocess with the correct environment variables for building
    """
    # Add call to set VC variables
    cmd_input = ['call "%s" >nul' % _get_vcvars_path()]
    cmd_input.append('set DEPOT_TOOLS_WIN_TOOLCHAIN=0')
    cmd_input.append(' '.join(map('"{}"'.format, args)))
    cmd_input.append('exit\n')
    subprocess.run(('cmd.exe', '/k'),
                   input='\n'.join(cmd_input),
                   check=True,
                   encoding=ENCODING,
                   **kwargs)

def _copy_files(src, dst = source_tree):
    if os.path.isdir(src):
        copy_tree(str(src), str(dst))
    else:
        print(str(src) + " doesn't exist")

def _make_tmp_paths():
    """Creates TMP and TEMP variable dirs so ninja won't fail"""
    tmp_path = Path(os.environ['TMP'])
    if not tmp_path.exists():
        tmp_path.mkdir()
    tmp_path = Path(os.environ['TEMP'])
    if not tmp_path.exists():
        tmp_path.mkdir()

def _package():
    try:
        os.remove('build/Breeze_{}_installer.exe'.format(
            get_breeze_version()))
    except:
        print()
    shutil.copyfile('build/src/out/Default/mini_installer.exe',
        'build/Breeze_{}_installer.exe'.format(
            get_breeze_version()))

def main():
    """CLI Entrypoint"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--disable-ssl-verification',
        action='store_true',
        help='Disables SSL verification for downloading')
    parser.add_argument(
        '--7z-path',
        dest='sevenz_path',
        default=USE_REGISTRY,
        help=('Command or path to 7-Zip\'s "7z" binary. If "_use_registry" is '
              'specified, determine the path from the registry. Default: %(default)s'))
    parser.add_argument(
        '--winrar-path',
        dest='winrar_path',
        default=USE_REGISTRY,
        help=('Command or path to WinRAR\'s "winrar.exe" binary. If "_use_registry" is '
              'specified, determine the path from the registry. Default: %(default)s'))
    args = parser.parse_args()

    # Copy files
    _copy_files(_ROOT_DIR / 'core' / 'wip_src' / 'src')
    _copy_files(_ROOT_DIR / 'core' / 'icons_src' / 'src')
    _copy_files(breeze_core / 'supporting-extensions' / 'default_extensions', source_tree / 'chrome' / 'browser' / 'extensions' / 'default_extensions')
    _copy_files(breeze_core / 'breeze-dashboard' / 'out', source_tree / 'chrome' / 'browser' / 'extensions' / 'default_extensions')
    _copy_files(breeze_core / 'privacy-master-controller', source_tree / 'chrome' / 'browser' / 'resources' / 'privacy_master_controller')
    _copy_files(breeze_core / 'breeze-webstore-extension', source_tree / 'chrome' / 'browser' / 'resources' / 'breeze_webstore')

    # Output args.gn
    if not os.path.isdir(source_tree / 'out/Default'):
        (source_tree / 'out/Default').mkdir(parents=True)
    gn_flags = (_ROOT_DIR / 'core' / 'flags.gn').read_text(encoding=ENCODING)
    gn_flags += '\n'
    gn_flags += (_ROOT_DIR / 'flags.windows.gn').read_text(encoding=ENCODING)
    (source_tree / 'out/Default/args.gn').write_text(gn_flags, encoding=ENCODING)

    # Setup environment
    source_tree.mkdir(parents=True, exist_ok=True)
    downloads_cache.mkdir(parents=True, exist_ok=True)
    _make_tmp_paths()

    # Enter source tree to run build commands
    os.chdir(source_tree)

    # Run GN bootstrap
    _run_build_process(
        sys.executable, 'tools\\gn\\bootstrap\\bootstrap.py', '-o', 'out\\Default\\gn.exe',
        '--skip-generate-buildfiles')

    # Run gn gen
    _run_build_process('out\\Default\\gn.exe', 'gen', 'out\\Default', '--fail-on-unused-args')
    
    # Run ninja
    _run_build_process('third_party\\ninja\\ninja.exe', '-C', 'out\\Default', 'chrome',
                       'chromedriver', 'mini_installer', 'google_update')

    # Output exe file to build folder
    os.chdir(_ROOT_DIR)
    _package()

if __name__ == '__main__':
    main()
