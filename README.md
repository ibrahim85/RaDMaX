RaDMaX is a program that allows to retrieve strain and damage profiles in ion-irradiated materials from the simulation of X-ray diffraction data recorded in symmetric thêta-2thêta geometry. It is distributed freely under the CeCILL license (see LICENSE.txt and COPYRIGHT.txt).

**If you use this program in academic work, please cite:**
M. Souilah, A. Boulle, A. Debelle, "RaDMaX: a graphical program for the determination of strain and damage profiles in irradiated crystals", _J. Appl.Cryst._ **49**, 311-316 (2016). [Link to article.] (http://dx.doi.org/10.1107/S1600576715021019)

# Installation instructions
Download zip file and extract it to your disk.

RaDMaX requires python 2.7, SciPy, Matplotlib and wxPython. For the moment, the wxpython library is not compatible with Python 3 and above. **RaDMaX won't work with Python 3.** Instructions for Windows and GNU/Linux are given below.


## MS Windows
1. For most users, especially on Windows and Mac, the easiest way to install scientific Python is to download **one** of these Python distributions, which includes most of the key packages:
 
 * [Anaconda](http://continuum.io/downloads): A free distribution for the SciPy stack. Supports Linux, Windows and Mac. [Download.](https://3230d63b5fc54e62148e-c95ac804525aac4b6dba79b00b39d1d3.ssl.cf1.rackcdn.com/Anaconda-2.3.0-Windows-x86.exe)
 * [Python(x,y)](http://python-xy.github.io/): A free distribution including the SciPy stack, based around the Spyder IDE. Windows only. [Download.](http://ftp.ntua.gr/pub/devel/pythonxy/Python(x,y)-2.7.10.0.exe)
 * [WinPython](http://winpython.github.io/): A free distribution including the SciPy stack. Windows only. [Download.] (http://sourceforge.net/projects/winpython/files/WinPython_2.7/2.7.9.5/WinPython-32bit-2.7.9.5.exe/download)


2. Download and install [wxPython] (http://downloads.sourceforge.net/wxpython/wxPython3.0-win32-3.0.2.0-py27.exe)
3. Finally execute the "Radmax.py" file. Alternatively, open a terminal (press "windows" and "r", type "cmd" [without commas] and press "Enter"). Navigate to the "Radmax" folder and type `python Radmax.py`. **The first execution of the program may take some time.**


## GNU / Linux
1. On most Linux systems the dependencies are available in the software repositories. For debian based systems run (as root): `apt-get install python python-scipy python-matplolib python-wxgtk3.0`. 
2. In a terminal, run the Radmax.py file with `python Radmax.py`.
 
For other distributions please visit the [python 2.7] (http://www.python.org), [SciPy](http://www.scipy.org), [Matplotlib](http://www.matplotlib.org) and [wxPython] (http://www.wxpython.org) websites.

## Mac OSX
1. Macs don’t come with a package manager. Fortunately, you can use for instance a private package manager [Macports](http://www.macports.org/) to install the SciPy package which already contains Matplotlib.
Run (as root): `port install py27-numpy py27-scipy py27-matplotlib py27-ipython +notebook py27-pandas py27-sympy py27-nose`.
2. Download and install [wxPython](http://www.wxpython.org/download.php#osx), choose the install that fit your system, if OSX < 10.5, [wxPython](http://sourceforge.net/projects/wxpython/files/wxPython/3.0.2.0/wxPython3.0-osx-3.0.2.0-carbon-py2.7.dmg/download?use_mirror=kent)
or OSX > 10.5 [wxPython](http://sourceforge.net/projects/wxpython/files/wxPython/3.0.2.0/wxPython3.0-osx-3.0.2.0-cocoa-py2.7.dmg/download?use_mirror=vorboss) 
3. In a terminal, run the Radmax.py file with `python Radmax.py`.

## Development environment
The RaDMaX program has been developed on MS Windows using python 2.7.10, Matplotlib 1.4.3 and 1.5.0 and WxPython 3.0.2.0.
It has been tested on several GNU/Linux distributions including Debian 8 and Kubuntu 15.04, using python 2.7.9, Matplotlib 1.4.2 and WxPython 3.0.1.1. It also has been tested on a MacMini running OSX Yosemite 10.10.5 with python 2.7.10, Matplotlib 1.5.0 and WxPython 3.0.2.0.


# Quick test of the program
1. In a text editor open the "test.ini" file located in the "examples/YSZ" or "examples/SiC-3C" folder. Modify lines 5-7: insert the paths of the files on your system. For instance, for a Radmax file located in the "documents" folder:

   * Windows: C:\Users\User_name\Documents\
   * Linux: /home/user_name/Documents/
2. Launch Radmax.py.
3. In the "File" menu select "Load Project".
4. Navigate to the "examples/YSZ" or "examples/SiC-3C" folder and load the "test.ini" file.

* Any change in any of the upper panels has to be validated with the "Update" button to update the XRD curve.
* The strain and damage profiles can be modified by dragging the control points. The XRD curve is updated in real time.
* The strain and damage profile can be scaled up or down with the mouse wheel + pressing the "u" key. The XRD curve is update when the "u" key is released.
* Calculated XRD curves can be fitted to experimental data in the "Fitting window" tab.
* Conventional least-squares (recommended) or generalized simulated annealing algorithm can be used.
* The fitted curve, the strain and damage profiles are automatically saved (*.txt) in the folder selected above. 

# Data format
XRD data can be loaded from the "File" menu. The data should be provided as a two-columns (2thêta, intensity) ASCII file in space- (or tab-) separated format. The 2thêta values have to be equally spaced (constant step). For the moment RaDMaX can only handle data recorded in symmetric coplanar geometry (conventional thêta-2thêta scan), as this is the most commonly used geometry in the analysis of irradiated materials.

Guess strain/damage profile can be imported from the "File" menu. The data should be providedas a two-columns ASCII file with the depth below the surface (in Angstroms) as first column.

# Screenshots
RaDMaX running in Windows 10

![Screenshot](https://raw.github.com/aboulle/RaDMaX/master/Screen1.png)

# Screencast
