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
import save_original_files
import var_replace
import patch_made_files_remover
import set_version

from distutils.dir_util import copy_tree
from _common import ENCODING, USE_REGISTRY, ExtractorEnum, get_logger
sys.path.pop(0)

_ROOT_DIR = Path(__file__).resolve().parent
_PATCH_BIN_RELPATH = Path('third_party/git/usr/bin/patch.exe')

# Set common variables
source_tree = _ROOT_DIR / 'build' / 'src'
core_dir = _ROOT_DIR / 'core'
downloads_cache = _ROOT_DIR / 'build' / 'downloads_cache'
domsubcache = _ROOT_DIR / 'build' / 'domsubcache.tar.gz'
urlsubcache = _ROOT_DIR / 'build' / 'urlsubcache.tar.gz'
exesubcache = _ROOT_DIR / 'build' / 'exesubcache.tar.gz'
saved_patches = _ROOT_DIR / 'build' / 'patches'
temp_patches = _ROOT_DIR / 'build' /'temp_patches'

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
        print(src + " doesnt exists")
        

def _test_python2(error_exit):
    """
    Tests if Python 2 is setup with the proper requirements
    """
    python2_exe = shutil.which('python')
    if not python2_exe:
        error_exit('Could not find "python" in PATH')

    # Check Python version is at least 2.7.9 to avoid exec issues
    result = subprocess.run((python2_exe, '--version'),
                            stderr=subprocess.PIPE,
                            check=True,
                            universal_newlines=True)
    match = re.fullmatch(r'Python 2\.7\.([0-9]+)', result.stderr.strip())
    if not match:
        error_exit('Could not detect Python 2 version from output: {}'.format(
            result.stdout.strip()))
    if int(match.group(1)) < 9:
        error_exit('At least Python 2.7.9 is required; found 2.7.{}'.format(match.group(1)))

    # Check for pypiwin32 module
    result = subprocess.run((python2_exe, '-c', 'import win32api'))
    if result.returncode:
        error_exit('Unable to find pypiwin32 module in Python 2 installation.')


def _make_tmp_paths():
    """Creates TMP and TEMP variable dirs so ninja won't fail"""
    tmp_path = Path(os.environ['TMP'])
    if not tmp_path.exists():
        tmp_path.mkdir()
    tmp_path = Path(os.environ['TEMP'])
    if not tmp_path.exists():
        tmp_path.mkdir()

def main():
    # Test environment
    _test_python2(parser.error)

    # Setup environment
    source_tree.mkdir(parents=True, exist_ok=True)
    downloads_cache.mkdir(parents=True, exist_ok=True)
    _make_tmp_paths()

    series_files_list = [
        _ROOT_DIR / 'core' / 'patches',
        _ROOT_DIR / 'patches',
        _ROOT_DIR / 'core' / 'patches' / 'core' / 'breeze'
    ]
    patches.combine_patches(
        series_files_list,
        temp_patches
    )
    var_replace.main()
    if saved_patches.exists():
        patches.compare_new_patches(
                saved_patches,
                temp_patches,
                source_tree,
                patch_bin_path=(source_tree / _PATCH_BIN_RELPATH)
        )
    else:
        print('No previous patches found\n')
        print('Applying all!\n')
        patch_made_files_remover.main()
        _copy_files("build/unpatched")    
        save_original_files.main()
        # apply patches
        patches.apply_patches(
            patches.generate_patches_from_series(temp_patches, resolve=True),
            source_tree,
            patch_bin_path=(source_tree / _PATCH_BIN_RELPATH)
        )

    _copy_files(src = temp_patches, dst = saved_patches)
    shutil.rmtree(temp_patches)
    set_version.update_version(source_tree, core_dir / 'breeze_version.txt')

if __name__ == '__main__':
    main()
