#!/usr/bin/env python3

# A Fritzing part check script. This will read various types of Fritzing files
# (.fzp and .svg) and both check them for correctness and converting xml
# formats (such as CSS style and px on font-size) that Fritzing doesn't support
# in to equivelent xml that Fritzing does support. As well it will convert old
# style white silkscreen images to the new black silkscreen standard.

# Set Debug to 0 for normal operation (rename the input file and write the
# pretty printed output to the input file name.
#
# Set Debug to 1 to not rename the input file and write the output to stdout
# rather than the file for debugging but with no debug messages.
#
# Set Debug to 2 to not rename the input file and write the output to stdout
# rather than the file for debugging with debug messages for entry and exit
# from routines.
#
# Set Debug to 3 to not rename the input file and write the output to stdout
# rather than the file for debugging with verbous debug messages for detail
# debugging.

import logging
import re
import sys
import PPTools as PP
import FritzingTools as Fritzing
import os
Debug = 0

Version = '0.0.3'  # Version number of this file.

# Set up the requested debug level

# Import os and sys to get file rename and the argv stuff, re for regex and
# logging for logging support


if Debug == 3:

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

elif Debug == 2:

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

else:

    # For debug levels 0 and 1

    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

# End of if Debug == 3:

# Import various svg routines and pretty printing routines.


# Start of the main script

# Set the Errors flag to 'n' to indicate no errors yet.

ErrorsSeen = 'n'

# Create the processed dictionary to keep track of what files have been
# processed in a dir dir context to prevent part. type svg files from being
# processed twice (which would destroy the original file as it got backed up
# for the second time). The FzpDict gets reset for each file and thus won't
# do for this purpose.

FilesProcessed = {}

# Set default initial values for a variety of global variables.

Errors, Warnings, Info, FzpDict, CurView, TagStack, State, InheritedAttributes = Fritzing.InitializeAll()

# PrefixDir needs to be global even between files, so reset it once here.

PrefixDir = None

FileType, DirProcessing, PrefixDir, Path, File, SrcDir, DstDir = Fritzing.ProcessArgs(
    sys.argv, Errors)

logging.debug(' FritzingCheckPart.py FileType %s, DirProcessing %s  PrefixDir %s,  Path %s, File %s, SrcDir %s, DstDir %s\n',
              FileType, DirProcessing, PrefixDir, Path, File, SrcDir, DstDir)

# If the returned FileType is None then go print the errors then exit.

if FileType == None:

    PP.PrintErrors(Errors)

    sys.exit(1)

# End of FileType == None:

# Regex to match '.svg' to find svg files (ignoring case)

SvgExtRegex = re.compile(r'\.svg$', re.IGNORECASE)

# Regex to match .fzp to find fzp files

FzpExtRegex = re.compile(r'\.fzp$', re.IGNORECASE)

# Regex to match 'part. to identify an unzipped fzpz file'

PartRegex = re.compile(r'^part\.', re.IGNORECASE)

SVgPrefixRegex = re.compile(r'^svg\.', re.IGNORECASE)

if DirProcessing == 'Y':

    # The input is two directories (src and dst), so process the files in src
    # directory one at a time and write the results to the dst directory.
    # There are three cases, One: a directory of svg files only, which will
    # be processed and written to the dst directory (although the empty
    # directories for the svg files will be there as well) Two: a fzp file
    # where first the fzp file will be processed, and then its associated
    # svg files will be processed (with data from the fzp file to check against
    # the svg data) and written in to the corresponding directories under the
    # dst directory. Three: a part.filename.fzp which will be processed in to
    # the dst directory, and then its associated svg files which will also be
    # processed in to the dst directory (again with the empty svg directories
    # being present as well). As the fzp file is processed (and its associated
    # svgs) the svg filenames will be added to the FilesProcessed dictionary
    # and tested for here so that the svg does not get processed as part of
    # the fzp and then again as the individual svg (without the connector
    # information from the fzp) to avoid duplication, less information
    # (because of no fzp data), confusion and most importantly loss of the
    # original input file. Any svg files that aren't referenced by an fzp will
    # get processed as svg files though.

    # Then process all the files in the src directory

    for InFile in os.listdir(SrcDir):

        # Set the input and output file nams

        FQInFile = os.path.join(SrcDir, InFile)

        FQOutFile = os.path.join(DstDir, InFile)

        # Then get just the file name (no path) for the regexs and the svg
        # already processed as part of an fzp check.

        BaseFile = os.path.basename(FQInFile)

        # Determine if this is a part. type file or not.

        if PartRegex.search(BaseFile) or SVgPrefixRegex.search(BaseFile):

            FzpType = 'FZPPART'

        else:

            FzpType = 'FZPFRITZ'

        # End of if PartRegex.search(BaseFile) or
        # SVgPrefixRegex.search(BaseFile):

        logging.debug(
            ' FritzingCheckPart.py dir loop set FzpType %s\n', FzpType)

        # Check the dictionary to make sure we haven't already processed this
        # svg as part of one of the fzp files we have already processed.

        logging.debug(
            ' FritzingCheckPart.py dir loop trying FQInFile %s\n', FQInFile)

        if not 'processed.' + FQInFile in FilesProcessed:

            logging.debug(
                ' FritzingCheckPart.py didn\'t find \"%s\" in FilesProcessed\n', 'processed.' + FQInFile)

            # We haven't yet processed this file so do so now.

            # Initialize all the global variables before processing a new file.

            Errors, Warnings, Info, FzpDict, CurView, TagStack, State, InheritedAttributes = Fritzing.InitializeAll()

            print('\n**** Starting to process file {0:s}'.format(str(InFile)))

            if SvgExtRegex.search(BaseFile):

                # This looks to be an svg file so process it.

                # set the FzpType to None (as dir to dir processing doesn't
                # require filename translation).

                Doc = Fritzing.ProcessSvg(FzpType, 'SVG', FQInFile, FQOutFile, CurView, PrefixDir, Errors,
                                          Warnings, Info, FzpDict, FilesProcessed, TagStack, State, InheritedAttributes, Debug)

            elif PartRegex.search(BaseFile):

                # This looks to be an part.filename.fzp file so process it.

                # set the FzpType to 'dir' (as dir to dir processing doesn't
                # require filename translation) and FileType to 'fzpPart'.

                Doc = Fritzing.ProcessFzp(DirProcessing, FzpType, 'FZPPART', FQInFile, FQOutFile, CurView, PrefixDir,
                                          Errors, Warnings, Info, FzpDict, FilesProcessed, TagStack, State, InheritedAttributes, Debug)

            elif FzpExtRegex.search(BaseFile):

                # This looks to be a filename.fzp file so process it.

                # set the FzpType to 'dir' (as dir to dir processing doesn't
                # require filename translation) and FileType to 'fzpFritz'.
                # We do however need to add the PrefixDir to the output
                # filename.

                FQOutFile = os.path.join(DstDir, PrefixDir)

                FQOutFile = os.path.join(FQOutFile, InFile)

                Doc = Fritzing.ProcessFzp(DirProcessing, FzpType, 'FZPFRITZ', FQInFile, FQOutFile, CurView, PrefixDir,
                                          Errors, Warnings, Info, FzpDict, FilesProcessed, TagStack, State, InheritedAttributes, Debug)

            else:

                # Not a fritzing file type so warn about it but otherwise
                # ignore it.

                Warnings.append(
                    'Warning 1: File\n\n\'{0:s}\'\n\nIsn\'t a Fritzing file and has been ignored in processing the directory\n'.format(str(InFile)))

            # End of if SvgExtRegex.search(InFile):

            if len(Errors) != 0:

                # If we have seen errors in this file, note that to set the
                # eventual return code when all processing is done.

                ErrorsSeen = 'Y'

            # End of if len(Errors) != 0:

            # Output the Info, Warnings and Errors associated with the document
            # before they get cleared for the next file.

            PP.PrintInfo(Info)

            PP.PrintWarnings(Warnings)

            PP.PrintErrors(Errors)

        else:

            logging.debug(
                ' FritzingCheckPart.py skipped file %s as already proessed\n', FQInFile)

        # End of if not 'processed.' + FQInFile in FilesProcessed:

    # End of for InFile in os.listdir(SrcDir):

elif FileType == 'SVG':

    # This looks to be an svg file so process it  Create the input file name
    # from Path, PrefixDir and File then set the output file to None
    # to cause the input file to be moved to .bak and be replaced by the
    # output.

    InFile = os.path.join(Path, PrefixDir)

    InFile = os.path.join(InFile, File)

    # set the FzpType

    if SVgPrefixRegex.match(File):

        logging.debug(' FritzingCheckPart.py: set FzpType fzpPart\n')

        FzpType = 'FZPPART'

    else:

        logging.debug(' FritzingCheckPart.py: set FzpType fzpfritz\n')

        FzpType = 'FZPFRITZ'

    # End of if SVgPrefixRegex.match(File):

    Doc = Fritzing.ProcessSvg(FzpType, FileType, InFile, None, CurView, PrefixDir, Errors,
                              Warnings, Info, FzpDict, FilesProcessed, TagStack, State, InheritedAttributes, Debug)

    # Output the Info, Warnings and Errors associated with the document

    PP.PrintInfo(Info)

    PP.PrintWarnings(Warnings)

    PP.PrintErrors(Errors)

elif FileType == 'FZPPART':

    # This looks to be an fzpPart file so process it  Create the input file name
    # from Path, PrefixDir and File then set the output file to None
    # to cause the input file to be moved to .bak and be replaced by the
    # output.

    InFile = os.path.join(Path, PrefixDir)

    InFile = os.path.join(InFile, File)

    # set the FzpType to 'fzpPart' by reusing FileType in this call

    Doc = Fritzing.ProcessFzp(DirProcessing, FileType, FileType,  InFile, None, CurView, PrefixDir,
                              Errors, Warnings, Info, FzpDict, FilesProcessed, TagStack, State, InheritedAttributes, Debug)

    # Output the Info, Warnings and Errors associated with the document

    PP.PrintInfo(Info)

    PP.PrintWarnings(Warnings)

    PP.PrintErrors(Errors)

elif FileType == 'FZPFRITZ':

    # This looks to be an fzp file so process it  Create the input file name
    # from Path, PrefixDir and File then set the output file to None
    # to cause the input file to be moved to .bak and be replaced by the
    # output.

    InFile = os.path.join(Path, PrefixDir)

    InFile = os.path.join(InFile, File)

    # set the FleType to 'fzpFritz'

    logging.debug(' FritzingCheckPart.py: Call ProcessFzp Infile %s\n', InFile)

    # Use FileType as the FzpType in this call

    Doc = Fritzing.ProcessFzp(DirProcessing, FileType, FileType, InFile, None, CurView, PrefixDir,
                              Errors, Warnings, Info, FzpDict, FilesProcessed, TagStack, State, InheritedAttributes, Debug)

    # Output the errors and warnings associated with the document

    PP.PrintInfo(Info)

    PP.PrintWarnings(Warnings)

    PP.PrintErrors(Errors)

else:

    Errors.append(
        'Error 8: Unknown FileType {0:s} (should not occur, software error)\n'.format(str(FileType)))

# End of if FileType == 'dir':

if len(Errors) != 0:

    # if there were errors set the flag so we exit non 0

    ErrorsSeen = 'y'

# End of if len(Errors) != 0:

if ErrorsSeen == 'y':

    # An error occurred in at least one file so exit non zero.

    sys.exit(1)

else:

    # no errors so exit with rc 0

    sys.exit(0)

# End of if ErrorsSeen == 'Y`:
