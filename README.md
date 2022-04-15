# Breeze for Windows

Windows packaging for [Breeze](../../../breeze-core).

## Building

This section will explain in detail how to build Breeze for Windows 10 x64.
The building process is very similiar to building `ungoogled_chromium`. [[1]](#1)
If you encounter any problem while following this tutorial, feel free to open an issue. 

### Setting up the build environment

**IMPORTANT**: Please set up only what is referenced below. Do NOT set up other Chromium compilation tools such as `depot_tools`, since we have a custom build process which avoids using Google's pre-built binaries.

#### Build Requirements
##### 0. PC Requirements
* Building chromium is a demanding process. It is recommended to have at least 8 GB of RAM, a high-end CPU to avoid a very long building time. Additionally, ~20GB of space will be needed to complete the whole build process. 
##### 1. Visual Studio 2019
* Download [Visual Studio 2019](https://visualstudio.microsoft.com/downloads/). Community edition will do.
* Make sure to select `Desktop development with C++`, all its default add-ons and `C++ MFC for latest version build tools (x86 & x64)` in Visual Studio Installer. You must have Windows 10 SDK version 10.0.19041 or higher installed. This can be installed separately or by checking the appropriate box in the Visual Studio Installer in `Additional components`. 
* SDK Debugging Tools must also be installed. If Windows 10 SDK was installed via the Visual Studio installer, then it can be installed by going to: Control Panel → Programs → Programs and Features → Select the “Windows Software Development Kit” → Change → Change → Check “Debugging Tools For Windows” → Change. Alternatively, you can download the [standalone SDK installer](https://developer.microsoft.com/en-us/windows/downloads/windows-10-sdk/) and use it to install SDK Debugging Tools. [[2]](#2)
##### 2. Python
* First install and configure Python 3.6+ following the next procedure:
    * Download [Python 3.6+](https://www.python.org/downloads/).
    * Add Python 3.6+ to `PATH` as `py`, select customize installation and make sure to check `Install for all users`. 
    * At the end of the Python installer, click the button to lift the `MAX_PATH` length restriction.
* Then install and configure the latest Python 2.7 following the next procedure:
    * Download [Python 2.7](https://www.python.org/downloads/release/python-2718/).
    * Select add `python.exe` to `PATH`.
    * Install `pypiwin32` module using `python -m pip install pypiwin32`.

**NOTE**:  To make sure both Python versions are installed correctly, open `cmd.exe` and make sure typing `py` starts Python 3.6+ while typing `python` starts Python 2.7
 If this is not the case, in Environment Variables → System Variables → Path set Python 2.7 above Python 3.6+.

##### 3. Other dependencies
* Install [7-zip](https://www.7-zip.org/download.html).
* Install [Git](https://git-scm.com/download/win) (to fetch all Breeze repositories).

### Building

Run `cmd.exe` as administrator, change the current directory to the one in which you wish to build Breeze and run the following commands:

##### Cloning the repository
```cmd
git clone https://github.com/privacyone/breeze-windows.git
cd breeze-windows
git submodule update --recursive --init
```
This will make a local main repository with all needed subrepositories.
##### Preparing chromium source files

```
py prepare_source.py
```
This will download and unpack archived chromium source files and required tools, `prune_binaries` and apply `domain_substitution` and `url_substitution` on the unpacked code. If no errors are encountered, this script should be run only once. If it fails, run the `remove_src.bat` script and wait for it to finish before trying `prepare_source.py` again.

##### Applying patches
```
py apply_patches.py
```
If no previous patches have been applied, this will apply all Windows specific and core patches. Otherwise, it will only apply updated patches.

##### Building
```
py build.py
```
This will start the build process. It may fail due to `out of memory error` or faulty code. The previous rarely occurs, while the latter is caused by anyone editing the source code. You can run the build again and it will continue the build process from where it previously failed. (Make sure to fix any faulty code!)

Once the build passes successfully, Breeze `.exe` file will be copied to `out` folder.

## References
<a id="1">[1]</a> [ungoogled-chromium-windows](https://github.com/ungoogled-software/ungoogled-chromium-windows)

<a id="2">[2]</a> Checking out and Building Chromium for Windows. Section [Visual Studio](https://chromium.googlesource.com/chromium/src/+/refs/tags/85.0.4183.102/docs/windows_build_instructions.md#visual-studio).

## License

See [LICENSE](LICENSE)
