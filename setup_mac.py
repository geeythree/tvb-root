# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under 
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General 
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
Create TVB distribution package for Mac OS.

Execute:
    python setup_py2app.py py2app

"""

#Prepare TVB code and dependencies.
import os
import sys
import platform
from glob import glob
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED
import shutil
import setuptools
from tvb.basic.profile import TvbProfile
import tvb_bin

BIN_FOLDER = os.path.dirname(tvb_bin.__file__)
TVB_ROOT = os.path.dirname(__file__)
DIST_FOLDER = os.path.join(TVB_ROOT, "dist")
DIST_FOLDER_FINAL = "TVB_Distribution"
STEP1_RESULT = os.path.join(TVB_ROOT, "build_resources", "tvb_builder", "build", "TVB_Distribution_a.zip")

FW_FOLDER = os.path.join(TVB_ROOT, "framework_tvb")
VERSION = TvbProfile.current.version.BASE_VERSION

FOLDERS_TO_DELETE = ['.svn', '.project', '.settings']
FILES_TO_DELETE = ['.DS_Store', 'dev_logger_config.conf']


def _create_command_file(command_file_path, command, before_message, done_message=False):
    """
    Private script which adds the common part of a command file.
    """
    pth = command_file_path + ".command"
    with open(pth, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('cd "$(dirname "$0")"\n')
        f.write('echo "' + before_message + '"\n')
        f.write(command + "\n")
        if done_message:
            f.write('echo "Done."\n')


def _copy_collapsed(to_copy):
    """
    Merge multiple src folders, and filter some resources which are not needed (e.g. svn folders)
    """
    for module_path, destination_folder in to_copy.iteritems():
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        for sub_folder in os.listdir(module_path):
            src = os.path.join(module_path, sub_folder)
            dest = os.path.join(destination_folder, sub_folder)

            if not os.path.isdir(src) and not os.path.exists(dest):
                shutil.copy(src, dest)

            if os.path.isdir(src) and not sub_folder.startswith('.') and not os.path.exists(dest):
                ignore_patters = shutil.ignore_patterns('.svn', '*.rst')
                shutil.copytree(src, dest, ignore=ignore_patters)


def add_sitecustomize(base_folder, destination_folder):
    full_path = os.path.join(base_folder, destination_folder, "sitecustomize.py")
    with open(full_path, 'w') as sc_file:
        sc_file.write("# -*- coding: utf-8 -*-\n\n")
        sc_file.write("import sys\n")
        sc_file.write("sys.setdefaultencoding('utf-8')\n")


def copy_simulator_library(library_folder):
    """
    Make sure all TVB folders are collapsed together in one folder in distribution.
    """
    import tvb

    destination_folder = os.path.join(library_folder, 'tvb')
    for module_path in tvb.__path__:
        for sub_folder in os.listdir(module_path):
            src = os.path.join(module_path, sub_folder)
            dest = os.path.join(destination_folder, sub_folder)
            if os.path.isdir(src) and not (sub_folder.startswith('.')
                                           or sub_folder.startswith("tests")) and not os.path.exists(dest):
                print "  Copying TVB: " + str(src)
                shutil.copytree(src, dest)

    tests_folder = os.path.join(destination_folder, "tests")
    if os.path.exists(tests_folder):
        shutil.rmtree(tests_folder, True)
        print "  Removed: " + str(tests_folder)

    for excluded in [os.path.join(destination_folder, "simulator", "doc"),
                     os.path.join(destination_folder, "simulator", "demos")]:
        if os.path.exists(excluded):
            shutil.rmtree(excluded, True)
            print "  Removed: " + str(excluded)


def introspect_licenses(destination_folder, root_introspection, extra_licenses_check=None):
    """Generate archive with 3rd party licenses"""
    print "- Introspecting for dependencies..." + str(root_introspection)
    import locale

    try:
        locale.getdefaultlocale()
    except Exception:
        os.environ['LANG'] = 'en_US.UTF-8'
        os.environ['LC_ALL'] = 'en_US.UTF-8'
    from third_party_licenses.build_licenses import generate_artefact

    zip_name = generate_artefact(root_introspection, extra_licenses_check=extra_licenses_check)
    ZipFile(zip_name).extractall(destination_folder)
    os.remove(zip_name)
    print "- Dependencies archive with licenses done."


def zipdir(basedir, archivename):
    """Create ZIP archive from folder"""
    assert os.path.isdir(basedir)
    with closing(ZipFile(archivename, "w", ZIP_DEFLATED)) as z_file:
        for root, _, files in os.walk(basedir):
            #NOTE: ignore empty directories
            for file_nname in files:
                absfn = os.path.join(root, file_nname)
                zfn = absfn[len(basedir) + len(os.sep):]
                z_file.write(absfn, zfn)


def clean_up(folder_path, to_delete):
    """
    Remove any read only permission for certain files like those in .svn, then delete the files.
    """
    #Add Write access on folder
    folder_name = os.path.split(folder_path)[1]
    will_delete = False
    os.chmod(folder_path, 0o777)
    if to_delete or folder_name in FOLDERS_TO_DELETE:
        will_delete = True

    #step through all the files/folders and change permissions
    for file_ in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_)
        os.chmod(file_path, 0o777)
        #if it is a directory, do a recursive call
        if os.path.isdir(file_path):
            clean_up(file_path, to_delete or will_delete)
        #for files merely call chmod
        else:
            if file_ in FILES_TO_DELETE:
                os.remove(file_path)

    if to_delete or will_delete:
        shutil.rmtree(folder_path)


def _generate_distribution(final_name, library_path, version, extra_licensing_check=None):
    # merge sources
    library_abs_path = os.path.join(DIST_FOLDER, library_path)

    copy_simulator_library(library_abs_path)

    shutil.copytree(os.path.join("externals", "BCT"), os.path.join(DIST_FOLDER, library_path, "externals", "BCT"))
    #write_svn_current_version(os.path.join(DIST_FOLDER, library_path))

    add_sitecustomize(DIST_FOLDER, library_path)

    bin_src = os.path.join(DIST_FOLDER, "_tvb_bin")
    bin_dst = os.path.join(library_abs_path, "tvb_bin")
    print "- Moving " + bin_src + " to " + bin_dst
    os.rename(bin_src, bin_dst)

    demo_data_src = os.path.join(DIST_FOLDER, "_tvb_data")
    demo_data_dst = os.path.join(library_abs_path, "tvb_data")
    print "- Moving " + demo_data_src + " to " + demo_data_dst
    os.rename(demo_data_src, demo_data_dst)

    online_help_src = os.path.join(DIST_FOLDER, "_help")
    online_help_dst = os.path.join(library_abs_path, "tvb", "interfaces", "web", "static", "help")
    print "- Moving " + online_help_src + " to " + online_help_dst
    os.rename(online_help_src, online_help_dst)

    _copy_collapsed({os.path.join("tvb_documentation_new", "demos"): os.path.join(DIST_FOLDER, "demo_scripts"),
                     os.path.join("tvb_documentation_new", "tutorials"): os.path.join(DIST_FOLDER, "demo_scripts")})

    print "- Cleaning up non-required files..."
    clean_up(DIST_FOLDER, False)
    if os.path.exists(DIST_FOLDER_FINAL):
        shutil.rmtree(DIST_FOLDER_FINAL)
    os.rename(DIST_FOLDER, DIST_FOLDER_FINAL)
    shutil.rmtree('tvb.egg-info', True)
    shutil.rmtree('build', True)
    for file_zip in glob('*.zip'):
        os.unlink(file_zip)

    print "- Creating required folder structure..."
    if os.path.exists(final_name):
        shutil.rmtree(final_name)
    os.mkdir(final_name)
    shutil.move(DIST_FOLDER_FINAL, final_name)

    if extra_licensing_check:
        extra_licensing_check = extra_licensing_check.split(';')
        for idx in xrange(len(extra_licensing_check)):
            extra_licensing_check[idx] = os.path.join(final_name, DIST_FOLDER_FINAL, extra_licensing_check[idx])
    introspect_licenses(os.path.join(final_name, DIST_FOLDER_FINAL, 'THIRD_PARTY_LICENSES'),
                        os.path.join(final_name, DIST_FOLDER_FINAL, library_path), extra_licensing_check)
    print "- Creating the ZIP folder of the distribution..."
    architecture = '_x32_'
    if sys.maxint > 2 ** 32 or platform.architecture()[0] == '64bit':
        architecture = '_x64_'
    zip_name = final_name + "_" + version + architecture + "web.zip"
    if os.path.exists(zip_name):
        os.remove(zip_name)
    zipdir(final_name, zip_name)
    if os.path.exists(final_name):
        shutil.rmtree(final_name)
    print '- Finish creation of distribution ZIP'


#--------------------------- PY2APP specific configurations--------------------------------------------

PY2APP_PACKAGES = ['cherrypy', 'email', 'h5py', 'IPython', 'idlelib', 'migrate', 'minixsv',
                   'numpy', 'scipy', 'sklearn', 'tables', 'tornado', 'tvb']

PY2APP_INCLUDES = ['apscheduler', 'apscheduler.scheduler', 'cfflib', 'cmath', 'contextlib', 'formencode', 'gdist',
                   'genshi', 'genshi.template', 'genshi.template.loader', 'jinja2', 'jsonschema', 'logging.config',
                   'lxml.etree', 'lxml._elementpath', 'markupsafe', 'matplotlib', 'minixsv', 'mod_pywebsocket',
                   'mplh5canvas.backend_h5canvas', 'mpl_toolkits.axes_grid', 'nibabel', 'numexpr', 'os', 'psycopg2',
                   'runpy', 'sqlite3', 'sqlalchemy', 'sqlalchemy.dialects.sqlite', 'sqlalchemy.dialects.postgresql',
                   'simplejson', 'StringIO', 'xml.dom', 'xml.dom.minidom', 'zlib', 'zmq']

PY2APP_EXCLUDES = ['_markerlib', 'coverage', 'cython', 'Cython', 'tvb_data', 'docutils', 'lib2to3',
                   'nose', 'OpenGL', 'PyOpenGL', 'PyQt4', 'sphinx', 'wx']

PY2APP_OPTIONS = {'iconfile': 'build_resources/icon.icns',
                  'plist': 'build_resources/info.plist',
                  'packages': PY2APP_PACKAGES,
                  'includes': PY2APP_INCLUDES,
                  'frameworks': ['Tcl', 'Tk'],
                  'resources': [],
                  'excludes': PY2APP_EXCLUDES,
                  'argv_emulation': True,
                  'strip': True,  # TRUE is the default
                  'optimize': '0'}


#This is a list of all the dynamic libraries identified so far that are added by py2app even though apparently
#they are not used by TVB. We will exclude them from package so as not to worry about licenses.
EXCLUDED_DYNAMIC_LIBS = ['libbz2.1.0.dylib', 'libdb-4.6.dylib', 'libexslt.0.dylib',
                         'libintl.8.dylib', 'liblzma.5.dylib', 'libpng15.15.dylib', 'libtiff.3.dylib',
                         'libsqlite3.0.dylib', 'libXss.1.dylib', 'libxml2.2.dylib', 'libxslt.1.dylib']

#-------------- Finish configuration, starting build-script execution ---------------------------------

print "Running pre-py2app:"
print " - Cleaning old builds"

if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists(DIST_FOLDER):
    shutil.rmtree(DIST_FOLDER)

print "Decompressing " + STEP1_RESULT + " into '" + DIST_FOLDER
step1_tmp_dist_folder = os.path.join(TVB_ROOT, 'TVB_Distribution')
if os.path.exists(step1_tmp_dist_folder):
    shutil.rmtree(step1_tmp_dist_folder)
ZipFile(STEP1_RESULT).extractall(TVB_ROOT)
# the above created a TVB_Distribution/ we need a dist folder
shutil.move(step1_tmp_dist_folder, DIST_FOLDER)

print "PY2APP starting ..."
# Log everything from py2app in a log file
REAL_STDOUT, REAL_STDERR = sys.stdout, sys.stderr
sys.stdout = open('PY2APP.log', 'w')
sys.stderr = open('PY2APP_ERR.log', 'w')

FW_NAME = "framework_tvb"

setuptools.setup(name="tvb",
                 version=VERSION,
                 packages=setuptools.find_packages(FW_NAME),
                 package_dir={'': FW_NAME},
                 license="GPL v2",
                 options={'py2app': PY2APP_OPTIONS},
                 include_package_data=True,
                 extras_require={'postgres': ["psycopg2"]},
                 app=['tvb_bin/app.py'],
                 setup_requires=['py2app'])

sys.stdout = REAL_STDOUT
sys.stderr = REAL_STDERR
print "PY2APP finished."

print "Running post-py2app build operations:"
print "- Start creating startup scripts..."

# os.mkdir(os.path.join(DIST_FOLDER, "bin"))
os.mkdir(os.path.join(DIST_FOLDER, "demo_scripts"))

_create_command_file(os.path.join(DIST_FOLDER, "bin", 'distribution'),
                     '../tvb.app/Contents/MacOS/tvb $@', '')
_create_command_file(os.path.join(DIST_FOLDER, "bin", 'tvb_start'),
                     'source ./distribution.command start', 'Starting TVB Web Interface')
_create_command_file(os.path.join(DIST_FOLDER, "bin", 'tvb_clean'),
                     'source ./distribution.command clean', 'Cleaning up old TVB data.', True)
_create_command_file(os.path.join(DIST_FOLDER, "bin", 'tvb_stop'),
                     'source ./distribution.command stop', 'Stopping TVB related processes.', True)

IPYTHON_COMMAND = 'export PYTHONPATH=../tvb.app/Contents/Resources/lib/python2.7:' \
                  '../tvb.app/Contents/Resources/lib/python2.7/site-packages.zip:' \
                  '../tvb.app/Contents/Resources/lib/python2.7/lib-dynload\n' \
                  '../tvb.app/Contents/MacOS/python -m tvb_bin.run_ipython notebook '
_create_command_file(os.path.join(DIST_FOLDER, "bin", 'ipython_notebook'),
                      IPYTHON_COMMAND + '../demo_scripts', '')
# _create_command_file(os.path.join(DIST_FOLDER, "demo_scripts", 'ipython_notebook'), IPYTHON_COMMAND, '')

_create_command_file(os.path.join(DIST_FOLDER, "bin", 'contributor_setup'),
                     'cd ..\n'
                     'export PYTHONPATH=tvb.app/Contents/Resources/lib/python2.7:'
                     'tvb.app/Contents/Resources/lib/python2.7/site-packages.zip:'
                     'tvb.app/Contents/Resources/lib/python2.7/lib-dynload\n'
                     './tvb.app/Contents/MacOS/python  '
                     'tvb.app/Contents/Resources/lib/python2.7/tvb_bin/git_setup.py $1 $2\n'
                     'cd bin\n',
                     'Setting-up contributor environment', True)

#py2app should have a --exclude-dynamic parameter but it doesn't seem to work until now
for entry in EXCLUDED_DYNAMIC_LIBS:
    path = os.path.join(DIST_FOLDER, "tvb.app", "Contents", "Frameworks", entry)
    if os.path.exists(path):
        os.remove(path)

DESTINATION_SOURCES = os.path.join("tvb.app", "Contents", "Resources", "lib", "python2.7")

# this dependency is deprecated
_generate_distribution("TVB_MacOS", DESTINATION_SOURCES, VERSION)

## Clean after install      
shutil.rmtree(os.path.join(FW_FOLDER, 'tvb.egg-info'), True)    
    


