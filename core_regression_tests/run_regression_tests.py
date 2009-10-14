#!/usr/bin/python
#
# Copyright (C) 1998-2009 by authors (see AUTHORS.txt 
#
# This file is part of LuxRender.
#
# Lux Renderer is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Lux Renderer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This project is based on PBRT ; see http://www.pbrt.org
# Lux Renderer website : http://www.luxrender.net

import os, sys, re, subprocess
from optparse import OptionParser
from stat import *

def LaunchAndWait(cmd):
    ostype = sys.platform

    if ostype == "win32":
        return os.system(cmd)
    elif ostype == "linux2" or ostype == "darwin":
        return subprocess.call(cmd, shell=True)
    else:
        print "Unsupportes OS type: " + ostype
        return -1

def LookForTests(rootDir, patterns):
    print "Scanning directory: " + rootDir

    testList = []
    for f in os.listdir(rootDir):
        pathName = os.path.join(rootDir, f)
        mode = os.stat(pathName)[ST_MODE]
        if S_ISDIR(mode):
            # Dade - it's a directory, recurse into it
            testList += LookForTests(pathName, patterns)
        elif S_ISREG(mode):
            # Dade - it's a file, check if it is a test
            if (re.match("^.*\.cfg$", pathName)):
                # Dade - check if the file name matches one of the pattern
                found = False
                for p in patterns:
                    if (re.match(p, pathName)):
                        found = True
                        break
                if (found):
                    print "Found test: " + pathName
                    testList.append(os.path.abspath(pathName))
        else:
            # Dade - unknown file type, print a message
            print "Skipping:  " + pathName

    return testList

def ExecuteTest(fileName, luxconsole, luxcomp):
    print "---------------------------------------------"
    print "Executing test: " + fileName

    try:
        os.chdir(os.path.dirname(fileName))

        lvars = {
            "sceneFile":"default.lxs",
            "referenceFilm":"reference.flm",
            "testFilm":"default.flm",
            "errorTreshold":"0.0001",
            "cleanFiles":"",
            }

        # Dade - execute the configuration file
        execfile(fileName, globals(), lvars)

        # Dade - build command to execute
        cmd = luxconsole + " -f " + lvars["sceneFile"]
        print "Rendering command to execute: " + cmd

        # Dade - execute the command
        if (LaunchAndWait(cmd) != 0):
            print "Error while executing the rendering"
            return False

        # Dade - build command to compare the rendering
        cmd = luxcomp + " -e " + str(lvars["errorTreshold"]) + " " + lvars["referenceFilm"] + " " + lvars["testFilm"]
        print "Test command to execute: " + cmd

        # Dade - execute film comparison
        if (LaunchAndWait(cmd) != 0):
            print "Error while executing film comparison"
            return False

        # Dade - clean temporary files
        for f in lvars["cleanFiles"].split(","):
            print "Deleteing temporary file: " + f
            os.unlink(f);
    except:
        print "Unexpected error:", sys.exc_info()
        return False
    else:
        return True
    finally:
        print "---------------------------------------------"


######################################################################
# Main
######################################################################

print "Luxrender core regression test suite V1.0"

# Dade - parse command line options

parser = OptionParser()
parser.add_option("-c", "--luxcomp-exe", dest="luxcomp", default="luxcomp",
                  help="Path of Luxcomp image compare tool")
parser.add_option("-l", "--luxconsole-exe", dest="luxconsole", default="luxconsole",
                  help="Path of Luxconsole executable")
parser.add_option("-r", "--root-dir", dest="rootdir", default=".",
                  help="Path of the root directory of tests")

(options, args) = parser.parse_args()

print "Luxcomp image compare tool: " + options.luxcomp
print "Luxconsole executable: " + options.luxconsole
print "Test root directory: " + options.rootdir

if (len(args) == 0):
    args.append(".*")

print "Test patterns:"

for t in args:
    print " [" + t + "]"

# Dade - build the list of tests to execute

testList = LookForTests(options.rootdir, args)

# Dade - execute tests

currentDir = os.path.abspath(options.rootdir);
testResults = {}
for t in testList:
    os.chdir(currentDir)
    result = ExecuteTest(t, options.luxconsole, options.luxcomp)
    testResults[t] = result
    print "Test " + t + " result: " + str(result)

# Dade - generate the test report

print "---------------------------------------------"
print "---------------------------------------------"
print "---------------------------------------------"
print "Test report:"

someFailed = False
for t in testList:
    if (testResults[t]):
        print "Test " + t + " result: OK"
    else:
        print "Test " + t + " result: FAILED !!!" 
    if (not testResults[t]):
        someFailed = True

if (someFailed):
    print "One or more tests FAILED !!!"
else:
    print "All tests are OK"
