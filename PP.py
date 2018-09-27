#!/usr/bin/env python3

# A python xml pretty_print script written to pretty print svg files from 
# Inkscape, but should work on pretty much any xml. 

# Set Debug to 0 for normal operation (rename the input file and write the 
# pretty printed output to the input file name.
# 
# Set Debug to 1 to not rename the input file and send the output to the 
# console rather than write it to the file, but no other debug messages.

# Set Debug to 2 for debug messages on entry and exit from subroutines and
# to not rename the input file iand write the output to the console rather 
# than the file for debugging. 

# Set Debug to 3 for very verbose debug messages. 

Debug = 0

Version = '0.0.2'  # Version number of this file.
	
# Import os and sys to get file rename and the argv stuff, re for regex and 
# logging to get logging support and the various svg routines from LxmlTools.
	
import os, sys, re, logging 

# Set up the requested debug level

if Debug == 3:

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

elif Debug == 2:

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

else:

    # Debug set to 0 or 1

    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

# End of if Debug == 3:

# The logging level needs to be set before we import this library.
	
import PPTools as PP

# Start of the main script

# Create an empty Errors, Warnings and Info (Warnings and Info not used) array

Errors = []

Warnings = []

Info = []

InFile = PP.ProcessArgs (sys.argv, Errors)	

if len(InFile) > 0:
	
    for File in InFile:

        print ('Process {0:s}\n'.format(str(File)))

        Doc, Root = PP.ParseFile (File, Errors)

        if Root != None:

            # If we managed to parse the file, then set up to pretty print it 
            # as if it was a svg (to pretty print to the element level). 
            # As we don't have a path broken out of the file name, set it to 
            # nothing (Fritzing processing needs the path when using these 
            # routines).

            FileType = 'SVG'

            Path = ''

            PP.OutputTree(Doc, Root, FileType, Path, File, Errors, Warnings, Info, Debug)

        # End of if Root != None:

    # End of for Files in InFile:

    # Print any error messages found. 

    PP.PrintErrors(Errors)
	
# End of if len(InFile) > 0:

# Set the return code depending on whether there were errors or not. 

if len(Errors) > 0:

    sys.exit(1)

else:

    sys.exit(0)

# end of if len(Errors) > 0:
