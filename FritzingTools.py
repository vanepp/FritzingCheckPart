#!/usr/bin/python3

# Various support routines for processing Fritzing's fzp and svg files. 

# Change this from 'no' to 'yes' to cause 0 length/width terminal definitions
# to be warned about but not modified, to being changed (which will cause them
# to move in the svg and need repositioning) to a length/width of 10 (which 
# depending on scaling may or may not be .01in). The default is warn but not
# change, but I use modify as it is much easier converting 0 width parts with
# Inkscape like that.

ModifyTerminal = 'n'

# Import os and sys to get file rename and the argv stuff, re for regex, 
# logging to get logging support and PPTools for the parse routine

import os, sys, re, logging, PPTools as PP

# and the lxml library for the xml

from lxml import etree

def InitializeAll():

    # Initialize all of the global variables

    Errors = []

    Warnings = []

    Info = []

    FzpDict = {}

    FzpDict['connectors.fzp.breadboardView'] = []

    FzpDict['connectors.fzp.iconView'] = []

    FzpDict['connectors.fzp.pcbView'] = []

    FzpDict['connectors.fzp.schematicView'] = []

    FzpDict['views'] = []

    CurView = None

    TagStack = [['empty', 0]]

    State={'lasttag': 'none', 'nexttag': 'none', 'lastvalue': 'none', 'image': 'none', 'noradius': [], 'KeyErrors': []}

    InheritedAttributes=None

    return Errors, Warnings, Info, FzpDict, CurView, TagStack, State, InheritedAttributes

# End of def InitializeAll():

def InitializeState():

    # Initialize only the state related global variables (not the PrefixDir, 
    # Errors, Warnings or dictionary) to start processing a different file 
    # such as an svg linked from a fzp. 

    TagStack = [['empty', 0]]

    State={'lasttag': 'none', 'nexttag': 'none', 'lastvalue': 'none', 'image': 'none', 'noradius': [], 'KeyErrors': []}

    InheritedAttributes=None

    return TagStack, State, InheritedAttributes

# End of def InitializeState():

def ProcessArgs(Argv, Errors):

    # Process the input arguments on the command line. 

    logging.info (' Entering ProcessArgs\n')

    # Regex to match '.svg' to find svg files

    SvgExtRegex = re.compile(r'\.svg$', re.IGNORECASE)

    # Regex to match .fzp to find fzp files

    FzpExtRegex = re.compile(r'\.fzp$', re.IGNORECASE)

    # Regex to match 'part. to identify an unzipped fzpz file'

    PartRegex = re.compile(r'^part\.', re.IGNORECASE)

    # Regex to match 'part.filename' for substitution for both unix and windows.

    PartReplaceRegex = re.compile(r'^part\..*$|\/part\..*$|\\part\..*$', re.IGNORECASE)

    # Set the return values to the error return (really only FileType needs
    # to be done, but do them all for consistancy. Set PrefixDir and Path
    # to striing constants (not None) for the dir routines. 

    FileType = None

    PrefixDir = ""

    Path = ""

    File = None

    SrcDir = None

    DstDir = None

    if len(sys.argv) == 3:

        # If we have two directories, one empty, process all the fzp files in 
        # the first directory in to the empty second directory, creating 
        # subdirectories as needed (but no backup files!) 

        FileType, PrefixDir, Path, File, SrcDir, DstDir = ProcessDirArgs(Argv, Errors)

        return FileType, PrefixDir, Path, File, SrcDir, DstDir

    elif len(sys.argv) != 2:

        # No input file or too many arguments so print a usage message and exit.

        Errors.append('Usage 9: {0:s} filename.fzp or filename.svg or srcdir dstdir\n'.format(str(sys.argv[0])))

        return FileType, PrefixDir, Path, File, SrcDir, DstDir

    else:

        # only a single file is present so arrange to process it.

        InFile = sys.argv[1]

        logging.debug (' ProcessArgs: input filename %s\n', InFile)

        if not os.path.isfile(InFile) and not SvgExtRegex.search(InFile) and not FzpExtRegex.search(InFile):

            # Input file isn't valid, return a usage message.

            Errors.append('Usage 9: {0:s} filename.fzp or filename.svg or srcdir dstdir\n\n{1:s} either isn\'t a file or doesn\'t end in .fzp or .svg\n'.format(str(sys.argv[0]),  str(InFile)))

            return FileType, PrefixDir, Path, File, SrcDir, DstDir

        # End of if not os.path.isfile(InFile) and not SvgExtRegex.search(InFile) and not FzpExtRegex.search(InFile):

        Path = ''

        # First strip off the current path if any

        Path = os.path.dirname(InFile)

        if not Path:

            # No path present so set that

            Path = ''

        # End of if not Path:

        # and then get the filename 

        File = os.path.basename(InFile)

        if SvgExtRegex.search(File):

            # process a single svg file.

            FileType = 'svg'

            logging.debug (' ProcessArgs: Found svg input file %s set FileType %s\n', InFile, FileType)

        else:

            # this is an fzp file of some kind so figure out which kind and 
            # set the appropriate path.

            pat = PartRegex.search(File)

            logging.debug (' ProcessArgs: Found svg input file %s Match %s\n', InFile, pat)
    
            if PartRegex.search(File):
    
                # It is a part. type fzp, thus the svgs are in this same
                # directory named svg.image_type.filename so set FileType 
                # to fzpPart to indicate that.
    
                FileType = 'fzpPart'

                logging.debug (' ProcessArgs: Set filetype fzpPart\n')
    
            else:
    
                # This is a Fritzing internal type fzp and thus the svgs are in
                # svg/PrefixDir/image_type/filename.svg. So make sure we have a 
                # prefix directory on the input file. 

                # get the path from the input file. 

                Path = os.path.dirname(InFile)

                # and the file name

                File =  os.path.basename(InFile)
    
                SplitDir = os.path.split(Path)
    
                if SplitDir[1] == '' or SplitDir[1] == '.' or SplitDir[1] == '..':
    
                    Errors.append('Error 10: There must be a directory that is not \'.\' or \'..\' in the input name for\na fzp file in order to find the svg files.\n')
    
                    logging.info (' Exiting ProcessArgs no prefix dir error\n')
    
                    return FileType, PrefixDir, Path, File, SrcDir, DstDir
    
                # End of if SplitDir[1] == '' or SplitDir[1] == '.' or SplitDir[1] == '..':
        
                Path = SplitDir[0]
        
                PrefixDir =  SplitDir[1]

                if PrefixDir == None:

                    # Make sure PrefixDir has a string value not None for the
                    # path routines.

                    PrefixDir = ""

                # End of if PrefixDir == None:
        
                # then so set FileType to fzpFritz to indicate that. 
    
                FileType = 'fzpFritz'
    
                logging.debug (' Found Fritzing type input file %s path %s\n', InFile, Path)

                return FileType, PrefixDir, Path, File, SrcDir, DstDir
    
            # End of if PartRegex.search(File):
    
        # End of if SvgExtRegex.search(File):

    # End of if len(sys.argv) == 3:

    logging.debug (' ProcessArgs: End of ProcessArgs return FileType %s PrefixDir %s Path %s File %s\n', FileType, PrefixDir, Path, File)

    return FileType, PrefixDir, Path, File, SrcDir, DstDir

# End of def ProcessArgs(Argv, Errors):

def ProcessDirArgs(argv, Errors):

    logging.info (' Entering ProcessDirArgs\n')

    # Clear the return variables in case of error. 

    FileType = None

    PrefixDir = ""

    Path = ""

    File = None

    # Get the 2 directories from the input arguments.

    SrcDir = argv[1]

    DstDir = argv[2]

    # Check that the source is a directory

    if not os.path.isdir(SrcDir):

        Errors.append('Usage 11: {0:s} src_dir dst_dir\n\nsrc_dir {1:s} isn\'t a directory\n'.format(sys.argv[0], SrcDir))

        logging.info (' Exiting ProcessDirArgs src dir error\n')

        return FileType, PrefixDir, Path, File, SrcDir, DstDir

    # End of if not os.path.isdir(SrcDir):

    # then that the dest dir is a directory

    if not os.path.isdir(DstDir):

        Errors.append('Usage 12: {0:s} src_dir dst_dir\n\ndst_dir {1:s} Isn\'t a directory\n'.format(sys.argv[0], DstDir))

        logging.info (' Exiting ProcessDirArgs dst dir error\n')

        return FileType, PrefixDir, Path, File, SrcDir, DstDir

    # End of if not os.path.isdir(DstDir):

    # Both are directories so make sure the dest is empty

    if os.listdir(DstDir) != []:

        Errors.append('Error 13: dst dir\n\n{0:s}\n\nmust be empty and it is not\n'.format(str(DstDir)))

        logging.info (' Exiting ProcessDirArgs dst dir not empty error\n')

        return FileType, PrefixDir, Path, File, SrcDir, DstDir

    # End of if os.listdir(DstDir) != []:

    # Now get the last element of the src path to create the fzp and svg
    # directories under the destination directory.

    SplitDir = os.path.split(SrcDir)

    logging.debug  (' ProcessDirArgs: SplitDir %s\n', SplitDir)

    if SplitDir[1] == '' or SplitDir[1] == '.' or SplitDir[1] == '..':

        Errors.append('Error 10: There must be a directory that is not \'.\' or \'..\' in the input name for\na fzp file in order to find the svg files.\n')

        logging.info (' Exiting ProcessDirArgs no prefix dir error\n')

        return FileType, PrefixDir, Path, File, SrcDir, DstDir

    else:
    
        Path = SplitDir[0]
    
        PrefixDir =  SplitDir[1]

        if PrefixDir == None:

            # Insure PrefixDir has a string value for the directory routines. 

            PrefixDir = ""

        # End of if PrefixDir == None:

        DstFzpDir = os.path.join(DstDir,PrefixDir) 

        try:    

            os.makedirs(DstFzpDir)

        except os.error as e:

            Errors.append('Error 14: Creating dir\n\n{0:s} {1:s} \({2:s}\)\n'.format(DstFzpDir), e.strerror, str(e.errno))

            logging.info (' Exiting ProcessDirArgs dir on error %s\n',e.strerror)

            return FileType, PrefixDir, Path, File, SrcDir, DstDir

        # End of try:
    
        logging.debug (' ProcessDirArgs: mkdir %s\n',DstFzpDir)
        
        # The fzp directory was created so create the base svg directory
        
        DstSvgDir = os.path.join(DstDir, 'svg')
    
        try:    
    
            os.makedirs(DstSvgDir)

        except os.error as e:

            Errors.append('Error 14: Creating dir\n\n{0:s} {1:s} \({2:s}\)\n'.format(DstFzpDir), e.strerror, str(e.errno))

            logging.info (' Exiting ProcessDirArgs dir on error %s\n',e.strerror)

            return FileType, PrefixDir, Path, File, SrcDir, DstDir

        # End of try:
    
        logging.debug (' ProcessDirArgs: mkdir %s\n',DstSvgDir)
        
        DstSvgDir = os.path.join(DstSvgDir, PrefixDir)
    
        try:    
        
            os.makedirs(DstSvgDir)

        except os.error as e:

            Errors.append('Error 14: Creating dir\n\n{0:s} {1:s} \({2:s}\)\n'.format(DstFzpDir), e.strerror, str(e.errno))

            logging.info (' Exiting ProcessDirArgs dir on error %s\n',e.strerror)

            return FileType, PrefixDir, Path, File, SrcDir, DstDir

        # End of try:
    
        logging.debug (' ProcessDirArgs: mkdir %s\n', DstSvgDir)
        
        # then the four svg direcotries
        
        SvgDir = os.path.join(DstSvgDir, 'breadboard')
    
        try:    
        
            os.makedirs(SvgDir)

        except os.error as e:

            Errors.append('Error 14: Creating dir\n\n{0:s} {1:s} \({2:s}\)\n'.format(DstFzpDir), e.strerror, str(e.errno))

            logging.info (' Exiting ProcessDirArgs dir on error %s\n',e.strerror)

            return FileType, PrefixDir, Path, File, SrcDir, DstDir

        # End of try:
    
        logging.debug(' ProcessDirArgs: mkdir %s\n', SvgDir)
        
        SvgDir = os.path.join(DstSvgDir, 'icon')
    
        try:    
        
            os.makedirs(SvgDir)

        except os.error as e:

            Errors.append('Error 14: Creating dir\n\n{0:s} {1:s} \({2:s}\)\n'.format(DstFzpDir), e.strerror, str(e.errno))

            logging.info (' Exiting ProcessDirArgs dir on error %s\n',e.strerror)

            return FileType, PrefixDir, Path, File, SrcDir, DstDir

        # End of try:
    
        logging.debug(' ProcessDirArgs: mkdir %s\n', SvgDir)
        
        SvgDir = os.path.join(DstSvgDir, 'pcb')
    
        try:    
        
            os.makedirs(SvgDir)

        except os.error as e:

            Errors.append('Error 14: Creating dir\n\n{0:s} {1:s} \({2:s}\)\n'.format(DstFzpDir), e.strerror, str(e.errno))

            logging.info (' Exiting ProcessDirArgs dir on error %s\n',e.strerror)

            return FileType, PrefixDir, Path, File, SrcDir, DstDir

        # End of try:
    
        logging.debug(' ProcessDirArgs: mkdir %s\n', SvgDir)
        
        SvgDir = os.path.join(DstSvgDir, 'schematic')
    
        try:    
        
            os.makedirs(SvgDir)

        except os.error as e:

            Errors.append('Error, Creating dir {0:s} {1:s} ({2:s})\n'.format(DstFzpDir), e.strerror, str(e.errno))

            logging.info (' Exiting ProcessDirArgs dir on error %s\n',e.strerror)

            return FileType, PrefixDir, Path, File, SrcDir, DstDir

        # End of try:
    
        logging.debug(' ProcessDirArgs: mkdir %s\n', SvgDir)

    # End of if SplitDir[1] == '' or SplitDir[1] == '.' or SplitDir[1] == '..':
        
    # If we get here we have a src and dst directory plus all the required new
    # dst directories so return all that to the calling routine. Set the
    # FileType to 'dir' to indicate success.

    FileType = 'dir'

    logging.debug (' ProcessDirArgs returning FileType %s PrefixDir %s Path %s File %s SrcDir %s DstDir %s\n',FileType, PrefixDir, Path, File, SrcDir, DstDir)

    logging.info (' Exiting ProcessDirArgs\n')

    return FileType, PrefixDir, Path, File, SrcDir, DstDir

# End of def ProcessDirArgs(Argv, Errors):

def PopTag(TagStack, Level):

    # Determine from the current level if the value on the tag stack is still
    # in scope. If it is not, then remove the value from the stack.

    logging.info (' Entering PopTag Level %s\n', Level)

    logging.debug(' PopTag: entry TagStack %s Level %s\n', TagStack, Level)

    Tag, StackLevel = TagStack[len(TagStack) - 1]

    # Because we may have exited several recusion levels before calling this
    # delete all the tags below the current level. 

    while Level != 0 and StackLevel >= Level:

        # Pop the last item from the stack.

        logging.debug(' PopTag: popped Tag %s, StackLevel %s\n', Tag, StackLevel )

        TagStack.pop(len(TagStack) - 1)

        Tag, StackLevel = TagStack[len(TagStack) - 1]

    # End of while Level != 0 and StackLevel >= Level:

    logging.debug(' PopTag: exit TagStack %s Level %s\n', TagStack, Level)

    logging.info (' Exiting PopTag Level %s\n', Level)

# End of def PopTag(Elem, TagStack, Level):

def BackupFilename(InFile, Errors):

    logging.info (' Entering BackupFilename\n')

    # First set the appropriate output file name None for an error condition.

    OutFile = None

    try:

        # Then try and rename the input file to InFile.bak

        os.rename (InFile, InFile + '.bak')

    except os.error as e:

        Errors.append('Error 15: Can not rename\n\n\'{0:s}\'\n\nto\n\n\'{1:s}\'\n\n\'{2:s}\'\n\n{3:s} ({4:s})\n'.format(str(InFile), str(InFile + '.bak'), str( e.filename), e.strerror, str(e.errno)))

        return InFile, OutFile

    # End of try:

    # If we get here, then the file was successfully renamed so change the 
    # filenames and return.

    OutFile = InFile

    InFile = InFile + '.bak'

    return InFile, OutFile

    logging.info (' Exiting BackupFilename\n')

# End of def BackupFilename(InFile, Errors):

def DupNameError(InFile, Id, Elem, Errors):

    logging.info (' Entering DupNameError:\n')

    logging.debug (' DupNameError: Entry InFile %s Id %s Elem %s Errors %s\n', InFile, Id, Elem, Errors)

    # Log duplicate name error 

    Errors.append('Error 16: File\n\'{0:s}\'\nAt line {1:s}\n\nId {2:s} present more than once (and should be unique)\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

    logging.info (' Exiting DupNameError\n')

#End of def DupNameError(InFile, Id, Elem, Errors):

def DupNameWarning(InFile, Id, Elem, Warnings):

    logging.info (' Entering DupNameWarning:\n')

    logging.debug (' DupNameWarning: Entry InFile %s Id %s Elem %s Errors %s\n', InFile, Id, Elem, Warnings)

    # Log duplicate name warning

    Warnings.append('Warning 28: File\n\'{0:s}\'\nAt line {1:s}\n\nname {2:s} present more than once (and should be unique)\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

    logging.info (' Exiting DupNameWarning\n')

#End of def DupNameWarning(InFile, Id, Elem, Warnings):

def ProcessTree(FzpType, InFile, OutFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Debug, Level=0):

    # Potentially recursively process the element nodes of an lxml tree to 
    # aquire the information we need to check file integrity. This routine gets
    # called recursively to process child nodes (other routines get called for
    # leaf node processing). 

    logging.info (' Entering ProcessTree FzpType %s InFile %s Level %s\n', FzpType, InFile, Level)

    logging.debug (' ProcessTree: Source line %s Elem len %s Level %s Elem attributes %s text %s FzpType %s InFile %s OutFile %s CurView %s PrefixDir %s Errors %s Warnings %s Info %s TagStack %s State %s InheritedAttributes %s\n', Elem.sourceline, len(Elem), Level, Elem.attrib, Elem.text, FzpType, InFile, OutFile, CurView, PrefixDir, Errors, Warnings, Info, TagStack, State, InheritedAttributes)


    # Start by checking for non whitespace charactes in tail (which is likely
    # an error) and flag the line if present. 

    Tail = Elem.tail

    logging.debug (' ProcessTree: Tail = \'%s\'\n', Tail)

    if Tail != None and not Tail.isspace(): 

        Warnings.append('Warning 2: File\n\'{0:s}\'\nAt line {1:s}\n\nText \'{2:s}\' isn\'t white space and may cause a problem\n'.format(str(InFile), str(Elem.sourceline), str(Tail)))
        
    # End of if not Elem.tail.isspace(): 

    if len(Elem):

        logging.debug (' ProcessTree: Procees parent node attributes Source line %s len %s Level %s tag %s\n', Elem.sourceline, len(Elem), Level, Elem.tag)

        ProcessLeafNode(FzpType, InFile, OutFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Debug, Level)

        logging.debug (' ProcessTree: Child nodes Source line %s len %s Level %s tag %s\n', Elem.sourceline, len(Elem), Level, Elem.tag)

        # This node has children so recurse down the tree to deal with them.

        for Elem in Elem:

            if len(Elem):

                # this node has children so process them (the attributes of 
                # this node will be processed by the recursion call and the 
                # level will be increased by one.) 

                ProcessTree(FzpType, InFile, OutFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Debug, Level+1)

            else: # This particular element in the for loop is a leaf node.

                # As this is a leaf node proecess it again increasing the 
                # level by 1 before doing the call. 

                ProcessLeafNode(FzpType, InFile, OutFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Debug, Level+1)

            # End of if len(Elem):

        # End of for Elem in Elem:

    else:
    
        # This is a leaf node and thus the level needs to be increased by 1
        # before we process it.  

        ProcessLeafNode(FzpType, InFile, OutFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Debug, Level+1)

    # end of if len(Elem):

    if Level == 0 and 'fzp' in FzpDict and CurView == None:

        # We are at the end of processing the fzp file so check that the 
        # connector numbers are contiguous. 

        FzpCheckConnectors(InFile, Elem, FzpDict, Errors, Warnings, Info, State, Level)    

    # End of if Level == 0 and 'fzp' in FzpDict and CurView == None:

    if Level == 0 and 'fzp' in FzpDict and CurView != None and CurView != 'iconView':

        # If we are finished processing this file, we have an fzp file (because
        # fzp is set)  and it isn't the fzp file (because CurView isn't None), 
        # and isn't the icon svg (which doesn't care about connectors),
        # then check the connectors on this svg file to make sure they are 
        # all present. 

        logging.debug  (' ProcessTree: Checking connectors for %s\n', InFile)

        for Connector in FzpDict['connectors.fzp.' + CurView]:

            # Check that the connector is in the svg and error if not. 

            logging.debug  (' ProcessTree: Checking connector %s\n', Connector)

            if not 'connectors.svg.' + CurView in FzpDict:

                Errors.append('Error 17: File\n\'{0:s}\'\n\nNo connectors found for view {1:s}.\n'.format(str(InFile), str(CurView)))

            elif not Connector in FzpDict['connectors.svg.' + CurView]:

                logging.debug  ('ProcessTree: Connector %s missing\n', Connector)

                Errors.append('Error 18: File\n\'{0:s}\'\n\nConnector {1:s} is in the fzp file but not the svg file. (typo?)\n'.format(str(InFile), str(Connector)))

            # End of if not 'connectors.svg.' + CurView in FzpDict:
                
        # End of `for Connector in FzpDict['connectors.fzp.' + CurView]:

    # End of if Level == 0 and 'fzp' in FzpDict and CurView != None and CurView != 'IconView':

    logging.info (' Exiting ProcessTree Level %s\n', Level)

# End of def ProcessTree(FzpType, InFile, OutFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Debug, Level=0):

def ProcessLeafNode(FzpType, InFile, OutFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Debug, Level):

    logging.info (' Entering ProcessLeafNode FzpType %s Level %s\n', FzpType, Level)

    logging.debug (' ProcessLeafNode: InFile %s CurView %s Errors %s\n', InFile,CurView, Errors)

    # Start by checking for non whitespace charactes in tail (which is likely
    # an error) and flag the line if present. 

    Tail = Elem.tail

    logging.debug (' ProcessLeafNode: Tail = \'%s\'\n', Tail)

    if Tail != None and not Tail.isspace(): 

        Warnings.append('Warning 2: File\n\'{0:s}\'\nAt line {1:s}\n\nText  \'{2:s}\' isn\'t white space and may cause a problem\n'.format(str(InFile), str(Elem.sourceline), str(Tail)))
        
    # End of if not Elem.tail.isspace(): 

    # Select the appropriate leaf node processing routing based on the FzpType
    # variable. 

    if FzpType == 'fzpFritz' or  FzpType == 'fzpPart':

        # If this is a fzp file do the leaf node processing for that. 

        ProcessFzpLeafNode(FzpType, InFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)
        
    elif FzpType == 'svg':

        ProcessSvgLeafNode(FzpType, InFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Level)

    else:

        if not 'SoftwareError' in State:

            # Report the software error once, then set 'SoftwareError' in State
            # to supress more messages and just return. It won't work right 
            # but the problem will at least be reported. 

            Errors.append('Error 19: File\n\'{0:s}\'\n\nFile type {1:s} is an unknown format (software error)\n'.format(str(InFile), str(FzpType)))

            State['SoftwareError'] = 'y'

        # End of if not 'SoftwareError' in State:

    # End of if if FzpType == 'fzpFritz' or  FzpType == 'fzpPart':

    logging.info (' Exiting ProcessLeafNode Level %s\n', Level)

# End of def ProcessLeafNode(FzpType, InFile, OutFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Debug, Level):

def ProcessFzp(FileType, FzpType, InFile, OutFile, CurView, PrefixDir, Errors, Warnings, Info, FzpDict, FilesProcessed, TagStack, State, InheritedAttributes, Debug):

    logging.info (' Entering ProcessFzp FzpType %s FileType %s InFile %s\n', FzpType, FileType, InFile)

    logging.debug ('  ProcessFzp: FzpType %s FileType %s InFile %s OutFile %s CurView %s PrefixDir %s Errors %s Warnings %s Info %s FzpDict %s TagStack %s State %s InheritedAttributes %s Debug %s\n', FzpType, FileType, InFile, OutFile, CurView, PrefixDir, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Debug)

    # Parse the input document.

    Doc, Root = PP.ParseFile (InFile, Errors)

    logging.debug (' ProcessFzp: return from parse Doc %s\n', Doc)

    if Doc != None:

        # We have successfully parsed the input document so process it. Since
        # We don't yet have a CurView, set it to None.

        logging.debug (' ProcessFzp: Calling ProceesTree Doc %s\n', Doc)

        # Set the local output file to a value in case we don't use it but 
        # do test it. 

        FQOutFile = None

        if OutFile == None:

            if Debug == 0:
    
                # No output file indicates we are processing a single fzp file
                # so rename the src file to .bak and use the original src file
                # as the output file (assuming the rename is successfull).
                # Use FQOutFile as the new file name to preserve the value
                # of OutFile for svg processing later. 
    
                InFile, FQOutFile = BackupFilename(InFile, Errors)
    
                logging.debug (' ProcessFzp: After BackupFilename(InFile, Errors) InFile %s FQOutFile %s\n', InFile, FQOutFile)
    
                if FQOutFile == None:
    
                    # An error occurred, so just return to indicate that without
                    # writing the file (as there is no where to write it to).
    
                    logging.info (' ProcessFzp: Exiting ProcessFzp after rename error\n')
    
                    return
    
                # End of if FQOutFile == None:
    
            # End of if Debug == 0:

        else:

            # OutFile wasn't none, so set FQOutFile

            FQOutFile = OutFile

        # End of if OutFile == None:

        # Now that we have an appropriate input file name, process the tree.
        # (we won't get here if there is a file rename error above!)

        logging.debug (' ProcessFzp: before ProcessTree FzpType %s FQOutFile %s\n', FzpType, FQOutFile)

        ProcessTree(FzpType, InFile, FQOutFile, None, PrefixDir, Root, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Debug)

        logging.debug (' ProcessFzp: After ProcessTree FzpType %s FQOutFile %s\n', FzpType, FQOutFile)

        # We have an output file name so write the fzp file to it (or the 
        # console if Debug is > 0.)

        logging.debug (' ProcessFzp: Prettyprint FQOutFile %s FzpType %s\n', FQOutFile, FzpType)

        PP.OutputTree(Doc, Root, FzpType, InFile, FQOutFile, Errors, Warnings, Info, Debug)

        # Then process the associatted svg files from the fzp.

        logging.debug (' ProcessFzp: Calling ProcessSvgsFromFzp FileType %s FzpType %s InFile %s OutFile %s PrefixDir %s Errors %s Warnings %s Info %s FzpDict %s Debug %s\n', FileType, FzpType, InFile, OutFile, PrefixDir, Errors, Warnings, Info, FzpDict, Debug)


        # Use the original value of OutFile to process the svgs. 

        ProcessSvgsFromFzp(FileType, FzpType, InFile, OutFile, PrefixDir, Errors, Warnings, Info, FzpDict, FilesProcessed, Debug)

    # End of if Doc != None:
    
    logging.info (' Exiting ProcessFzp\n')

# End of  ProcessFzp(FileType, FzpType, InFile, OutFile, CurView, PrefixDir, Errors, Warnings, Info, FzpDict, FilesProcessed, TagStack, State, InheritedAttributes, Debug):

def ProcessSvgsFromFzp(FileType, FzpType, InFile, OutFile, PrefixDir, Errors, Warnings, Info, FzpDict, FilesProcessed, Debug):

    # Process the svg files referenced in the FzpDict created from a Fritzing
    # .fzp file.

    logging.info (' Entering ProcessSvgsFromFzp  FileType %s FzpType %s InFile %s\n', FzpType, FileType, InFile)

    logging.debug (' ProcessSvgsFromFzp: OutFile %s PrefixDir %s FzpDict %s\n', OutFile, PrefixDir, FzpDict)

    # First we need to determine the directory structure / filename for the 
    # svg files as there are several to choose from: uncompressed parts which 
    # are all in the same directory but with odd prefixes of 
    # svg.layer.filename or in a Fritzing directory which will be 
    # ../svg/PrefixDir/layername/filename in 4 different directories. In
    # addition we may be processing a single fzp file (in which case the input
    # file needs a '.bak' appended to it), or directory of fzp files in which
    # case the '.bak' isn't needed. We will form appropriate file names from 
    # the InFile, OutFile and PrefixDir arguments to feed to the svg 
    # processing routine. 

    # Insure FQOutFile has a value

    FQOutFile = None

    # Get the path from the input and output files (which will be the fzp file 
    # at this point.) 

    InPath = os.path.dirname(InFile)

    # Record in FilesProcessed that we have processed this file name in case 
    # this is a directory operation. Get just the file name.

    BaseFile = os.path.basename(InFile)

    if 'processed.' + InFile in FilesProcessed:

        # If we have already processed it, flag an error (should not occur).

        logging.debug (' ProcessSvgsFromFzp: InFile %s Error 87 issued\n', InFile)

        Errors.append('Error 87: File\n\'{0:s}\'\n\nFile has already been processed (software error)\n'.format(str(InFile)))

        logging.info (' Exiting ProcessSvgsFromFzp on already processed error\n')

        return
        
    else:

        # Mark that we have processed this file. 

        FilesProcessed['processed.' + InFile] = 'y'

        logging.debug (' ProcessSvgsFromFzp: InFile %s marked as processed\n', InFile)

    # End of if 'processed.' + InFile in FilesProcessed:

    logging.debug (' ProcessSvgsFromFzp: InPath %s InFile %s', InPath, InFile)

    if OutFile == None:

        OutPath = ''

        logging.debug (' ProcessSvgsFromFzp: OutPath %s OutFile %s', OutPath, OutFile)

    else:

        OutPath = os.path.dirname(OutFile)

        logging.debug (' ProcessSvgsFromFzp: OutPath %s OutFile %s', OutPath, OutFile)

    # End of if OutFile == None:

    for CurView in FzpDict['views']:

        logging.debug (' ProcessSvgsFromFzp: Process View %s FzpType %s FzpDict[views] %s\n', CurView, FzpType, FzpDict['views'])

        if CurView == 'iconView':

            # If this is iconview, don't do processing as we aren't going to 
            # check anything and sometimes the breadboard svg is reused which 
            # will cause a warning and replace the .bak file (which is 
            # undesirable)

            logging.debug (' ProcessSvgsFromFzp: Process View %s skipping iconview\n', CurView)

            continue

        # End of if CurView == 'iconview':

        # Extract just the image name as a string from the list entry.

        Image = ''.join(FzpDict[CurView + '.image'])

        logging.debug (' ProcessSvgsFromFzp 1: Image %s FzpType %s OutFile %s\n', Image, FzpType, OutFile)

        # indicate we haven't seen an output file rename error. 

        OutFileError = 'n'

        if FzpType == 'fzpPart':

            # The svg is of the form svg.layer.filename in the directory 
            # pointed to by Path. So append a svg. to the file name and 
            # convert the '/' to a '.' to form the file name for processing. 

            Image = Image.replace(r"/", ".")

            if OutFile == None:

                # Single file processing so set the output filename and use 
                # FQOutFile.bak as the input. Again preserve the original 
                # value of OutFile for processing later svg files. 

                Image = Image.replace(r"/", ".")

                FQOutFile = os.path.join(InPath, 'svg.' + Image)

                # Set the input file from the output file in case debug is non
                # zero and we don't set a backup file. 

                FQInFile = FQOutFile

                if Debug == 0:

                    # If Debug isn't set then rename the input file and
                    # change the input file name. Otherwise leave it alone 
                    # (in this case OutFile is unused and output goes to the
                    # console for debugging.)

                    FQInFile, FQOutFile = BackupFilename(FQInFile, Errors)

                    if FQOutFile == None:

                        # an error occurred renaming the input file so set an
                        # an OutFileError so we don't try and process this 
                        # file as we have no valid output file to write it to. 

                        OutFileError = 'n'

                    # End of if FQOutFile == None:

                    logging.debug (' ProcessSvgsFromFzp 2: FQInFile %s FQOutFile %s OutFileError %s\n', FQInFile, FQOutFile, OutFileError)
                    
                # End of if Debug == 0:

            else:

                # dir to dir processing so set appropriate file names
                # (identical except for path)

                FQInFile = os.path.join(InPath, 'svg.' + Image)

                FQOutFile = os.path.join(OutPath, 'svg.' + Image)

            # End of if OutFile == None:

        elif FzpType == 'fzpFritz':

            # The svg is of the form path../svg/PrefixDir/layername/filename, 
            # so prepend the appropriate path and use that as the file name. 

            # First create the new end path as NewFile 
            # (i.e. '../svg/PrefixDir/Image') once, ready to append as needed.

            NewFile = '..'

            NewFile = os.path.join(NewFile, 'svg')

            logging.debug (' ProcessSvgsFromFzp: after add svg NewFile %s PrefixDir %s\n', NewFile, PrefixDir)

            NewFile = os.path.join(NewFile, PrefixDir)

            logging.debug (' ProcessSvgsFromFzp: after add  PrefixDir NewFile %s\n', NewFile)

            NewFile = os.path.join(NewFile, Image)

            logging.debug (' ProcessSvgsFromFzp: after add  Image NewFile %s\n', NewFile)

            if OutFile == None:

                # add the new end path to the end of the source path

                FQInFile = os.path.join(InPath, NewFile)

                if Debug == 0:

                    # If Debug isn't set then rename the input file and
                    # change the input file name. Otherwise leave it alone 
                    # (in this case OutFile is unused and output goes to the
                    # console for debugging.)

                    FQInFile, FQOutFile = BackupFilename(FQInFile, Errors)

                    logging.debug (' ProcessSvgsFromFzp: after rename FQInfile %s FQOutFile %s\n', FQInFile, FQOutFile)

                    if FQOutFile == None:

                        # an error occurred renaming the input file so set an
                        # an OutFileError so we don't try and process this 
                        # file as we have no valid output file to write it to. 

                        OutFileError = 'y'

                    # End of if FQOutFile == None:

                else:

                    # Insure FQOutFile has a value

                    FQOutFile = None

                # End of if Debug == 0:

            else:

                # dir to dir processing 

                FQInFile = os.path.join(InPath, NewFile)

                FQOutFile = os.path.join(OutPath, NewFile)


            # End of if OutFile == None:

        else:

            # Software error! Shouldn't ever get here.

            Errors.append('Error 19: File\n\'{0:s}\'\n\nFile type {1:s} is an unknown format (software error)\n'.format(str(InFile), str(FzpType)))

        # End of if FzpType == 'fzpPart':

        logging.debug (' ProcessSvgsFromFzp: FzpType %s Process %s to %s\n', FzpType, FQInFile, FQOutFile)

        if not os.path.isfile(FQInFile):

            # The file doesn't exist so flag an error,

            Errors.append('Error 20: File\n\'{0:s}\'\n\nDuring processing svgs from fzp, svg file doesn\'t exist\n'.format(str(FQInFile)))

        else:

            # Check for identical case in the filename (Windows doesn't care
            # but Linux and probably MacOS do)

            TmpPath = os.path.dirname(FQInFile)

            TmpFile = os.path.basename(FQInFile)

            # get the path from the input file

            logging.debug(' ProcessSvgsFromFzp: TmpPath %s TmpFile %s\n', TmpPath, TmpFile)

            if TmpPath == '':

                # Change an empty path to current directory to prevent os error

                TmpPath = './'

            # End of if TmpPath == '':

            if not TmpFile in os.listdir(TmpPath):

                logging.debug(' ProcessSvgsFromFzp: dir names %s\n', os.listdir(TmpPath))

                # File system case mismatch error. 

                logging.debug(' ProcessSvgsFromFzp: InFile %s OutFile %s FzpType %s \n', InFile, OutFile, FzpType)

                if OutFile == None or FzpType == 'dir':

                    # Then InFile is the fzp file.

                    Errors.append('Error 21: Svg file\n\n\'{0:s}\'\n\nHas a different case in the file system than in the fzp file\n\n\'{1:s}\'\n'.format(str(FQInFile), str(InFile)))

                else:

                    # Then OutFile is the fzp file (InFile will have .bak 
                    # appended which we don't want.)

                    Errors.append('Error 21: Svg file\n\n\'{0:s}\'\n\nHas a different case in the file system than in the fzp file\n\n\'{1:s}\'\n'.format(str(FQInFile), str(OutFile)))

                # End of if OutFile == None or FzpType == 'dir':

            # End of if not TmpFile in os.listdir(TmpPath):

            # Mark that we have processed this file in case this is directory
            # processing of part.files to avoid double processing the svg files.

            if 'processed.' + FQInFile in FilesProcessed:

                # Already seen, may occur if svgs are shared, so warn as the
                # .bak file will be overwritten and the user needs to know that 

                logging.debug(' ProcessSvgsFromFzp: FQInFile %s Warning 29 issued. FilesProcessed %s\n', FQInFile, FilesProcessed)

                Warnings.append('Warning 29: File\n\'{0:s}\'\n\nProcessing view {1:s}, File {2:s}\nhas already been processed\nbut will be processed again as part of this fzp file in case of new warnings.\n'.format(str(InFile), str(CurView), str(FQInFile)))

            else:

                logging.debug(' ProcessSvgsFromFzp: FQInFile %s marked as processed.\n', FQInFile)

                FilesProcessed['processed.' + FQInFile] = 'y'

            # End of if 'processed.' + FQInFile in FilesProcessed:

            if OutFileError == 'n':

                # If the file exists and there was not a file rename error then
                # go and try and process the svg (set the FzpType explicitly 
                # to svg), but first reset the state variables for the new 
                # file (but not Errors, Warnings, FzpDict or CurView).

                TagStack, State, InheritedAttributes = InitializeState()

                ProcessSvg('svg', FQInFile, FQOutFile, CurView, PrefixDir,  Errors, Warnings, Info, FzpDict, FilesProcessed, TagStack, State, InheritedAttributes, Debug)

                if CurView == 'schematicView' and 'subparts' in FzpDict:

                    # We have subparts, so now having processed the entire svg
                    # make sure we have found all the connectors we should have.

                    logging.debug(' ProcessSvgsFromFzp: Subpart start FzpDict[\'subparts\'] %s\n',FzpDict['subparts'])

                    for SubPart in FzpDict['subparts']:

                        # Get the list of subparts from the fzp.

                        logging.debug(' ProcessSvgsFromFzp: Subpart before loop SubPart=%s\nFzpDict[SubPart + \'.subpart.cons\']=%s\nFzpDict[SubPart + \'.svg.subparts\']=%s\n',SubPart, FzpDict[SubPart + '.subpart.cons'], FzpDict[SubPart + '.svg.subparts'])

                        for SubpartConnector in FzpDict[SubPart + '.subpart.cons']:

                            logging.debug(' ProcessSvgsFromFzp: SubpartConnector %s\n',SubpartConnector)

                            if not SubPart + '.svg.subparts' in FzpDict:

                                # No connectors in svg error. 

                                logging.debug(' ProcessSvgsFromFzp: no connectors in svg, SubpartConnector %s\n',SubPartConnector, SubPart)

                                Errors.append('Error 78: Svg file\n\n\'{0:s}\'\n\nWhile looking for {1:s}, Subpart {2:s} has no connectors in the svg\n'.format(str(FQInFile), str(OutFile), str(SubpartConnector), str(SubPart)))

                            elif not SubpartConnector in FzpDict[SubPart + '.svg.subparts']:

                                # Throw an error if one of the connectors we 
                                # should have isn't in the svg. 

                                Errors.append('Error 79: Svg file\n\n\'{0:s}\'\n\nSubpart {1:s} is missing connector {2:s} in the svg\n'.format(str(FQInFile), str(SubPart), str(SubpartConnector)))

                                logging.debug(' ProcessSvgsFromFzp: x6 no connector %s in svg, SubpartConnector %s\n',SubpartConnector, SubPart)

                            # if not SubPart + '.svg.subparts' in FzpDict:

                        # End of for SubpartConnector in FzpDict[SubPart + '.subpart.cons']:

                    # End of for SubPart in FzpDict['subparts']:

                # End of if CurView == 'schematicView' and 'subparts' in FzpDict:

            # End of if OutFileError == 'n':

        # End of if not os.path.isfile(FQInFile):

    # End of for CurView in FzpDict['views']:

    logging.info (' Exiting ProcessSvgsFromFzp\n')

# End of def ProcessSvgsFromFzp(FileType, FzpType, InFile, OutFile, PrefixDir, Errors, Warnings, Info, FzpDict, Debug):

def ProcessFzpLeafNode(FzpType, InFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    # We are processing an fzp file so do the appropiate things for that. 

    logging.info (' Entering ProcessFzpLeafNode FzpType %s Infile %s Level %s\n', FzpType, InFile, Level)

    # Regex to detect comment lines (ignoring case)

    CommentRegex = re.compile(r'^<cyfunction Comment at',re.IGNORECASE)

    # Mark in the dictionary that we have processed the fzp file so when we 
    # process an associated svg we know if the fzp data is present in the dict.

    if not 'fzp' in FzpDict:

        # not here yet so set it. 

        FzpDict['fzp'] = 'y'

    # End of if not 'fzp' in FzpDict:

    # Then check for any of Fritzing's tags.

    FzpTags(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, Level)

    StackTag, StackLevel = TagStack[len(TagStack) - 1]
 
    logging.debug (' ProcessFzpLeafNode StackTag %s StackLevel %s\n', StackTag, StackLevel)

    if len(TagStack) == 2 and StackTag == 'module':

        Tag = Elem.tag

        logging.debug (' ProcessFzpLeafNode Tag %s\n', Tag)

        if CommentRegex.match(str(Tag)):

            # Ignore comment lines so as to not complain about lack of tags.

            logging.debug (' ProcessFzpLeafNode Comment ignored\n ')

            return

        # End of if CommentRegex.match(str(Tag)):
 
        logging.debug (' ProcessFzpLeafNode moduleid TagStack %s len %s',TagStack, len(TagStack))

        # If the tag stack is only 'module' check for a moduleid if this
        # is a dup that will be caught in FzpmoduleId via the dictionary.

        FzpmoduleId(FzpType, InFile, Elem, Errors, Warnings, Info, FzpDict, State, Level)
   
        # Set where we are and what we expect to see next.
 
        State['lasttag'] = 'module'

        State['nexttag'] = 'views'

    elif len(TagStack) == 2:

        Errors.append('Error 22: File\n\'{0:s}\'\n\nAt line {1:s}\n\nNo ModuleId found in fzp file\n'.format(str(InFile), str(Elem.sourceline)))

    # End of if len(TagStack) == 2 and StackTag == 'module':

    # If TagStack is 3 or more and is 'module', 'views' (i.e. TagStack[2] is
    # 'views', so first get TagStack[2] in to BaseTag.)

    if len(TagStack) > 2:

        BaseTag, StackLevel = TagStack[2]

    else:

        # We aren't yet that far in the file so set BaseTag to ''

        BaseTag = ''

    # End of If len TagStack > 2:
 
    logging.debug (' ProcessFzpLeafNode moduleid BaseTag %s len %s', BaseTag, len(TagStack))

    if len(TagStack) > 2 and BaseTag == 'views':

        logging.debug (' ProcessFzpLeafNode: start processing views\n')

        # As long as we haven't cycled to 'connectors' as the primary tag,
        # keep processing views tags.
   
        if not 'views' in FzpDict:

            # If we don't have a views yet create an empty one. 

            logging.debug (' ProcessFzpLeafNode: create \'views\' in dictionary\n')

            FzpDict['views'] = []

        # End of if not 'views' in FzpDict:

        if State['lasttag'] == 'module':

            # Note that we have seen the 'views' tag now. 

            State['lasttag'] = 'views'

            # notw we are looking for a viewname next.

            State['nexttag'] = 'viewname'

        # End of if State['lasttag'] == 'module':

        # We are currently looking for file and layer names so do that. 

        if len(TagStack) > 3:

            # We have already dealt with the TagStack 3 ('views') case above 
            # so only call FzpProcessViewsTs3 for 4 or higher 
            # (viewname, layers and layer). 

            FzpProcessViewsTs3(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

        # End of len(TagStack) > 3:

    # End of if len(TagStack) > 2 and BaseTag == 'views':

    # Again BaseTag is TagStack[2] (the current tag may be different.)

    if len(TagStack) == 3 and BaseTag == 'connectors':

        # process the connectors

        logging.debug (' ProcessFzpLeafNode: Start of processing connectors\n')

        # By the time we get here we should have all the views present so check
        # and make sure we have at least one view and warn about any that are
        # missing or have unexpected names (no views is an error!). 

        if not 'FzpCheckViews' in State:

            logging.debug (' ProcessFzpLeafNode: Set State[\'FzpCheckViews\'] = [] and call FzpCheckViews State %s line %s\n', State, Elem.sourceline)

            # Indicate we have executed the check so it is only done once.

            State['FzpCheckViews'] = []

            FzpCheckViews(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

        # End of if not FzpCheckViews in State:

        # Set the appropriate states for connectors.

        State['lasttag'] = 'connectors'

        State['nexttag'] = 'connector'

    # End of if len(TagStack) == 3 and BaseTag == 'connectors':

    # Again BaseTag is TagStack[2] (the current tag may be different.)

    if len(TagStack) > 3 and  BaseTag == 'connectors':

        logging.debug (' ProcessFzpLeafNode: continue processing connectors\n')

        # We have dealt with TagStack = 3 'connectors' above so only do 
        # 4 and higher by calling FzpProcessConnectorsTs3.

        FzpProcessConnectorsTs3(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

    # End of if len(TagStack) > 3 and  BaseTag == 'connectors':

    # If TagStack is 3 and is 'module', 'buses' 

    # Again BaseTag is TagStack[2] (the current tag may be different.)

    if len(TagStack) == 3 and BaseTag == 'buses':

        logging.debug (' ProcessFzpLeafNode: start processing buses\n')

        # Since some parts have an empty bus tag at the end of the fzp
        # don't check the previous state (but do set the new state in case
        # this really is a bus definition.)

        State['lasttag'] = 'buses'

        State['nexttag'] = 'bus'

        if not 'buses' in FzpDict:

            # If we don't have a buses yet create an empty one. 

            logging.debug (' ProcessFzpLeafNode: create \'buses\' in dictionary\n')

            FzpDict['buses'] = []

        # End of if not 'buses' in FzpDict:

        logging.debug (' ProcessFzpLeafNode: TagStack len %s\n', len(TagStack))

    # End of if len(TagStack) == 3 and BaseTag == 'buses':

    # Again BaseTag is TagStack[2] (the current tag may be different.)

    if len(TagStack) > 3 and  BaseTag == 'buses':

        logging.debug (' ProcessFzpLeafNode: continue processing buses\n')

        # Go and process the bus tags

        FzpProcessBusTs3(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

    # End of if len(TagStack) > 3 and  BaseTag == 'buses':

    logging.debug (' ProcessFzpLeafNode: before subparts processing TagStack len %s TagStack %s\n', len(TagStack), TagStack)

    # Again BaseTag is TagStack[2] (the current tag may be different.)

    if len(TagStack) == 3 and BaseTag == 'schematic-subparts':

        logging.debug (' ProcessFzpLeafNode: start sub parts processing\n')

        if 'buses' in FzpDict:

            # A bus has already been defined and won't allow schematic parts.

            logging.debug (' ProcessFzpLeafNode: subparts but bus defined\n')

            if 'bus_defined' in FzpDict:

                if 'bus_defined' == 'n':

                    Errors.append('Error 23: File\n\'{0:s}\'\nAt line {1:s}\n\nA bus is already defined, schematic parts won\'t work with busses\n'.format(str(InFile), str(Elem.sourceline)))

                    # Mark that we have flagged the error so we don't repeat it.

                    FzpDict['bus_defined'] = 'y'

                # End of if 'bus_defined' == 'n':

            # End of if 'bus_defined' in FzpDict:
    
        else:
    
            if not 'schematic-subparts' in FzpDict:
    
                # If we don't have a schematic-subparts yet create an empty one. 
                logging.debug (' ProcessFzpLeafNode: create \'schematic-subparts\' in dictionary\n')
    
                FzpDict['schematic-subparts'] = []
    
            # End of if not 'schematic-subparts' in FzpDict:

        # End of if 'buses' in FzpDict:

        # Set State for where we are and what we expect next.

        State['lasttag'] = 'schematic-subparts'

        State['nexttag'] = 'subpart'

    # End of if len(TagStack) == 3 and BaseTag == 'schematic-subparts':

    # Again BaseTag is TagStack[2] (the current tag may be different.)

    if len(TagStack) > 3 and  BaseTag == 'schematic-subparts':

        logging.debug (' ProcessFzpLeafNode: continue sub parts Tag > 2 TagStack %s\n',TagStack)

        # Process the schematic-subparts section of the fzp.

        if not 'bus_defined' in FzpDict:

            # But only if there isn't a bus already defined.
    
            FzpProcessSchematicPartsTs3(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

        # End of if not 'bus_defined' in FzpDict:

    # End of if len(TagStack) > 3 and  BaseTag == 'schematic-subparts':
    
    logging.debug (' Exiting ProcessFzpLeafNode Level %s State %s line %s\n', Level, State, Elem.sourceline)

    logging.info (' Exiting ProcessFzpLeafNode Level %s\n', Level)

# End of def ProcessFzpLeafNode(FzpType, InFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpTags(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, Level):

    # Looks for and log any of the Fritzing tags. We will check the dictionary
    # to make sure the appropriate tag has been seen when processing layer and
    # pin information later. 

    logging.info (' Entering FzpTags Level %s\n', Level)

    Tag = Elem.tag

    if Tag != None:

        # If we have a tag go and adjust the tag stack if needed. 

        PopTag(TagStack, Level)

    # End of if Tag != None:

    logging.debug (' FzpTags: Tag: %s attributes:%s TagStack %s\n',Elem.tag, Elem.attrib, TagStack)

    # Check the single per file tags (more than one is an error)

    if Tag in ['module', 'version', 'author', 'title', 'label', 'date', 'tags', 'properties', 'taxonomy', 'url', 'schematic-subparts', 'buses']:

        logging.debug (' FzpTags: Source line %s Level %s tag %s\n', Elem.sourceline, Level, Tag)

        # Record the tag in the dictionary (and check for more than one!)

        if Tag in FzpDict:

            logging.debug (' FzpTags: Dup Source line %s Level %s tag %s\n', Elem.sourceline, Level, Tag)

            # If its already been seen flag an errror.

            Errors.append('Error 24: File\n\'{0:s}\'\nAt line {1:s}\n\nMore than one copy of Tag {2:s}\n'.format(str(InFile), str(Elem.sourceline), str( Tag)))
        
        # End of if Tag in FzpDict:
        
        FzpDict[Tag] = [Tag]

    # End of if Tag in ['module', 'version', 'author', 'title', 'label', 'date', 'tags', 'properties', 'taxonomy', 'url', 'schematic-subparts', 'buses']:

    # For the repeating tags: views, iconView, layers, breadboardView,
    # schematicView, pcbView, connector, subpart, bus and the non repeating 
    # tags connectors, schematic-subparts, buses stick them in a stack
    # so we know where we are when we come across an attribute.

    if Tag in ['module', 'version', 'author', 'title', 'label', 'date', 'tags', 'tag', 'properties', 'property', 'spice', 'taxonomy', 'description', 'url', 'line', 'model', 'views', 'iconView', 'layers', 'layer', 'breadboardView', 'schematicView', 'pcbView', 'connectors', 'connector', 'p', 'buses', 'bus', 'nodeMember', 'schematic-subparts', 'subpart']:

        # Push the Id and Level on to the tag stack.

        TagStack.append([Tag, Level])

        logging.debug (' FzpTags: End, found tag, source line %s Tag %s Level %s TagStack %s TagStack len %s\n', Elem.sourceline, Tag, Level, TagStack, len(TagStack))

    else:
        
        logging.debug (' FzpTags: End didn\'t find tag, source line %s Tag %s Level %s TagStack %s TagStack len %s\n', Elem.sourceline, Tag, Level, TagStack, len(TagStack))

    # End of if Tag in ['module', 'version', 'author', 'title', 'label', 'date', 'tags', 'tag', 'properties', 'property', 'spice', 'taxonomy', 'description', 'url', 'line', 'model', 'views', 'iconView', 'layers', 'layer', 'breadboardView', 'schematicView', 'pcbView', 'connectors', 'connector', 'p', 'buses', 'bus', 'nodeMember', 'schematic-subparts', 'subpart']:

    logging.info (' Exiting FzpTags Level %s\n', Level)

# End of def FzpTags(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, Level):

def FzpmoduleId(FzpType, InFile, Elem, Errors, Warnings, Info, FzpDict, State, Level):

    logging.info (' Entering FzpmoduleId Level %s\n', Level)

    LeadingPartRegex = re.compile(r'^part\.', re.IGNORECASE)

    TrailingFzpRegex = re.compile(r'\.fzp$', re.IGNORECASE)

    # Check to see if we have a moduleId and flag an error if not, because 
    # one is required. 
    
    ModuleId =  Elem.get('moduleId')

    logging.debug(' FzpmoduleId: ModuleId %s\n',ModuleId)

    # Make a local copy of the base file name (without its path if any)
    # as we may make changes to it that we don't want to propigate. 

    File = os.path.basename(InFile)

    # Remove the trailing .bak if it is present.

    File = re.sub(r'\.bak$','', File)

    if ModuleId == None:

        if not 'moduleId' in FzpDict:

            Errors.append('Error 22: File\n\'{0:s}\'\n\nAt line {1:s}\n\nNo ModuleId found in fzp file\n'.format(str(InFile), str(Elem.sourceline)))

        # End of if not 'moduleId' in FzpDict:

        logging.debug(' FzpmoduleId: no moduleId\n')

    else:
            
        # We have found a moduleId so process it. Check that it matches the 
        # input filename without the fzp, and there is only one of them. Look 
        # for (and warn if absent) a referenceFile and fritzingVersion as well.

        # Check if this is a breadboard file and mark that in State if so.

        if File in ['breadboard.fzp', 'breadboard2.fzp']:

            State['breadboardfzp'] = 'y'

        # End of if File in ['breadboard.fzp', 'breadboard2.fzp']:

        logging.debug(' FzpmoduleId: FzpType %s InFile %s File %s\n', FzpType, InFile,  File)

        if FzpType == 'fzpPart':

            # This is a part. type file so remove the "part." from the
            # file name before the compare.

            File = LeadingPartRegex.sub('', File)

            logging.debug(' FzpmoduleId: removed part. to leave %s\n', File)

        # End of if FzpType == 'fzpPart':

        # Then remove the trailing ".fzp"

        File = TrailingFzpRegex.sub('', File)

        logging.debug(' FzpmoduleId: removed .fzp to leave %s\n', File)

        if File != ModuleId:

            Warnings.append('Warning 3: File\n\'{0:s}\'\nAt line {1:s}\n\nModuleId \'{2:s}\'\n\nDoesn\'t match filename\n\n\'{3:s}\'\n'.format(str(InFile), str(Elem.sourceline), str(ModuleId), str(File)))
            
        # End of if File != ModuleId:
    
        if 'moduleId' in FzpDict:
        
            Errors.append('Error 25: File\n\'{0:s}\'\nAt line {1:s}\n\nMultiple ModuleIds found in fzp file\n'.format(str(InFile), str(Elem.sourceline)))

            FzpDict['moduleId'].append(ModuleId)

        else:

            # Otherwise create a new key with the value as a single element
            # list (so we can append if we find another.)

            FzpDict['moduleId'] = [ModuleId]

            logging.debug(' FzpmoduleId: Added ModuleId %s to FzpDict\n', ModuleId)

        # End of if 'ModuleId' in FzpDict:

    # End of if ModuleId == None:

    # Now look for a reference file.

    RefFile =  Elem.get('referenceFile')

    logging.debug(' FzpmoduleId: ReFile %s File %s\n', RefFile, File)
    
    if RefFile == None:

        Warnings.append('Warning 4: File\n\'{0:s}\'\nAt line {1:s}\n\nNo referenceFile found in fzp file\n'.format(str(InFile), str(Elem.sourceline)))

    else:

        if 'referenceFile' in FzpDict:

            Warnings.append('Warning 5: File\n\'{0:s}\'\nAt line {1:s}\n\nMultiple referenceFile found in fzp file\n'.format(str(InFile), str(Elem.sourceline)))

            FzpDict['referenceFile'].append(RefFile)

        else:

            # Otherwise create a new key with the value as a single element
            # list (so we can append if we find another.)

            FzpDict['referenceFile'] = [RefFile]

        # End of if 'referenceFile' in FzpDict:

        if RefFile != File + '.fzp':

            # The reference file doesn't match the input file name which it 
            # should.

            Warnings.append('Warning 6: File\n\'{0:s}\'\nAt line {1:s}\n\nReferenceFile name \n\n\'{2:s}\'\n\nDoesn\'t match fzp filename\n\n\'{3:s}\'\n'.format(str(InFile), str(Elem.sourceline), str(RefFile), str(File + '.fzp')))

        # End of if RefFile != File + '.fzp':

    # End of if RefFile == None:

    # Then check for a Fritzing version

    Version =  Elem.get('fritzingVersion')

    if Version == None:

            Warnings.append('Warning 7: File\n\'{0:s}\'\nAt line {1:s}\n\nNo Fritzing version in fzp file\n'.format(str(InFile), str(Elem.sourceline)))

    else:

        # There is a Fritzing version so record it.
            
        if 'fritzingVersion' in FzpDict:
        
            Warnings.append('Warning 8: File\n\'{0:s}\'\nAt line {1:s}\n\nMultiple fritzingVersion found in fzp file\n'.format(str(InFile), str(Elem.sourceline)))

            FzpDict['fritzingVersion'].append(Version)

        else:

            # Otherwise create a new key with the value as a single element
            # list (so we can append if we find another.)

            FzpDict['fritzingVersion'] = [Version]

        # End of if 'fritzingVersion' in FzpDict:

    # End of if Version == None:

    logging.info (' Exiting moduleId found moduleId\n')

# End of def FzpmoduleId(FzpType, InFile, Elem, Errors, Warnings, Info, FzpDict, State, Level):

def FzpProcessViewsTs3(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    # We are in the views grouping so find and record our groupnames, layerIds
    # and filenames in the input stream. 

    logging.info (' Entering FzpProcessViewsTs3 Level %s source line %s\n', Level, Elem.sourceline)

    StackTag, StackLevel = TagStack[len(TagStack) - 1]

    logging.debug (' FzpProcessViewsTs3: StackTag %s State %s TagStack %s attributes %s\n', StackTag, State, TagStack, Elem.attrib)

    # TagStack length of 3 ('empty', 'module', 'views') is what tripped the 
    # call to this routine so we start processing at TagStack length 4 in 
    # this large case statement which trips when it finds the correct state 
    # (or complains if it finds an incorrect state due to errrorS.)

    if len(TagStack) == 4:

        # TagStack should be 'module', 'views', view name so check and process
        # the view name. Check that State['nexttag'] is 'viewname' or 'layer'
        # (the end of a previous entry) to indicate that is what we are 
        # expecting at this time. 

        if State['nexttag'] != 'viewname' and State['nexttag'] != 'layer':

            Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected tag {2:s} not a view name\n'.format(str(InFile), str(Elem.sourceline), str(State['nexttag'])))
            
        # End of if State['nexttag'] != 'viewname' and State['nexttag'] != 'layer':

        # Get the latest tag value from StackTag in to View

        View = StackTag

        if View == 'layers':

            # If it is 'layers' (indicating we don't have a valid view),  
            # set View to none so it has a value (even though its wrong) and 
            # the state is unrecoverable. So as we have noted the error just 
            # proceed although it will likely cause an error cascade. 

            View = 'none'

            logging.debug (' FzpProcessViewsTs3: missing view, View set to none\n', View)

            Errors.append('Error 27: File\n\'{0:s}\'\nAt line {1:s}\n\nView name missing\n'.format(str(InFile), str(Elem.sourceline)))

        # End of if View == 'layers':
            
        if View in ['iconView', 'breadboardView', 'schematicView', 'pcbView']:

            # View value is legal so process it. 

            if not 'views' in FzpDict:

                # views doesn't exist yet so create it and add this view.

                FzpDict['views'] = [View]

                logging.debug (' FzpProcessViewsTs3: Created dict entry views and added  %s\n', View)

            else:

                if View in FzpDict['views']:

                    # Error, already seen.

                    Errors.append('Error 28: File\n\'{0:s}\'\nAt line {1:s}\n\nMultiple view tags {2:s} present, ignored\n'.format(str(InFile), str(Elem.sourceline), str(View)))

                    logging.debug (' FzpProcessViewsTs3: error view %s already present\n', View)

                else: 

                    # Add this view to the list. 
                    
                    FzpDict['views'].append(View)

                    logging.debug (' FzpProcessViewsTs3: appended View %s to dict entry views\n', View)

                # End of if View in FzpDict['views']:

            # End of if not 'views' in FzpDict:

        else:

            Errors.append('Error 29: File\n\'{0:s}\'\nAt line {1:s}\n\nView tag {2:s} not recognized (typo?)\n'.format(str(InFile), str(Elem.sourceline), str(View)))

            logging.debug (' FzpProcessViewsTs3: error View %s not recognized\n', View)

        # End of if View in ['iconView', 'breadboardView', 'schematicView', 'pcbView']:

        # Now set State['lastvalue'] to View to keep state for the next entry 

        State['lastvalue'] = View

        # Set State['nexttag'] to the next tag we expect to see for the next entry

        State['nexttag'] = 'layers'

        logging.debug (' FzpProcessViewsTs3: Set State[\'views\'] to %s and State[\'tag\'] to %s\n', State['lastvalue'], State['nexttag'])

    elif len(TagStack) == 5 and StackTag == 'layers':

        if State['nexttag'] != 'layers':

            # note an internal state error.

            Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nNState error, nexttag {2:s} not \'layers\'\n'.format(str(InFile), str(Elem.sourceline), str(State['nexttag'])))
           
        # End of if State['nexttag'] != 'layers': 
        
        # Get the current tag value from the state variable set on a previous 
        # call to this routine. 

        View = State['lastvalue'] 

        # We should have an image file here so try and get it. 
        
        Image = Elem.get('image')

        if Image == None:

            # We didn't find an image, so set it to 'none' so it has a value
            # even if it is bogus. 

            Image = 'none'

            Errors.append('Error 30: File\n\'{0:s}\'\nAt line {1:s}\n\nNo image name present\n'.format(str(InFile), str(Elem.sourceline)))

        # End of if Image == None:
        
        # We have found an image attribute so put it in the dictonary 
        # indexed by viewname aquired above.

        if (View + '.image') in FzpDict:

            # too many input files!

            Errors.append('Error 31: File\n\'{0:s}\'\nAt line {1:s}\n\nMultiple {2:s} image files present\n'.format(str(InFile), str(Elem.sourceline), str(View)))

            FzpDict[View + '.image'].append(Image)
    
            logging.debug (' FzpProcessViewsTs3: error multiple image files added %s\n', Image)

        else:

            # Put it in a list in case we find another (which is an error!)

            FzpDict[View + '.image'] = [Image]

            logging.debug (' FzpProcessViewsTs3: added image file %s\n', Image)

        # End if (View + 'image') in FzpDict:

        # Then set State['lastvalue'] to the image to capture the layerids that 
        # should follow this image file.

        State['image'] = Image

        # then set the next expected tag to be 'layer' for the layerId.

        State['nexttag'] = 'layer'

    elif len(TagStack) == 6 and StackTag == 'layer':

        if State['nexttag'] != 'layer':

            # note an internal state error.

            Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, nexttag {2:s} not \'layer\'\n'.format(str(InFile), str(Elem.sourceline), str(State['nexttag'])))
           
        # End of if State['nexttag'] != 'layers': 
        
        # set the current view from State['lastvalue'] and the current image 
        # path/filename value from State['image'] for dict keys. The values 
        # are those saved the last time we were in this routine). 

        View = State['lastvalue']

        Image = State['image']

        # Now do the same for a layerId if it is here (there may be multiple
        # layerIds for a single view so use a list).

        LayerId = Elem.get('layerId')

        if LayerId == None:

            # There isn't a layer id so set it to none so it has a value even
            # if it is bogus. 

            LayerId = 'none'

            Errors.append('Error 32: File\n\'{0:s}\'\nAt line {1:s}\n\nNo layerId value present\n'.format(str(InFile), str(Elem.sourceline)))

        # End of if LayerId == None:

        # Set the index value to View.LayerId

        Index = View + '.' + 'LayerId'

        # For all except pcb view there should only be one LayerId

        if View != 'pcbView':

            if Index in FzpDict:

                Errors.append('Error 33: File\n\'{0:s}\'\nAt line {1:s}\n\nView {2:s} already has layerId {3:s}, {4:s} ignored\n'.format(str(InFile), str(Elem.sourceline),str(View), str(FzpDict[Index]), str(LayerId)))

            else:

                FzpDict[Index] = LayerId

            # End of if Index in FzpDict:

        else:

            # This is pcb view so there may be multiple layerIds but they must
            # be unique.

            if not Index in FzpDict:

                # this is the first and possibly only layerId so create it. 

                FzpDict[Index] = [LayerId]

                logging.debug (' FzpProcessViewsTs3: created LayerId %s\n', LayerId)

            elif LayerId in FzpDict[Index]:

                # must be unique and isn't.

                Errors.append('Error 33: File\n{0:s}\nAt line {1:s}\n\nView {2:s} already has layerId {3:s}, ignored\n'.format(str(InFile), str(Elem.sourceline),str(View), str(FzpDict[Index]), str(LayerId)))

            else:

                # if this is a second or later layerId append it

                FzpDict[Index].append(LayerId)

                logging.debug (' FzpProcessViewsTs3: appended LayerId %s\n', LayerId)

            # End of if not Index in FzpDict:

        # End of if View != 'pcbView':

        # if the view is pcbview and the layer is copper0 or copper1 note 
        # the layers presense to decide if this is a through hole or smd part
        # later (if there is only copper1 layer it is smd if both are present
        # it is through hole only copper0 is an error.

        logging.debug (' FzpProcessViewsTs3: View %s LayerId %s\n', View, LayerId)

        if View == 'pcbView' and LayerId in ['copper0', 'copper1']:

            # mark this layer id as present

            FzpDict[LayerId + '.layerid'] = 'y'

            # and save its source line number for error messages later.

            FzpDict[LayerId + '.lineno'] = Elem.sourceline

        # End of if View == 'pcbview' and LayerId in ['copper0', 'copper1']:

        # State is fine as is, no need for updates here. 

    else:

        # Input state incorrect so set an error.

        Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected tag {2:s} got tag {3:s}\n'.format(str(InFile), str(Elem.sourceline), str(State['nexttag']), str(StackTag)))
            
        # then set the next expected tag to be 'layer' for the layerId.

        State['nexttag'] = 'layer'

        logging.debug (' FzpProcessViewsTs3: unknown state combination expected %s got %s\n', State['nexttag'], StackTag)

    # End of if len(TagStack) == 4:

    logging.debug (' FzpProcessViewsTs3: FzpDict: %s\n', FzpDict)

    logging.info (' Exiting FzpProcessViewsTs3 Level %s\n', Level)

# End of def FzpProcessViewsTs3(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpCheckViews(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpCheckViews Level %s\n', Level)

    logging.debug (' FzpCheckViews: State: %s\n', State)

    # note no valid views seen yet

    ViewsSeen = 0

    if not 'views' in FzpDict:

        Errors.append('Error 34: File\n\'{0:s}\'\n\nNo views found.\n'.format(str(InFile)))
       
    else:

        # Check for unexpected View names

    
        for View in FzpDict['views']:

            if View not in ['iconView', 'breadboardView', 'schematicView', 'pcbView']:

                Errors.append('Error 35: File\n\'{0:s}\'\n\nUnknown view {1:s} found. (Typo?)\n'.format(str(InFile), str(View)))

            else:

                # Note we have seen a valid view.

                ViewsSeen += 1

            # End of if View not in ['iconView', 'breadboardView', 'schematicView', 'pcbView']

        # End of for View in FzpDict['views']:

    # End of if not 'views' in FzpDict:

    # Now make sure we have at least one view and warn if we don't have all 4.

    if ViewsSeen == 0:

            Errors.append('Error 36: File\n\'{0:s}\'\n\nNo valid views found.\n'.format(str(InFile)))

    elif ViewsSeen < 4:

            Warnings.append('Warning 9: File\n\'{0:s}\'\n\nOne or more expected views missing (may be intended)\n'.format(str(InFile)))
         
    # End of if ViewsSeen == 0:

    # Now check for copper0 and copper1 layers. Only copper1 indicates 
    # an smd part, both copper0 and copper1 indicates a through hole part
    # and only copper0 is an error. No copper or State['hybridsetforpcbView'] 
    # indicates no pcb view.

    if 'hybridsetforpcbView' in State:

        # There is no pcb view.

        Info.append('File\n\'{0:s}\'\n\nThere is no PCB view for this part.\n')

    elif 'copper0.layerid' in FzpDict and 'copper1.layerid' in FzpDict:

        Info.append('File\n\'{0:s}\'\n\nThis is a through hole part as both copper0 and copper1 views are present.\nIf you wanted a smd part remove the copper0 definition from line {1:s}\n'.format(str(InFile), str(FzpDict['copper0.lineno'])))

    elif not 'copper0.layerid' in FzpDict and 'copper1.layerid' in FzpDict:

        Info.append('File\n\'{0:s}\'\n\nThis is a smd part as only the copper1 view is present.\nIf you wanted a through hole part add the copper0 definition before line {1:s}\n'.format(str(InFile), str(FzpDict['copper1.lineno'])))

    elif 'copper0.layerid' in FzpDict and not 'copper1.layerid' in FzpDict:

        Errors.append('Error 37: File\n\'{0:s}\'\n\nThis is a smd part as only the copper0 view is present but it is on the bottom layer, not the top.\nIf you wanted a smd part change copper0 to copper 1 at line  {1:s}\nIf you wanted a through hole part add the copper1 definition after line {1:s}\n'.format(str(InFile), str(FzpDict['copper0.lineno'])))

    # End of if 'hybridsetforpcbView' in State:

    logging.info (' Exiting FzpCheckViews Level %s\n', Level)

# End of FzpCheckViews(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpProcessConnectorsTs3(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    # We are in the connectors grouping so find and record connectors and their
    # attributes in the input stream. 

    logging.info (' Entering FzpProcessConnectorsTs3 Level %s source line %s\n', Level, Elem.sourceline)

    logging.debug (' FzpProcessConnectorsTs3: Entry TagStack %s State %s Errors %s\n', TagStack, State, Errors)

    # TagStack length of 3 ('empty', 'module', 'connectors') is what tripped 
    # the call to this routine so we start processing at TagStack length 4 in 
    # this large case statement which trips when it finds the correct state 
    # (or complains if it finds an incorrect state due to errrorS.)

    if len(TagStack) == 4:

        # Go and process the TagStack level 4 stuff (connector name type id)

        FzpProcessConnectorsTs4(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

    elif len(TagStack) == 5:

        # Go and process the TagStack level 5 stuff (description or views)

        FzpProcessConnectorsTs5(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)


    elif len(TagStack) == 6:

        # Go and process the TagStack level 6 stuff (viewname)

        FzpProcessConnectorsTs6(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

    elif len(TagStack) == 7:

        # Go and process the TagStack level 7 stuff (p svgId layer terminalId
        # legId copper0 copper1 etc.)

        FzpProcessConnectorsTs7(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

    else:

        # Too many levels down in the tag stack. There is an error somewhere. 

        Errors.append('Error 38: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, tag stack is at level {2:s} and should only go to level 7\n'.format(str(InFile), str(Elem.sourceline), str(len(TagStack))))

    # End of if len(TagStack) == 4:

    logging.info (' Exiting FzpProcessConnectorsTs3 Level %s\n', Level)

# End of def FzpProcessConnectorsTs4(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpProcessConnectorsTs4(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpProcessConnectorsTs4 Level %s source line %s\n', Level, Elem.sourceline)

    logging.debug (' FzpProcessConnectorsTs4: Entry TagStack %s State %s\n', TagStack, State)


    LeadingConnectorRegex = re.compile(r'connector',  re.IGNORECASE)

    # TagStack should be 'module', 'connectors', 'connector' with attributes
    # name, type and id so check and process them. Check that 
    # State['nexttag'] is 'connector' or 'p' (from the end of a previous 
    # connector) to indicate that is what we are expecting at this time. 
    
    # Because we may also have spice data here (that we want to ignore) that 
    # isn't on the tag stack, check if the current tag may be spice (or at 
    # typo, we can't tell the difference) by checking the current tag value. 

    # Set the value of Tag from Elem (because spice tags won't be on the stack)

    Tag = Elem.tag

    logging.debug (' ProcessConnectorsTs4: initial Tag %s\n', Tag)

    # Since we can have spice data inserted here, check the tag to see if it
    # is one we are willing to deal with. If not read on discarding and warning
    # as we go until we come to something we recognize.

    if Tag == None or not Tag in ['connector', 'description', 'views', 'breadboardView', 'p', 'schematicView', 'pcbView']:

        # Assume this is spice data, but warn about it in case it is a typo
        # Ignore those tags which we know are spice related.

        if not Tag in ['erc', 'voltage', 'current']:

            logging.debug (' FzpProcessConnectorsTs4: assuming Tag %s is spice data\n', Tag)

            Warnings.append('Warning 10: File\n\'{0:s}\'\nAt line {1:s}\n\nTag {2:s}\nis not recognized and assumed to be spice data which is ignored\n(but it might be a typo, thus this warning)\n'.format(str(InFile), str(Elem.sourceline), str(Tag)))

        # End of if not Tag in ['erc', 'voltage', 'current']:
         
        # leave the state variables as is until we find something we recognize.

    else:
    
        StackTag, StackLevel = TagStack[len(TagStack) - 1]

        Tag = StackTag
    
        if State['nexttag'] != 'connector' and State['nexttag'] != 'p':
    
            logging.debug (' FzpProcessConnectorsTs4: TagStack 3: %s should be p or connector\n', State['nexttag'])
    
            Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected tag \'connector\' or \'p\' not {2:s}\n'.format(str(InFile), str(Elem.sourceline), str(State['nexttag'])))
            
        # End of if State['nexttag'] != 'connector' and State['nexttag'] != 'p':
    
        # Make sure the tag we saw is connector (independent of what we
        # expected to see above)
    
        if Tag != 'connector':
    
            logging.debug (' FzpProcessConnectorsTs4: TagStack 3: Tag %s should be connector\n', Tag)
    
            Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nSate error, expected tag \'connector\' not {2:s}\n'.format(str(InFile), str(Elem.sourceline), str(Tag)))
    
        # End of if Tag != 'connector':
    
        # Set the current tag to 'connector'
    
        State['lasttag'] = 'connector'
    
        # and that we expect a description to be next.
    
        State['nexttag'] = 'description'
    
        # Get the attribute values we should have
    
        Id = Elem.get('id')
    
        Type = Elem.get('type')
    
        Name = Elem.get('name')
    
        if Id == None:
    
            Errors.append('Error 39: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector has no id\n'.format(str(InFile), str(Elem.sourceline)))
    
            # give it a bogus value so it has one.
    
            Id = 'none'
        
        elif Id in FzpDict:
    
            # If it is a dup, error!
    
            DupNameError(InFile, Id, Elem, Errors)
    
        else:
    
            # else mark it as seen
    
            FzpDict[Id] = Id

            # and note that we have seen this pin number. To get the number
            # remove the prepended 'connector'.

            PinNo = LeadingConnectorRegex.sub('', Id)

            if 'pinnos' in FzpDict:

                # The entry already exists so append this pin number to the 
                # list. 

                FzpDict['pinnos'].append(PinNo)

            else:

                # create the entry and add the pin number.

                FzpDict['pinnos'] = [PinNo]

            # End of if 'pinnos' in FzpDict:
    
        # End of if Id == None:
    
        # Create an entry with unique prefix 'connectorx.id.bus so bus 
        # checking won't match svg terminal or leg ids, only id entries. 
        # Set it to itself so we know this isn't yet part of any bus during 
        # bus processing later. 
    
        FzpDict[Id + '.id.bus'] = Id + '.id.bus'

        # Do the same for subparts so we are ready if buses and subparts can
        # ever coexist (they can't right now ...)

        FzpDict[Id + '.id.subpart'] = Id + '.id.subpart'
    
        # Set the id value in to State for later processing. 
    
        State['lastvalue'] = Id
    
        if Name == None:
    
            Errors.append('Error 40: File\'n{0:s}\'\nAt line {1:s}\n\nConnector has no name\n'.format(str(InFile), str(elem.sourceline)))
    
            # give it a bogus value so it has one.
    
            Name = 'none'
    
        elif Name in FzpDict:

            # If it is a dup, warning!

            DupNameWarning(InFile, Name, Elem, Warnings)
    
        else:
    
            # else mark it as seen
    
            FzpDict[Name] = Name
    
        # End of if Name == None:
    
        # record the name in the dictionary
    
        FzpDict[Id + '.name'] = Name
    
        logging.debug (' FzpProcessConnectorsTs4 source line %s Tag %s Id %s Type %s Name %s\n', Elem.sourceline, Tag, Id, Type, Name)
    
        if Type != 'male' and not 'notmalewarning' in State and not'breadboardfzp' in State:

            # If this isn't a breadboard file (which has hundreds of female 
            # connectors) give a warning. 
    
            Warnings.append('Warning 11: File\n\'{0:s}\'\nAt line {1:s}\n\nType {2:s} is not male (it usually should be)\n'.format(str(InFile), str(Elem.sourceline), str(Type)))

            # Note we have output this warning so we don't repeat it.

            State['notmalewarning'] = 'y'
    
        # End of if Type != 'male' and not 'notmalewarning' in State and not'breadboardfzp' in State:
            
        if Type == None:
    
            # If not flag an error as it must have one.
    
            Errors.append('Error 41: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} has no type\n'.format(str(InFile), str(Elem.sourceline), str(Id)))
    
            # then assign it a bogus value so it has one. 
    
            Type = 'none'
    
        # End of if Type == None:
    
        # Record the connector type indexed by connector name
    
        FzpDict[Id + '.type'] = Type
    
        logging.info (' Exiting FzpProcessConnectorsTs4\n')

    # end of if Tag == None or not Tag in ['connector', 'description', 'views', 'breadboardView', 'p', 'schematicView', 'pcbView']:
    
# End of FzpProcessConnectorsTs4(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpProcessConnectorsTs5(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpProcessConnectorsTs5 Level %s source line %s\n', Level, Elem.sourceline)

    logging.debug (' FzpProcessConnectorsTs5: Entry TagStack %s State %s\n', TagStack, State)

    # Set the value of Tag from Elem (because spice tags won't be on the stack)

    Tag = Elem.tag

    logging.debug (' FzpProcessConnectorsTs5: initial Tag %s\n', Tag)

    # Since we can have spice data inserted here, check the tag to see if it
    # is one we are willing to deal with. If not read on discarding and warning
    # as we go until we come to something we recognize.

    if Tag == None or not Tag in ['connector', 'description', 'views', 'breadboardView', 'p', 'schematicView', 'pcbView']:

        # Assume this is spice data, but warn about it in case it is a typo

        logging.debug (' FzpProcessConnectorsTs5: assuming Tag %s is spice data\n', Tag)

        Warnings.append('Warning: File\n\'{0:s}\'\nAt line {1:s}\n\nTag {2:s}\nis not recognized and assumed to be spice data which is ignored\n(but it might also be a typo, thus this warning)\n'.format(str(InFile), str(Elem.sourceline), str(Tag)))
         
        # leave the state variables as is until we find something we recognize.

    else:
    
        # Set Id from State['lastvalue']
    
        Id = State['lastvalue']
    
        # We should now have either description or views so check what we 
        # expect and then what we actually have. 
    
        if State['nexttag'] != 'description' and State['nexttag'] != 'views':
    
            Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected tag \'description\' or \'views\' not {2:s}\n'.format(str(InFile), str(Elem.sourceline), str(State['nexttag'])))
    
        # End of if State['nexttag'] != 'description' and State['nexttag'] != 'views':
        if  Tag == 'description':
    
            # All we need to do is set up the last and next tags. 
    
            State['lasttag'] = 'description'
    
            State['nexttag'] = 'views'
    
        elif Tag == 'views':
    
            # All we need to do is check the last tag was 'description' then
            # set up the last and next tags.
    
            if State['lasttag'] != 'description':
                
                Errors.append('Error 42: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} has no description\n'.format(str(InFile), str(Elem.sourceline), str(Id)))
    
            # End of if State['lasttag'] != 'description':
    
            State['lastag'] = 'views'
    
            State['nexttag'] = 'viewname'
    
        else:
    
            Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, connector {2:s}, expected tag \'description\' or \'views\' got {3:s}\n'.format(str(InFile), str(Elem.sourceline), str(Id), str(Tag)))
    
        # End of if Tag == 'description':
    
    # End of if not Tag in ['connector', 'description', 'views', 'breadboardView', 'p', 'schematicView', 'pcbView']:

    logging.info (' Exiting FzpProcessConnectorsTs5\n')

#End of FzpProcessConnectorsTs5(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpProcessConnectorsTs6(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpProcessConnectorsTs6 Level %s source line %s\n', Level, Elem.sourceline)

    logging.debug (' FzpProcessConnectorsTs6: Entry TagStack %s State %s\n', TagStack, State)

    # Set the value of Tag from the TagStack

    StackTag, StackLevel = TagStack[len(TagStack) - 1]

    Tag = StackTag

    # Set Id from State['lastvalue']

    Id = State['lastvalue']

    if Tag == 'p':

        Errors.append('Error 43: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} missing viewname\n'.format(str(InFile), str(Elem.sourceline), str(Id)))
   
        State['lasttag'] = 'viewname'

        State['nexttag'] = 'p' 

    elif State['nexttag'] != 'p' and State['nexttag'] != 'viewname':

        Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, connector {2:s}, expected \'p\' or \'viewname\' got {3:s}\n'.format(str(InFile), str(Elem.sourceline), str(Id), str(State['nexttag'])))

        # It is unclear what State should be so leave it as is which will
        # likely cause an error cascade, but we have flagged the first one.

    else:

        # We look to have a view name so process it. 

        if Tag not in ['breadboardView', 'schematicView', 'pcbView']:

            logging.debug (' ProcessConnectorsTs6 source line %s Append invalid tag error Tag %s TagStack %s State %s\n', Elem.sourceline, Tag, TagStack, State)

            Errors.append('Error 44: File\n\'{0:s}\'\nAt line {1:s}\n\nViewname {2:s} invalid (typo?)\n'.format(str(InFile), str(Elem.sourceline), str(Tag)))

        else:

            # Note that we have seen this view in State.

            State[Tag] = 'y'

        # End of if Tag not in ['breadboardView', 'schematicView', 'pcbView']:

        State['lasttag'] = Tag

        State['nexttag'] = 'p'

    # End of if Tag == 'p':

    logging.debug (' FzpProcessConnectorsTs6: Exit TagStack %s State %s\n', TagStack, State)

    logging.info (' Exiting FzpProcessConnectorsTs6\n')

# End of def FzpProcessConnectorsTs6(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):


def FzpProcessConnectorsTs7(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpProcessConnectorsTs7 Level %s source line %s\n', Level, Elem.sourceline)

    logging.debug (' FzpProcessConnectorsTs7: Entry TagStack %s State %s\n', TagStack, State)

    # Set the value of Tag from the TagStack

    StackTag, StackLevel = TagStack[len(TagStack) - 1]

    Tag = StackTag

    # Set Id from State['lastvalue']

    Id = State['lastvalue']

    if not State['nexttag'] == 'p':

        # expected state doesn't match. 

        logging.debug (' FzpProcessConnectorsTs7 source line %s State[\'nexttag\'] %s isn\'t \'p\'\n', Elem.sourceline, State['nexttag'])

        Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected tag \'p\' got {2:s}\n'.format(str(InFile), str(Elem.sourceline), str(State['nexttag'])))

        # unclear what State should be so leave as is which may cause an
        # error cascade. 

    else:

        if Tag == 'p':

            # We have found a 'p' line which means we have the associated 
            # view id on the tag stack and need to add the connector names 
            # to the dictionary for use checking the pins in the svgs 
            # later.  

            # Get the viewname from the TagStack.

            StackTag, StackLevel = TagStack[len(TagStack) - 2]

            View = StackTag

            logging.debug (' FzpProcessConnectorsTs7 View set to %s\n', View)

            # We need a layer value (even if it is None) for the index.

            Layer = Elem.get('layer')

            if Layer == None:

                Layer = 'none'

                logging.debug (' FzpProcessConnectorsTs7 source line %s missing layer\n', Elem.sourceline)

                Errors.append('Error 45: File\n\'{0:s}\'\nAt line {1:s}\n\nLayer missing\n'.format(str(InFile), str(Elem.sourceline)))

            # End of if Layer == None:

            # Verify the layerId is correct. 

            if not View  + '.' + 'LayerId' in FzpDict:

                # Don't have a layerId for this view!

                Errors.append('Error 46: File\n\'{0:s}\'\nAt line {1:s}\n\nNo layerId for View {2:s}\n'.format(str(InFile), str(Elem.sourceline), str(View)))

            elif View != 'pcbView' and Layer != FzpDict[View  + '.' + 'LayerId']:

                # For all except pcbView, the layerIds don't match.

                Errors.append('Error 47: File\n\'{0:s}\'\nAt line {1:s}\n\nLayerId {2:s} doesn\'t match View {3:s} layerId {4:s}\n'.format(str(InFile), str(Elem.sourceline), str(Layer), str(View), str(FzpDict[View  + '.' + 'LayerId'])))

            elif View == 'pcbView':

                if  not Layer in FzpDict[View  + '.' + 'LayerId']:

                    # Layer isn't a valid layer for pcbView.

                    Errors.append('Error 47: File\n\'{0:s}\'\nAt line {1:s}\n\nLayerId {2:s} doesn\'t match any in View {3:s} layerIds {4:s}\n'.format(str(InFile), str(Elem.sourceline), str(Layer), str(View), str(FzpDict[View  + '.' + 'LayerId'])))

                elif Layer == 'copper0':

                    # While multiple layers are allowed, only copper0 and 
                    # copper1 (if they exist) are allowed in connectors and
                    # they must be unique. 

                    if Id + '.' + Layer in FzpDict:

                        # Not unique so error. 

                        Errors.append('Error 48: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} layer {3:s} already defined, must be unique\n'.format(str(InFile), str(Elem.sourceline), str(Id), str(Layer)))

                    else:
    
                        # It is unique so note that we have seen it now. 

                        FzpDict[Id + '.' + Layer] = 'y'

                    # End of if Id + '.' + Layer in FzpDict:

                elif Layer == 'copper1':

                    # While multiple layers are allowed, only copper0 and 
                    # copper1 (if they exist) are allowed in connectors and
                    # they must be unique. 

                    if Id + '.' + Layer in FzpDict:

                        # Not unique so error. 

                        Errors.append('Error 48: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} layer {3:s} already defined, must be unique\n'.format(str(InFile), str(Elem.sourceline), str(Id), str(Layer)))

                    else:
    
                        # It is unique so note that we have seen it now. 

                        FzpDict[Id + '.' + Layer] = 'y'

                    # End of if Id + '.' + Layer in FzpDict:

                # End of if  not Layer in FzpDict[View  + '.' + 'LayerId']:

            # End of if not View  + '.' + 'LayerId' in FzpDict:

            # Get the hybrid attribute if present (as it affects checking 
            # below)

            Hybrid = Elem.get('hybrid')

            if Hybrid != None:

                # If Hybrid isn't present just drop through as that is fine.
                # If Hybrid is present, anything but 'yes' is an error ...

                if Hybrid != 'yes':

                    Errors.append('Error 49: File\n\'{0:s}\'\nAt line {1:s}\n\nhybrid is present but isn\'t \'yes\' but {2:s} (typo?)\n'.format(str(InFile), str(Elem.eline),str(Hybrid)))

                else:

                    # hybrid is set so if this is pcbview note that in State

                    if View == 'pcbView':

                        State['hybridsetforpcbView'] = 'y'

                    # End of if View == 'pcbView':

                # End of if Hybrid != 'yes':

            # End of if Hybrid != None:

            logging.debug (' FzpProcessConnectorsTs7 Layer set to %s\n', Layer)

            # then get all the attributes and check their values as 
            # appropriate. Mark we haven't yet seen a svgid, terminalId or
            # legId. A svgId is required and will cause an error, terminalId 
            # will be warned about (becuase it is usually an error) in 
            # schematicview and both a TerminalId and a LegId is an error, it 
            # must be one or the other not both. 

            SvgIdSeen = 'n'

            TerminalIdSeen = 'n'

            LegIdSeen = 'n'

            for Key in Elem.keys():

                logging.debug (' FzpProcessConnectorsTs7: source line %s Tag %s Id %s Key %s\n', Elem.sourceline, Tag, Id, Key)

                if Key not in ['terminalId', 'svgId', 'layer', 'legId', 'hybrid']:

                    # Warn about a non standard key ...

                    logging.debug (' FzpProcessConnectorsTs7 unknown key %s\n', Key)

                    Warnings.append('Warning 12: File\n\'{0:s}\'\nAt line {1:s}\n\nKey {2:s} is not recognized\n'.format(str(InFile), str(Elem.sourceline), str(Key)))

                # End of if Key not in ['terminalId', 'svgId', 'layer', 'legId']:
                # Now get the value of the key.

                Value = Elem.get(Key)

                if Key == None:

                    Errors.append('Error 50: File\n\'{0:s}\'\nAt line {1:s}\n\nTag {2:s} is present but has no value\n'.format(str(InFile), str(Elem.sourceline),str(Key)))

                # End of if Key == None"

                # then make checks depending on the value of the key.

                if Key == 'svgId':

                    # Note that we have seen an svgId tag (if the value is 
                    # None, the error will have been noted above.) 

                    SvgIdSeen = 'y'

                # End of if Key == 'svgId':

                if Key == 'terminalId':

                    # Note that we have seen an terminalId tag (if the value 
                    # is None, the error will have been noted above.) 

                    TerminalIdSeen = 'y'
            
                # End of if Key == 'terminalId':

                if Key == 'legId':

                    # Note that we have seen an legId tag (if the value is 
                    # None, the error will have been noted above.) 

                    LegIdSeen = 'y'

                # End of if Key == 'legId':
            

                if Key == 'layer':

                    # If the key is 'layer' then this layer id needs to exist
                    # in the associated svg, so add this to the list of layers
                    # to look for in the svg. The layer needs to be the same
                    # for all

                    if View + '.layer' in FzpDict:

                        # Already exists so append this one if it isn't 
                        # already present.

                        if not Layer in FzpDict[View + '.layer']:

                            logging.debug (' FzpProcessConnectorsTs7: source line %s View %s layer %s added\n', Elem.sourceline, View, Layer)

                            FzpDict[View + '.layer'].append(Layer)

                        # End of if not Layer in FzpDict[View + '.layer']:

                    else:

                        # Doesn't exist yet, so create it and add the layer.

                        logging.debug (' FzpProcessConnectorsTs7: source line %s View %s, create and add layer %s added\n', Elem.sourceline, View, Layer)
                        FzpDict[View + '.layer'] = [Layer]

                    # End of if View + '.layer' in FzpDict:

                else:

                    # Key isn't layer so if it is a connector and Hybrid isn't
                    # set to 'yes' (in which case the connector will be ignored
                    # as this view is unused)
                
                    if Key in ['terminalId', 'svgId', 'legId'] and Hybrid != 'yes':

                        # Check if it matches with the connector defined
                
                        if not re.match(Id, Value):

                            # No, flag it as a warning, as it is unusual (but
                            # not illegal) and thus possibly an error.
 
                            logging.debug (' FzpProcessConnectorsTs7: Id %s doesn\'t match Value %s\n',Id, Value)

                            Warnings.append('Warning 13: File\n\'{0:s}\'\nAt line {1:s}\n\nValue {2:s} doesn\'t match Id {3:s}. (Typo?)\n'.format(str(InFile), str(Elem.sourceline), str(Value), str(Id)))


                        # End of if not re.match(Id, Value):

                        # Now make sure this connector is unique in this view
                        # and if it is add it to the list of connectors to 
                        # verify is in the associated svg.

                        if not View + '.' + Value + '.' + Layer in FzpDict:

                            # This is one of the pin names and we haven't seen
                            # it before, so add it to the connectors list for 
                            # matching in the svg. Indicate we have seen this
                            # connector (in case we see another)

                            FzpDict[View + '.' + Value + '.' + Layer] = 'y'

                            # If the entry for this view doesn't exist yet, 
                            # create it and add this connector to the list
                            # otherwise append the connector to the existing
                            # list (weeding out duplicate . 

                            if not 'connectors.fzp.' + View in FzpDict:
    
                                logging.debug (' FzpProcessConnectorsTs7: create %s add %s\n','connectors.fzp.' + View, Value)

                                # First connector so create the list.

                                FzpDict['connectors.fzp.' + View] = [Value]

                            else:


                                logging.debug (' FzpProcessConnectorsTs7: View %s conents %s\n','connectors.fzp.' + View, FzpDict['connectors.fzp.' + View])

                                if not Value in FzpDict['connectors.fzp.' + View]:

                                    # For pcb view pins will appear twice, once
                                    # for copper0 and once for copper1, we only
                                    # need one value so if it is already here 
                                    # don't add a new one.

                                    logging.debug (' FzpProcessConnectorsTs7: add %s add %s\n','connectors.fzp.' + View, Value)

                                    FzpDict['connectors.fzp.' + View].append(Value)

                                # End of if not Value in FzpDict['connectors.fzp.' + View]:

                            # End of if not 'connectors.fzp.' + View in FzpDict:

                        # End of if not View + '.' + Value + '.' + Layer in FzpDict:

                        if View == 'schematicView':

                            # This is schematic view, so in case this is a 
                            # subpart, associate the pins with the connectorId

                            if not 'schematic.' + Id in FzpDict:

                                # Doesn't exist yet so create it.

                                FzpDict['schematic.' + Id] = []

                            # End of if not 'schematic.' + Id in FzpDict:

                            FzpDict['schematic.' + Id].append(Value)

                        # End of if View == 'schematicView':

                    # End of if Key in ['terminalId', 'svgId', 'legId'] and Hybrid != 'yes':

                # End of if Key == 'layer':

            # End of for Key in Elem.keys():

            # Now we have all the attributes, see whats missing. We already
            # complained about a missing layer above so only do svgId and if
            # view is schematicview, terminalId as a warning, here.TerminalId
            # and legId are optional although no terminalId is usually an error
            # in schematic, only svgId is required, but if hybrid is 'yes' 
            # even that is optional. However both a terminalId and a legID are
            # an error so note that. 

            if TerminalIdSeen == 'y' and LegIdSeen == 'y':

                Errors.append('Error 80: File\n\'{0:s}\'\nAt line {1:s}\n\nBoth terminalId and legId present, only one or the other is allowed.\n'.format(str(InFile), str(Elem.sourceline)))

            # End of if TerminalIdSeen == 'y' and LegIdSeen == 'y':

            if SvgIdSeen != 'y' and Hybrid != 'yes':

                Errors.append('Error 51: File\n\'{0:s}\'\nAt line {1:s}\n\nsvgId missing\n'.format(str(InFile), str(Elem.sourceline)))
         
            # End of if SvgIdSeen != 'y' and Hybrid != 'yes':

            if TerminalIdSeen != 'y' and View == 'schematicView' and Hybrid != 'yes':
                Warnings.append('Warning 14: File\n\'{0:s}\'\nAt line {1:s}\n\nterminalId missing in schematicView (likely an error)\n'.format(str(InFile), str(Elem.sourceline)))

            # End of if TerminalIdSeen != 'y' and View == 'schematicview' and Hybrid != 'yes':

        # End of if Tag == 'p':

    # End of if not State['nexttag'] == 'p':

    logging.debug (' Exiting FzpProcessConnectorsTs7: source line %s tag %s attrib %s TagStack %s State %s\n', Elem.sourceline, Elem.tag, Elem.attrib, TagStack, State)

    logging.info (' Exiting FzpProcessConnectorsTs7\n')

# End of FzpProcessConnectorsTs7(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpProcessBusTs3(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpProcessBusTs3 Level %s\n', Level)

    # TagStack length of 3 ('empty', 'module', 'buses') is what tripped the 
    # call to this routine so we start processing at TagStack length 3 in this 
    # case statement which trips when it finds the correct state (or complains
    # if it finds an incorrect state due to errors.)

    if len(TagStack) == 4:

        # Go and process the TagStack level 4 stuff (bus for the bus id)

        FzpProcessBusTs4(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

    elif len(TagStack) == 5:

        # Go and process the TagStack level 5 stuff (nodeMembers)

        FzpProcessBusTs5(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

    elif len(TagStack) > 5:

        # There shouldn't be anything past 5th level so something is wrong. 

        Errors.append('Error 38: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, tag stack is at level {2:s} and should only go to level 5\n\nTag {3:s} will be ignored\n'.format(str(InFile), str(Elem.sourceline), str(len(TagStack)), str(Tag)))

    # End of if len(TagStack) == 4:
    
    logging.info (' Exiting FzpProcessBusTs3 Level %s\n', Level)

# End of def FzpProcessBusTs3(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpProcessBusTs4(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpProcessBusTs4 level %s source line %s\n', Level, Elem.sourceline)

    logging.debug (' FzpProcessBusTs4: Entry TagStack %s State %s\n', TagStack, State)

    if not State['lasttag'] in ['buses', 'bus', 'nodeMember']:

        logging.debug (' FzpProcessBusTs4:  Unexpected state %s expected buses or nodeMember\n',State['lasttag'])

        # Not the expected state possibly a missing line. 

        Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected lasttag \'buses\' or \'nodeMember\' not {2:s}\n(Missing line?)\n'.format(str(InFile), str(Elem.sourceline), str(State['lasttag'])))
        
    # End of if not State['lasttag'] in ['buses', 'nodeMember']:

    StackTag, StackLevel = TagStack[len(TagStack) - 1]

    Tag = StackTag

    if Tag != 'bus':

        logging.debug (' FzpProcessBusTs4:  Unexpected Tag %s expected bus\n', Tag)

        Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected tag \'bus\' not {2:s}. (Missing line?)\n'.format(str(InFile), str(Elem.sourceline), str(Tag)))
        
        # it is unclear what state should be so leave it as is which may cause
        # an error cascade ...

    else:

        # We look to have a bus line so get the bus id. 

        Id = Elem.get('id')

        if Id == None:

            # Note that we have seen an empty bus definition (some parts have
            # one) and give the Id a text value

            Id = ''

            FzpDict['empty_bus_defined'] = 'y'

            Warnings.append('Warning 15: File:\n\'{0:s}\'\nAt line {1:s}\n\nEmpty bus definition, no id (remove?)\n'.format(str(InFile), str(Elem.sourceline)))

        else:            

            # and note we have seen a bus (not just the buses tag) for subparts 
            # but we haven't put out an error message for it yet if there is a 
            # sub parts definition later, we will. 

            FzpDict['bus_defined'] = 'n'

            logging.debug (' FzpProcessBusTs4: source line %s Tag %s Id %s State %s\n', Elem.sourceline, Tag, Id, State)

            if Id + '.bus_seen' in FzpDict:
    
                # Not unique error
    
                DupNameError(InFile, Id, Elem, Errors)
    
            else:
    
                logging.debug (' FzpProcessBusTs4: Marked Id %s seen\n', Id)
    
                # else mark it as seen 
    
                FzpDict[Id + '.bus_seen'] = Id
    
            # End of if Id + '.bus_seen' in FzpDict:
    
        # End of Id == None:

        # Set the bus id even if it is None, so we don't impact the last bus
        # with the current information. 

        State['lastvalue'] = Id

        if (Id + '.bus') in FzpDict:

            logging.debug (' FzpProcessBusTs4: Id %s already exists\n', Id)

            # If we already have this bus id flag an error.

            Errors.append('Error 52: File\n\'{0:s}\'\nAt line {1:s}\n\nBus {2:s} already defined\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

        else:

            logging.debug (' FzpProcessBusTs4: created counter for Id %s\n', Id)

            # mark this as a bus currently with no nodes.

            FzpDict[Id + '.bus'] = 0

        # End of if (Id + '.bus') in FzpDict:

        # Set the current and expected State

        State['lasttag'] = 'bus'

        State['nexttag'] = 'nodeMember'

        logging.debug ('  FzpProcessBusTs4: source line %s end of bus Id %s State %s\n', Elem.sourceline, Id, State)

    # End of if Tag != 'bus':

    logging.info (' Exiting FzpProcessBusTs4 level %s source line %s\n', Level, Elem.sourceline)

# End of def FzpProcessBusTs4(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpProcessBusTs5(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpProcessBusTs5 level %s source line %s\n', Level, Elem.sourceline)

    logging.debug (' FzpProcessBusTs5: Entry TagStack %s State %s\n', TagStack, State)

    # At this point we set the last Id we saw from State and Tag from the 
    # TagStack. 

    Id = State['lastvalue']

    StackTag, StackLevel = TagStack[len(TagStack) - 1]

    Tag = StackTag

    if not State['nexttag'] in ['bus', 'nodeMember']:

        logging.debug (' FzpProcessBusTs5:  Unexpected state %s expected bus or nodeMember\n',State['nexttag'])

        # State isn't what we expected, error

        Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected lasttag \'bus\' or \'nodeMember\' not {2:s}\n(Missing line?)\n'.format(str(InFile), str(Elem.sourceline), str(State['lasttag'])))

    else:    
    
        if Tag == 'nodeMember':
    
            # Since Connector shouldn't be unique we don't need to check if 
            # it is.
    
            Connector = Elem.get('connectorId')
    
            if Connector != None:
    
                # Check if the connector exists
    
                if not Connector + '.id.bus' in FzpDict:

                    logging.debug (' FzpProcessBusTs5:  Connector %s doesn\'t exist\n',Connector)
    
                    # No, flag an error.
    
                    Errors.append('Error 53: File\n\'{0:s}\'\nAt line {1:s}\n\nBus nodeMember {2:s} does\'t exist\n'.format(str(InFile), str(Elem.sourceline), str(Connector)))
    
                else:
    
                    # Since we set the value as the key as a place holder 
                    # intially, check if that is still true (i.e. this isn't 
                    # part of another bus already). 
    
                    if FzpDict[Connector + '.id.bus'] == FzpDict[Connector + '.id.bus']:

                        logging.debug (' FzpProcessBusTs5: Connector %s added to bus %s\n',Connector, Id)
    
                        # connector not part of another bus so mark it as ours. 
                        # by writing our bus Id in to it.
    
                        FzpDict[Connector + '.id.bus'] = Id
    
                    else:
    
                        # connector is already part of another bus, flag an error.

                        logging.debug (' FzpProcessBusTs5: connector %s already in another bus\n',Connector)
    
                        Errors.append('Error 54: File\n\'{0:s}\'\nAt line {1:s}\n\nBus nodeMember {2:s} already in bus {3:s}\n'.format(str(InFile), str(Elem.sourceline), str(Connector), str(FzpDict[Connector + '.id.bus'])))
    
                    # End of if FzpDict[connector + '.id.bus'] == FzpDict[connector + '.id.bus']:
    
                # End of if not Connector + '.id.bus' in FzpDict:
    
                # Now increase the count of nodes in the bus by 1.
    
                FzpDict[Id + '.bus'] += 1
    
            # End of if Connector != None:
    
        # End of if Tag == 'nodeMember':
    
    # End of if not State['nexttag'] in ['bus', 'nodeMember']:

    logging.info (' Exiting FzpProcessBusTs5 level %s source line %s\n', Level, Elem.sourceline)

# End of def FzpProcessBusTs5(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpProcessSchematicPartsTs3(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpProcessSchematicPartsTs3 Level %s\n', Level)

    StackTag, StackLevel = TagStack[len(TagStack) - 1]

    Tag = StackTag

    # Check for a duplicate schematic-subparts

    if Tag == 'schematic-subparts':

        # Unexpected state error

        Errors.append('Error: File\n\'{0:s}\'\nAt line {1:s}\n\nDuplicate tag in schematic-subparts\n'.format(str(InFile), str(Elem.sourceline)))

    # End of if Tag == 'schematic-subparts':

    logging.debug (' FzpProcessSchematicPartsTs3: TagStack len %s Tag %s\n', len(TagStack), Tag)

    # Process the data according to tag stack level.

    if len(TagStack) == 4:

        # Go and process the TagStack level 4 stuff (subpart id and label)

        FzpProcessSchematicPartsTs4(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

    elif len(TagStack) == 5:

        # Go and process the TagStack level 4 stuff (connectors)

        FzpProcessSchematicPartsTs5(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

    elif len(TagStack) == 6:

        # Go and process the TagStack level 5 stuff (connector)

        FzpProcessSchematicPartsTs6(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)


    elif len(TagStack) > 6:

        # There shouldn't be anything past 5th level so something is wrong. 

        Errors.append('Error 38: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, tag stack is at level {2:s} and should only go to level 6\n\nTag {3:s} will be ignored\n'.format(str(InFile), str(Elem.sourceline), str(len(TagStack)), str(Tag)))

    # End of if len(TagStack) == 3:

    logging.info (' Exiting FzpProcessSchematicPartsTs3 Level %s\n', Level)

# End of def FzpProcessSchematicPartsTs3(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpProcessSchematicPartsTs4(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpProcessSchematicPartsTs4 Level %s\n', Level)

    StackTag, StackLevel = TagStack[len(TagStack) - 1]

    Tag = StackTag

    if Tag != 'subpart':

        logging.debug (' FzpProcessSchematicPartsTs4: Unexpected Tag %s expected subpart\n', Tag)

        # State isn't what we expected, error

        Errors.append('Error 26: File\n\n{0:s}\'\nAt line {1:s}\n\nState error, expected tag \'subpart\' not {2:s}. (Missing line?)\n'.format(str(InFile), str(Elem.sourceline), str(Tag)))

    else:

        if State['lasttag'] == 'schematic-subparts' or State['lasttag'] == 'connector':
    
            Id = Elem.get('id')
    
            if Id == None:
    
                logging.debug (' FzpProcessSchematicPartsTs4: Id none error\n')

                Errors.append('Error 55: File\n\'{0:s}\'\nAt line {1:s}\n\nSubpart has no id\n'.format(str(InFile), str(Elem.sourceline)))
    
            elif Id in FzpDict:
    
                logging.debug (' FzpProcessSchematicPartsTs4: subpart Id not unique error\n')

                # error, connector must be unique
    
                Errors.append('Error 56: File\n\'{0:s}\'\nAt line {1:s}\n\nSubpart id {2:s} already exists (must be unique)\n'.format(str(InFile), str(Elem.sourceline), str(Id)))
    
            # End of if Id == None:
    
            Label = Elem.get('label')
    
            if Label == None:
    
                logging.debug (' FzpProcessSchematicPartsTs4: Label None error\n')
    
                Errors.append('Error 57: File\n\'{0:s}\'\nAt line {1:s}\n\nSubpart has no label\n'.format(str(InFile), str(Elem.sourceline)))
    
            elif Label in FzpDict:
    
                # not unique error
    
                logging.debug (' FzpProcessSchematicPartsTs4: Label Not unique error\n')
    
                DupNameError(InFile, Label, Elem, Errors)
    
            else:
    
                # mark it as seen
    
                logging.debug (' FzpProcessSchematicPartsTs4: Mark Label %s seen\n',Label)
    
                FzpDict[Label] = Label 
    
            # End of if Label in FzpDict:
    
            # Set the subpart id even if it is None so we don't impact the last
            # subpart.
    
            State['lastvalue'] = Id
    
            if (Id + '.subpart') in FzpDict:
    
                # If we already have this subpart id flag an error (note in the
                # case of None, it may be due to other errors.)
    
                logging.debug (' FzpProcessSchematicPartsTs4: Id %s seeni already\n',Id)
    
                Errors.append('Error 58: File\n\'{0:s}\'\nAt line {1:s}\n\nSubpart {2:s} already defined (duplicate?)\n'.format(str(InFile), str(Elem.sourceline), str(Id)))
    
            else:
    
                # mark this as a subpart currently with no connections.
    
                logging.debug (' FzpProcessSchematicPartsTs4: Id %s set empty\n',Id)
    
                FzpDict[Id + '.subpart'] = 0

                if not 'subparts' in FzpDict:

                    # Note that we have subparts in the dictionary for svg 
                    # processing. 

                    FzpDict['subparts'] = []

                # End of if not Subparts in FzpDict:

                # Then add this subpart to the list of subpart ids and indicate
                # we haven't yet seen it in the svg. 

                FzpDict['subparts'].append(Id) 
    
            # End of if (Id + '.subpart') in FzpDict:
    
        else:

            # State isn't what we expected, error
    
            logging.debug (' FzpProcessSchematicPartsTs4: State error\n',State)

            Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected tag \'schematic-subparts\' or \'connector\' not {2:s}.\n'.format(str(InFile), str(Elem.sourceline), str(State['lasttag'])))

        # End of if State['lasttag'] == 'schematic-subparts' or State['lasttag'] == 'connector':

        State['lasttag'] = Tag

        State['nexttag'] = 'connectors'

    # End of if Tag != 'subpart':

    logging.info (' Exiting FzpProcessSchematicPartsTs4 Level %s\n', Level)

# End of def FzpProcessSchematicPartsTs4(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpProcessSchematicPartsTs5(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpProcessSchematicPartsTs5 Level %s\n', Level)

    StackTag, StackLevel = TagStack[len(TagStack) - 1]

    Tag = StackTag

    if Tag != 'connectors':

        logging.debug (' FzpProcessSchematicPartsTs5: Unexpected Tag %s expected connectors\n', Tag)

        # State isn't what we expected, error

        Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error expected tag \'connectors\' not {2:s}. Missing line?\n'.format(str(InFile), str(Elem.sourceline), str(Tag)))

    # End of if Tag != 'connectors':

    if State['lasttag'] == 'subpart':

        logging.debug (' FzpProcessSchematicPartsTs5: set nexttag to connector\n')

        State['lasttag'] = Tag

        State['nexttag'] = 'connector'

    else:

        # State isn't what we expected, error

        logging.debug (' FzpProcessSchematicPartsTs5: unexpected state %s expected connector\n', Tag)

        Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected last tag \'subpart\' not {2:s}.  (Missing line?)\n'.format(str(InFile), str(Elem.sourceline), str(State['lasttag'])))

    # End of if State['lasttag'] == 'subpart':

    logging.info (' Exiting FzpProcessSchematicPartsTs5 Level %s\n', Level)

# End of def FzpProcessSchematicPartsTs5(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpProcessSchematicPartsTs6(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering FzpProcessSchematicPartsTs6 Level %s\n', Level)

    StackTag, StackLevel = TagStack[len(TagStack) - 1]

    Tag = StackTag

    if Tag != 'connector':

        logging.debug (' FzpProcessSchematicPartsTs6: Unexpected Tag %s expected connector\n', Tag)

        # State isn't what we expected, error

        Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected tag \'connector\' not {2:s}. (Missing line?)\n'.format(str(InFile), str(Elem.sourceline), str(Tag)))

    # End of if Tag != 'connector':

    # Set the Id from the previous value we have seen.

    Id = State['lastvalue']

    if State['lasttag'] == 'connectors' or State['lasttag'] == 'connector':

        # Get the ConnectorId
        
        ConnectorId = Elem.get('id')

        if ConnectorId == None:

            Errors.append('Error 59: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector id missing, ignored\n'.format(str(InFile), str(Elem.sourceline)))

        elif not ConnectorId in FzpDict:

            Errors.append('Error 60: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} doesn\'t exist (and it must)\n'.format(str(InFile), str(Elem.sourceline), str(ConnectorId)))

        else:
    
            # Since we set the value as the key as a place holder 
            # intially, check if that is still true (i.e. this isn't 
            # part of another subpart already). 
    
            if FzpDict[ConnectorId + '.id.subpart'] == FzpDict[ConnectorId + '.id.subpart']:

                logging.debug (' FzpProcessSchematicPartsTs6: Connector %s added to bus %s\n',ConnectorId, Id)
    
                # connector not part of another subpart so mark it as ours. 
                # by writing our subpart Id in to it.
    
                FzpDict[ConnectorId + '.id.subpart'] = Id

                # success, so increase the connector count for this subpart
                # by 1. 

                FzpDict[Id + '.subpart'] += 1

                if not Id + '.subpart.cons' in FzpDict:

                    # Entry doesn't exist so create it.

                    FzpDict[Id + '.subpart.cons'] = []

                # End of if not Id + '.subpart.cons' in FzpDict:

                # Then add this connector to it. 

                if not 'schematic.' + ConnectorId in FzpDict:
    
                    Errors.append('Error 81: File\n\'{0:s}\'\nAt line {1:s}\n\nSubpart connector {2:s} has no pins defined\n'.format(str(InFile), str(Elem.sourceline), str(ConnectorId), str(FzpDict[ConnectorId + '.id.subpart'])))

                else:

                    for Con in FzpDict['schematic.' + ConnectorId]: 

                        # Append the pins associated with this connector to 
                        # the subpart ID list to check when the schematic 
                        # svg is processed later. 

                        FzpDict[Id + '.subpart.cons'].append(Con)

                    # End of for Con in FzpDict['schematic.' + ConnectorId]: 

                # End of if not 'schematic.' + ConnectorId in FzpDict:
    
            else:
    
                # connector is already part of another subpart, flag an error.

                logging.debug (' FzpProcessSchematicPartsTs6: connector %s already in another subpart\n',ConnectorId)
    
                Errors.append('Error 61: File\n\'{0:s}\'\nAt line {1:s}\n\nSubpart connector {2:s} already in subpart {3:s}\n'.format(str(InFile), str(Elem.sourceline), str(ConnectorId), str(FzpDict[ConnectorId + '.id.subpart'])))
    
            # End of if FzpDict[connectorId + '.id.subpart'] == FzpDict[connectorId + '.id.subpart']:

        # End of if ConnectorId == None:

    else:

        # State isn't what we expected, error

        Errors.append('Error 26: File\n\'{0:s}\'\nAt line {1:s}\n\nState error, expected last tag \'connectors\' or \'connector\' not {2:s}.\n'.format(str(InFile), str(Elem.sourceline), str(State['lasttag'])))

    # end of if State['lasttag'] == 'connectors' or State['lasttag'] == 'connector':

    State['lasttag'] = Tag

    State['nexttag'] = 'connector'

    logging.info (' Exiting FzpProcessSchematicPartsTs6 Level %s\n', Level)

# End of def FzpProcessSchematicPartsTs6(InFile, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def FzpCheckConnectors(InFile, Elem, FzpDict, Errors, Warnings, Info, State, Level):

    logging.info (' Entering FzpCheckConnectors Level %s\n', Level)

    if not 'pinnos' in FzpDict or len(FzpDict['pinnos']) == 0:

        # no connectors found!

        logging.debug (' FzpCheckConnectors: no pinnos found\n')

        Errors.append('Error 62: File\n\'{0:s}\'\n\nNo connectors found to check\n'.format(str(InFile)))

    else:

        # Check that pin numbers start at 0 and are contiguous. 

        logging.debug (' FzpCheckConnectors: pinnos %s\n',FzpDict['pinnos'])

        if not 'pinnosmsg' in State:

            # Only output a pin number message once per file.

            if not '0' in FzpDict['pinnos']:

                Errors.append('Error 63: File\n\'{0:s}\'\n\nConnector0 doesn\'t exist (connectors should start at 0)\n'.format(str(InFile)))

            # End of if not '0' in FzpDict['pinnos']:

            State['pinnosmsg'] = 'y'

        # End of if not 'pinnosmsg' in State:
        
        for Pin in range(len(FzpDict['pinnos'])):
    
            # Mark an error if any number in sequence doesn't exist as the 
            # connector numbers must be contiguous. 

            if not 'pinnosmsg' in State:

                # Only output a pin number message once per file.

                if not str(Pin) in FzpDict['pinnos']:

                    logging.debug (' FzpCheckConnectors: pin %s pinnos %s\n',Pin, FzpDict['pinnos'])

                    Errors.append('Error 64: File\n\'{0:s}\'\n\nConnector{1:s} doesn\'t exist when it must to stay in sequence\n'.format(str(InFile), str(Pin)))

                    State['pinnosmsg'] = 'y'

                # End of if not Pin in FzpDict['pinnos']:

            # End of if not 'pinnosmsg' in State:
        
        # End of for pin in range(len(FzpDict['pinnos'])):

    # End of if not pinnos in FzpDict or len(FzpDict['pinnos']) == 0:

    logging.info (' Exiting FzpCheckConnectors Level %s\n', Level)

# End of def FzpCheckConnectors(InFile, Elem, FzpDict, Errors, Warnings, Info, State, Level):

def ProcessSvg(FzpType, InFile, OutFile, CurView, PrefixDir, Errors, Warnings, Info, FzpDict, FilesProcessed, TagStack, State, InheritedAttributes, Debug):

    logging.info (' Entering ProcessSvg\n')

    logging.debug ('  ProcessSvg: FzpType %s InFile %s OutFile %s CurView %s\n', FzpType, InFile, OutFile, CurView)

    # Parse the input document.

    Doc, Root = PP.ParseFile (InFile, Errors)

    logging.debug ('  ProcessSvg: return from parse Doc %s\n', Doc)

    if Doc != None:

        logging.debug ('  ProcessSvg: Calling ProcessTree Doc %s\n', Doc)

        # We have successfully parsed the input document so process it. If
        # this is only an svg file without an associated fzp, the FzpDict 
        # will be empty as there is no fzp data to check the svg against. 

        ProcessTree(FzpType, InFile, OutFile, CurView, PrefixDir, Root, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Debug)

        if not 'fzp' in FzpDict and 'pcbsvg' in State:
    
            # We don't have a fzp file so check the pcb layers which it would
            # normally do if this is a pcb svg. 

            SvgCheckPcbLayers(InFile, Errors, Warnings, Info, FzpDict, TagStack, State)

        # End of if not 'fzp' in FzpDict:

        PP.OutputTree(Doc, Root, FzpType, InFile, OutFile, Errors, Warnings, Info, Debug)

    # End of if Doc != None:

    logging.info (' Exiting ProcessSvg\n')

# End of def ProcessSvg(FzpType, InFile, OutFile, CurView, PrefixDir, Errors, Warnings, Info, FzpDict, FilesProcessed, TagStack, State, InheritedAttributes, Debug):

def RemovePx(InFile, Elem, Info, Level):

    # Remove the trailing px from a font-size command if present.

    logging.info (' Entering  RemovePx Level %s\n', Level)

    pxRegex = re.compile(r'px', re.IGNORECASE)

    FontSize = Elem.get('font-size')

    if not FontSize == None:

        if pxRegex.search(FontSize) != None:

            logging.debug (' RemovePx: Removed a px from font-size\n')

            # we have a font size, so see if it has a px and remove it if so.

            FontSize = pxRegex.sub('', FontSize)

            Elem.set('font-size', FontSize)

            Info.append('Modified 1: File\n\'{0:s}\'\nAt line {1:s}\n\nRemoved px from font-size leaving {2:s}\n'.format(str(InFile), str(Elem.sourceline), str(FontSize)))

        # End of if pxRegex.search(FontSize) != None:

    # End of if not FontSize == None:

    logging.info (' Exiting  RemovePx Level %s\n', Level)

# End of def RemovePx(InFile, Elem, Info):


def ProcessSvgLeafNode(FzpType, InFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Level):

    logging.info (' Entering ProcessSvgLeafNode Level %s\n', Level)

    logging.debug (' ProcessSvgLeafNode: Entry File %s Source line %s FzpType %s CurView %s State %s\n',InFile, Elem.sourceline, FzpType, CurView, State)

    NameSpaceRegex = re.compile(r'{.+}')

    ConnectorRegex = re.compile(r'connector', re.IGNORECASE)

    ConnectorTermRegex = re.compile(r'connector.+terminal', re.IGNORECASE)

    # Get the id and tag values and remove the namespace if present. 

    Id = Elem.get('id')

    logging.debug (' ProcessSvgLeafNode: Id %s\n', Id)

    Tag = NameSpaceRegex.sub('', str(Id))

    logging.debug (' ProcessSvgLeafNode: removed namespace from Id %s\n', Id)

    # If there is an id for this node, remove the name space element 
    # from the tag to make later processing easier. 

    Tag = Elem.tag

    logging.debug (' ProcessSvgLeafNode: Tag %s\n', Tag)

    Tag = NameSpaceRegex.sub('', str(Tag))

    logging.debug (' ProcessSvgLeafNode: removed namespace from Tag %s\n', Tag)

    if not 'SvgStart' in State:

        # Haven't yet seen the svg start line so check this one. 

        SvgStartElem(InFile, Elem, Errors, Warnings, Info, State, Level)

    # End of if not SvgStart in State:

    # Check if this is the refenence file attribute and if so if it is correct.

    SvgRefFile(FzpType, InFile, Elem, Errors, Warnings, Info, State, Level)

    # First find and set any of Fritzing's layer ids in this element. 

    SvgGroup(InFile, CurView, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

    # Check we have a layerId before any drawing element.

    SvgCheckForLayerId(Tag, InFile, CurView, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

    # Then convert any style commands to inline xml (as Fritzing sometimes 
    # doesn't process style commands and the 2 forms are identical). 

    SvgInlineStyle(InFile, Elem, Warnings, State)

    # Remove any inheritable attributes (external scripts for pcb generation
    # can't inherit parameters so make them local). 

    SvgRemoveInheritableAttribs(InFile, Elem, Errors, Warnings, Info, State, InheritedAttributes, Level)

    # Remove any px from the font-size commands. 

    RemovePx(InFile, Elem, Info, Level)

    # Check for non supported font-family

    FontFamily = Elem.get('font-family')

    if not FontFamily == None and not FontFamily in ['DroidSans', "'DroidSans'", 'Droid Sans', "'Droid Sans'", 'OCRA', "'OCRA'"]:

        if not 'font.warning' in FzpDict:

            # Issue the warning then mark it as done so it only happens once
            # per file. 

            Warnings.append('Warning 24: File\n\'{0:s}\'\nAt line {1:s}\n\nFont family {2:s} is not Droid Sans or OCRA\nThis won\'t render in Fritzing\n'.format(str(InFile), str(Elem.sourceline), str(FontFamily)))

            FzpDict['font.warning'] = 'y'

        # End of if not 'font.warning' in FzpDict:

    # End of if not FontFamily == None and not FontFamily in ['DroidSans', "'Droid Sans'", "'OCRA'", 'OCRA']:

    # Check if this is a connector terminal definition
    # The str below takes care of comments which aren't a byte string and 
    # thus cause an exception. 

    Term = ConnectorTermRegex.search(str(Id))

    logging.debug (' ProcessSvgLeafNode: Term %s Tag %s\n', Term, Tag)
    
    if Term != None:

        # This looks to be a terminal definition so check it is a valid type.

        if Tag in ['path' , 'g']: 

            # Note one of the illegal terminalId types is present.

            Errors.append('Error 77: File\n\'{0:s}\'\nAt line {1:s}\n\nterminalId {2:s} can\'t be a {3:s} as it won\'t work.\n'.format(str(InFile), str(Elem.sourceline), str(Id), str(Tag)))

        # End of if Tag in ['path']: 

        # Since this is a terminal, check for height or width of 0 and complain
        # if so. 
            
        Height = Elem.get('height')
            
        Width = Elem.get('width')

        logging.debug (' ProcessSvgLeafNode: terminal %s height / width check height %s width %s\n', Id, Height, Width)

        if Height == '0':

            if ModifyTerminal == 'y':

                # Set the element to 10

                Elem.set('height', '10')

                # and log an error to warn the user we made a change that will 
                # affect the svg terminal position so they check it. 

                Error.append('Modified 2: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} had a zero height, set to 10\nCheck the alignment of this pin in the svg!\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

            else :

                Warnings.append('Warning 16: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} has a zero height\nand thus is not selectable in Inkscape\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

            # End of if ModifyTerminal == 'y':

            logging.debug (' ProcessSvgLeafNode: terminal %s 0 height warned or changed\n', Id)

        # End of if Height == '0':

        if Width == '0':

            if ModifyTerminal == 'y':

                # Set the element to 10 and issue an error so the user knows
                # to check the alignment of the terminal (which will have 
                # changed). 

                Elem.set('width', '10')

                Errors.append('Modified 2: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} had a zero width, set to 10\nCheck the alignment of this pin in the svg!\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

            else:

                Warnings.append('Warning 16: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} has a zero width\nand thus is not selectable in Inkscape\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

            # End of if ModifyTerminal == 'y':

            logging.debug (' ProcessSvgLeafNode: terminal %s issued\n', Id)

        # End of if Width == '0':
    
    # End of if Term != None:

    # End of if not 'connectors.svg.' + CurView in FzpDict:

    if Id != None and 'fzp' in FzpDict:

        # We are processing an svg from a fzp file so we can do more tests as 
        # we have connector and subpart data in the dict.

        # iconView doesn't have connectors so ignore it. 

        if CurView != None and CurView != 'iconView' and Id in FzpDict['connectors.fzp.' + CurView]:

            if not 'connectors.svg.' + CurView in FzpDict:
        
                # Doesn't exist yet so create it and add this connector.
        
                FzpDict['connectors.svg.' + CurView] = [Id]
        
                logging.debug (' ProcessSvgLeafNode: Created connectors.svg.%s and added %s to get %s\n', CurView, Id, FzpDict['connectors.svg.' + CurView])
        
            else:
        
                # Check for a dup connector. While Inkscape won't let you 
                # create one, a text editor or script generated part would ...
        
                if Id in FzpDict['connectors.svg.' + CurView]:
        
                    Errors.append('Error 66: File\n{0:s}\nAt line {1:s}\n\nConnector {2:s} is a duplicate (and should be unique)\n'.format(str(InFile), str(Elem.sourceline), str(Id)))
        
                else:
        
                    # not a dup, so append it to the list. 
        
                    FzpDict['connectors.svg.' + CurView].append(Id)
        
                    logging.debug (' ProcessSvgLeafNode: Appended %s to connectors.svg.%s to get %s\n', Id, CurView, FzpDict['connectors.svg.' + CurView])
        
                # End of if Id in FzpDict['connectors.svg.' + CurView]:

            # End of if not 'connectors.svg.' + CurView in FzpDict:

            if CurView == 'schematicView' and 'subparts' in FzpDict:

                # Get what should be the subpart tag from the tag stack

                if len(TagStack) > 2:
        
                    SubPartTag, StackLevel = TagStack[2]

                else:

                    SubPartTag = 'none'

                # End of if len(TagStack) > 2:

                logging.debug (' ProcessSvgLeafNode: SubPartTag %s\n', SubPartTag)

                if not 'subpartid' in State:

                    # no subpartID present at this time error.

                    Errors.append('Error 82: File\n\'{0:s}\'\nAt line {1:s}\n\nconnector {2:s} isn\'t in a subpart\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

                    logging.debug (' ProcessSvgLeafNode: subparts connector %s not in subpart\n', Id)

                else:

                    logging.debug (' ProcessSvgLeafNode: State[\'subpartid\'] %s SubPartTag %s\n', State['subpartid'], SubPartTag)
    
                    if not State['subpartid'] == SubPartTag:

                        if SubPartTag == 'none':

                            Errors.append('Error 82: File\n\'{0:s}\'\nAt line {1:s}\n\nconnector {2:s} isn\'t in a subpart\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

                            logging.debug (' ProcessSvgLeafNode: subparts connector %s not in subpart\n', Id)

                        else:

                            Errors.append('Error 83: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} shouldn\'t be in subpart {3:s} as it is\n'.format(str(InFile), str(Elem.sourceline), str(Id), str(SubPartTag)))

                            logging.debug (' ProcessSvgLeafNode: subparts connector %s not in correct subpart\n', Id)

                        # End of if SubPartTag == 'none':

                    elif Id in FzpDict[SubPartTag + '.subpart.cons']:

                        # Correct subpart so mark this connector as seen

                        FzpDict[SubPartTag + '.svg.subparts'].append(Id)

                        logging.debug (' ProcessSvgLeafNode: connector %s added to FzpDict[%s]\n', Id, SubPartTag + '.svg.subparts')

                    else:

                        Errors.append('Error 84: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} in incorrect subpart {3:s}\n'.format(str(InFile), str(Elem.sourceline), str(Id), str(SubPartTag)))

                        logging.debug (' ProcessSvgLeafNode: subparts connector %s in wrong subpart %s\n', Id, SubPartTag)

                    # End of if Id in FzpDict[SubPartTag + ',subpart.cons']:

                # End of if not 'subpartid' in State and not State['subpartid'] == SubPartTag:

            # End of if CurView == 'schematicView' and 'subparts' in FzpDict:

            if CurView == 'pcbView':

                # This is pcbView so check for connectors with ellipses instead
                # of circles

                # As this is only true for through hole parts and we don't yet
                # know if this part is through hole, put this in State for now
                # to be added to Errors only if this turns out to be a through
                # hole part later. 

                RadiusX = Elem.get('rx')

                if RadiusX != None:

                    if not 'hybridsetforpcbView' in State and 'copper0.layerid' in FzpDict and 'copper1.layerid' in FzpDict:

                        # pcb exists and has copper0 and copper1

                        Errors.append('Error 65: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} is an ellipse not a circle, (gerber generation will break.)\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

                    else:

                        State['noradius'].append('Error 65: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} is an ellipse not a circle, (gerber generation will break.)\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

                    # End of if not 'hybridsetforpcbView' in State and copper0.layerid' in FzpDict and 'copper1.layerid' in FzpDict:

                # End of if RadiusX != None:

                Radius = Elem.get('r')

                # As this is only true for through hole parts and we don't yet
                # know if this part is through hole, put this in State for now
                # to be added to Errors only if this turns out to be a through
                # hole part later. 

                if Radius == None:

                    if not 'hybridsetforpcbView' in State and 'copper0.layerid' in FzpDict and 'copper1.layerid' in FzpDict:

                        # pcb exists and has copper0 and copper1

                        Errors.append('Error 74: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} has no radius no hole will be generated\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

                    else:
        
                        # this is only an svg so we don't yet know if this is
                        # a through hole part yet so save the error message
                        # in State until we do.
            
                        State['noradius'].append('Error 74: File\n\'{0:s}\'\nAt line {1:s}\n\nConnector {2:s} has no radius no hole will be generated\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

                    # End of if not 'hybridsetforpcbView' in State and copper0.layerid' in FzpDict and 'copper1.layerid' in FzpDict:

                # End of if Radius != None:

            # End of if CurView == 'pcbView':

        # End of if Id in FzpDict['connectors.fzp' + CurView]:

        if CurView == 'schematicView' and 'subparts' in FzpDict:

            # We are in schematic and it has subparts so check they are 
            # correct.

            if Id in FzpDict['subparts']:

                logging.debug (' ProcessSvgLeafNode: Start of  subpart Id %s\n', Id)

                # Mark that we have seen a subpart label with (so far) no 
                # connectors

                if Id + '.svg.subparts' in FzpDict:

                    # Complain about a dup (although this shouldn't be able 
                    # to occur except via manual editing). 

                    logging.debug (' ProcessSvgLeafNode: subparts Id %s duplicate\n', Id)
                    Errors.append('Error 85: File\n\'{0:s}\'\nAt line {1:s}\n\nsubpart label {2:s} is already defined\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

                else:

                    # Create an empty list to contain the connectorids 
                    # for this label for later checking (to make sure they are
                    # all present). 

                    FzpDict[Id + '.svg.subparts'] = []

                    # Then record this subpartid in State for later connector
                    # ids. 

                    State['subpartid'] = Id

                    logging.debug (' ProcessSvgLeafNode: Create FzpDict[%s] and set state[\'subpartid\'] to %s\n', Id + '.svg.subparts', Id)

                # End of if Id + '.subparts' in FzpDict:

            # End of if Id in FzpDict['subparts']:

        # End of if CurView == 'schematicView' and 'subparts' in FzpDict:

    # End of if Id != None and 'fzp' in FzpDict:

    if not InheritedAttributes == None:

        # If there are inherited attributes step through them adding any
        # attributes that don't already exist. If the attribute is present
        # discard the inherited value. 

        SvgSetInheritedAttributes(InFile, Elem, InheritedAttributes)

    # End of if not InheritedAttributes == None:

    # Finally after all the attributes are set, search for font-size commands
    # and remove the trailing px (which Fritzing doesn't like) if it is present.

    RemovePx(InFile, Elem, Info, Level)

    # Then if this is group silkscreen, convert old style white silkscreen
    # (in all its forms) to new style black silkscreen. Warn about and 
    # modify items that are neither black nor white.

    if State['lastvalue'] == 'silkscreen':

        # Create the two color dictionaries

        ColorIsWhite = { 'white': 'y', 'WHITE': 'y', '#ffffff': 'y', '#FFFFFF': 'y', 'rgb(255, 255, 255)': 'y'}

        ColorIsBlack = { 'black': 'y', 'BLACK': 'y', '#000000': 'y', 'rgb(0, 0, 0)': 'y'}

        Stroke = Elem.get('stroke')

        if Stroke in ColorIsWhite:

            Elem.set('stroke', '#000000')

            # Change any non black color to black. 

            Info.append('Modified 3: File\n\'{0:s}\'\nAt line {1:s}\n\nSilkscreen, converted stoke from white to black\n'.format(str(InFile), str(Elem.sourceline)))

        elif not (Stroke == None or Stroke == 'none' or Stroke in ColorIsBlack):

            Info.append('Modified 3: File\n\'{0:s}\'\nAt line {1:s}\n\nSilkscreen stroke color {2:s} isn\'t white or black. Set to black.\n'.format(str(InFile), str(Elem.sourceline), str(Stroke)))

            Elem.set('stroke', '#000000')

        # End of if Stroke in ColorIsWhite:

        Fill = Elem.get('fill')

        if Fill in ColorIsWhite:

            # If the color is currently white or not black set it to black.

            Info.append('Modified 3: File\n\'{0:s}\'\nAt line {1:s}\n\nSilkscreen, converted fill from white to black\n'.format(str(InFile), str(Elem.sourceline)))

            Elem.set('fill', '#000000')

        elif not (Fill == None or Fill == 'none' or Fill in ColorIsBlack):

            # If the current color is neither white nor black (but not none),
            # tell the user so but otherwise ignore it.

            Info.append('Modified 3: File\n\'{0:s}\'\nAt line {1:s}\n\nSilkscreen fill color {2:s} isn\'t white or black. Set to black.\n'.format(str(InFile), str(Elem.sourceline), str(Fill)))

            Elem.set('fill', '#000000')

        # end of if Fill in ColorIsWhite:

    # End of if State['lastvalue'] == 'silkscreen':

    logging.debug ('  ProcessSvgLeafNode: State %s\n', State)

    logging.info (' Exiting ProcessSvgLeafNode Level %s\n', Level)

# End of def ProcessSvgLeafNode(FzpType, InFile, CurView, PrefixDir, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, InheritedAttributes, Level):

def SvgStartElem(InFile, Elem, Errors, Warnings, Info, State, Level):

    logging.info (' Entering SvgStartElem Level %s\n', Level)

    NumPxRegex = re.compile(r'\d$|px$', re.IGNORECASE)

    Tag = Elem.tag

    if Tag == '{http://www.w3.org/2000/svg}svg' or Tag == 'svg':
    
        if 'SvgStart' in State:

            Warnings.append('Warning 17: File\n\'{0:s}\'\nAt line {1:s}\n\nMore than one svg tag found\n'.format(str(InFile), str(Elem.sourceline)))
    
        # End of if 'SvgStart' in State:

        # Mark that we have seen the start tag for later. 

        State['SvgStart'] = 'y'

        Height = Elem.get('height')

        Width = Elem.get('width')

        # Check for either a bare number or numberpx as the height or width.

        logging.debug (' SvgStartElem: Height %s Width %s\n',Height, Width)

        if Height == None:

            Warnings.append('Warning 18: File\n\'{0:s}\'\nAt line {1:s}\n\nHeight attribute missing\n'.format(str(InFile), str(Elem.sourceline)))

        else:

            Units = NumPxRegex.search(str(Height))

            logging.debug (' SvgStartElem: Height units %s\n', Units)

            if Units != None:

                Warnings.append('Warning 19: File\n\'{0:s}\'\nAt line {1:s}\n\nHeight {2:s} is defined in px\nin or mm is a better option (px can cause scaling problems!)\n'.format(str(InFile), str(Elem.sourceline), str(Height)))

            # End of if Height != None:

        # End of if Height = None:

        if Width == None:

            Warnings.append('Warning 18: File\n\'{0:s}\'\nAt line {1:s}\n\nWidth attribute missing\n'.format(str(InFile), str(Elem.sourceline)))

        else:

            Units = NumPxRegex.search(str(Width))

            logging.debug (' SvgStartElem: Width units %s\n', Units)

            if Units != None:

                Warnings.append('Warning 19: File\n\'{0:s}\'\nAt line {1:s}\n\nWidth {2:s} is defined in px\nin or mm is a better option (px can cause scaling problems!)\n'.format(str(InFile), str(Elem.sourceline), str(Width)))

            # End of if Units != "":

        # End of if Width = None:

    else:
    
        if not 'SvgStart' in State:

            Errors.append('Error 67: File\n\'{0:s}\'\nAt line {1:s}\n\nFirst Tag {2:s} isn\'t an svg definition\n\n'.format(str(InFile), str(Elem.sourceline), str(Tag)))

            # then set 'SvgStart' so we don't repeat this warning.

            State['SvgStart'] = 'y'
    
        # End of if not 'SvgStart' in State:

    # End of if Tag == '{http://www.w3.org/2000/svg}svg':

    logging.info (' Exiting SvgStartElem Level %s\n', Level)

# End of def SvgStartElem(InFile, Elem, Errors, Warnings, Info, State, Level):

def SvgRefFile(FzpType, InFile, Elem, Errors, Warnings, Info, State, Level):

    logging.info (' Entering  SvgRefFile Line %s Level %s\n', Elem.sourceline, Level)

    logging.debug (' SvgRefFile: FzpType %s InFile %s\n', FzpType, InFile)
   
    SvgRegex = re.compile(r'^svg\.\w+\.', re.IGNORECASE)
    
    # Check if this is a referenceFile definition.

    Tag = Elem.tag

    logging.debug (' SvgRefFile: Tag %s\n',Tag)

    if Tag != '{http://www.w3.org/2000/svg}referenceFile':

        # No, so return.

        logging.debug (' SvgRefFile: not reference file, returning\n')

        return

    # End of if ReferenceFile == None:

    # This is the reference file so get the input file name (minus the path)

    File = os.path.basename(InFile)

    # Remove the trailing .bak if it is present.

    File = re.sub(r'\.bak$','', File)

    logging.debug (' SvgRefFile: File %s\n', File)

    if FzpType == 'fzpPart':

        # This is a part. type file so remove the "svg." from the
        # file name before the compare.

        File = SvgRegex.sub('', File)

        logging.debug (' SvgRefFile: Corrected file %s\n', File)

    # End of if FzpType == 'fzpPart':

    if Elem.text != File:

        # They don't match, so correct it (and log it).

        Info.append('Modified 4: File\n\'{0:s}\'\nAt line {1:s}\n\nReferenceFile\n\n\'{2:s}\'\n\ndoesn\'t match input file\n\n\'{3:s}\'\n\nCorrected\n'.format(str(InFile), str(Elem.sourceline), str(Elem.text), str(File)))

        Elem.text = File

        logging.debug (' SvgRefFile: set reference file to %s\n',Elem.text)

    # End of if ReferenceFile != File:

# End of def SvgRefFile(FzpType, InFile, Elem, Errors, Warnings, Info, State, Level):

def SvgCheckForLayerId(Tag, InFile, CurView, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering SvgCheckForLayerId Level %s\n', Level)

    logging.debug(' SvgCheckForLayerId: On entry Tag %s TagStack %s State %s\n', Tag, TagStack, State)

    # Check we have seen a svg definition and a layerId before the first 
    # drawing element. Ignore iconview because it doesn't matter as it isn't
    # processed by Fritzing. 

    if CurView != 'iconView' and not 'SvgFirstGroup' in State and Tag in ['rect', 'line', 'text', 'polyline', 'polygon', 'path', 'circle', 'ellipse', 'tspan']:

        if not 'SvgStart' in State:

            # If we haven't seen the svg definition flag an error.

            Errors.append('Error 68: File\n\'{0:s}\'\nAt line {1:s}\n\nFound first group but without a svg definition\n'.format(str(InFile), str(Elem.sourceline)))

        # End of if not 'SvgStart' in State:

        # Mark that we have seen a drawing element

        State['SvgFirstGroup'] = 'y'

        logging.debug(' SvgCheckForLayerId: line %s Tag %s found starting tag\n', Elem.sourceline, Tag)
        
        if CurView != 'iconView' and 'SvgFirstGroup' in State and not 'LayerId' in State:

            logging.debug(' SvgCheckForLayerId: drawing element before layerid State %s\n', State)

            # Complain about a drawing element before a layerId

            Errors.append('Error 69: File\n\'{0:s}\'\nAt line {1:s}\n\nFound a drawing element before a layerId (or no layerId)\n'.format(str(InFile), str(Elem.sourceline)))

        # End of if 'SvgFirstGroup' in State and not 'LayerId' in State:
                
    # End of if not 'SvgFirstGroup' in State and Tag in ['rect', 'line', 'text', 'polyline', 'polygon', 'path', 'circle', 'ellipse', 'tspan']:

    logging.info (' Exiting SvgCheckForLayerId Level %s\n', Level)

# End of def SvgCheckForLayerId(Tag, InFile, CurView, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def SvgCheckCopperTransform(Id, Transform, State, Level):

    logging.info (' Entering SvgCheckCopperTransform Level %s\n', Level)

    if Transform != None:

        State[Id + '_trans'] = Transform

    else:

        State[Id + '_trans'] = ''

    # End of if Transform != None:

    logging.debug(' SvgCheckCopperTransform: returned %s \'%s\'\n', Id + '_trans', State[Id + '_trans'])

    logging.info (' Exiting SvgCheckCopperTransform Level %s\n', Level)

# End of def SvgCheckCopperTransform(Id, Transform, State, Level):

def SvgPcbLayers(Id, InFile, CurView, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering SvgPcbLayers Level %s\n', Level)

    logging.debug (' Entering SvgPcbLayers State %s\n', State)

    StackTag, StackLevel = TagStack[len(TagStack) - 1]

    # get the first Fritzing tag to BaseTag

    if len(TagStack) > 1:

        BaseTag, StackLevel = TagStack[1]

    else:

        BaseTag = ''

    # End of if len(TagStack) > 1:

    if Id == 'silkscreen':

        if 'seensilkscreen' in State:

            # Already seen is an error. 

            Errors.append('Error 70: File\n\'{0:s}\'\nAt line {1:s}\n\nMore than one silkscreen layer\n'.format(str(InFile), str(Elem.sourceline)))

            logging.debug (' SvgPcbLayers: Already seen silkscreen State %s\n', State)

        else:

            # mark it as seen for the future.

            State['seensilkscreen'] = 'y'

            logging.debug (' SvgPcbLayers: Mark seen silkscreen State %s\n', State)

            # If we have already seen a copper layer issue a warning as that 
            # makes selection in pcb more difficult. 

            if 'seencopper0' in State or 'seencopper1' in State:

                Warnings.append('Warning 25: File\n\'{0:s}\'\nAt line {1:s}\n\nSilkscreen layer should be above the copper layers for easier selection\nin pcb view\n'.format(str(InFile), str(Elem.sourceline)))

            # End of if 'seencopper0' in State or 'seencopper1' in State:

        # End of if 'seensilkscreen' in State:
            
        if len(TagStack) != 2:

            # Not at the top layer is an error. 

            Errors.append('Error 71: File\n\'{0:s}\'\nAt line {1:s}\n\nSilkscreen layer should be at the top, not under group {2:s}\n'.format(str(InFile), str(Elem.sourceline), str(BaseTag)))
            
        # End of if len(TagStack) != 2:

    # End of if Id == 'silkscreen':

    if Id == 'copper1':

        if 'seencopper1' in State:

            Errors.append('Error 70: File\n\'{0:s}\'\nAt line {1:s}\n\nMore than one copper1 layer\n'.format(str(InFile), str(Elem.sourceline)))

            logging.debug (' SvgPcbLayers: Already seen copper1 State %s\n', State)

        else:

            # mark it as seen for the future.

            State['seencopper1'] = 'y'

            logging.debug (' SvgPcbLayers: Mark seen copper1 State %s\n', State)

        # End of if 'seencopper1' in State:

        if len(TagStack) != 2:

            # Not at the top layer is an error but not fatal. 

            Warnings.append('Warning 20: File\n\'{0:s}\'\nAt line {1:s}\n\ncopper1 layer should be at the top, not under group {2:s}\n'.format(str(InFile), str(Elem.sourceline), str(BaseTag)))

        # End of if len(TagStack) != 2:

    # End of if Id == 'copper1':

    if Id == 'copper0':

        if 'seencopper0' in State:

            Errors.append('Error 70: File\n\'{0:s}\'\nAt line {1:s}\n\nMore than one copper0 layer\n'.format(str(InFile), str(Elem.sourceline)))

            logging.debug (' SvgPcbLayers: Already seen copper0 State %s\n', State)

        else:

            # mark it as seen for the future.

            State['seencopper0'] = 'y'

            logging.debug (' SvgPcbLayers: Mark seen copper0 State %s\n', State)

        # End of if 'seencopper0' in State:

        if len(TagStack) == 2 and 'seencopper1' in State:

            # Not under copper1 is an error (this is the same level as copper1) 

            Errors.append('Error 72: File\n\'{0:s}\'\nAt line {1:s}\n\ncopper0 should be under copper1 not the same level\n'.format(str(InFile), str(Elem.sourceline)))

        elif len(TagStack) > 3:

            # too many layers is an error.

            Errors.append('Error 73: File\n\'{0:s}\'\nAt line {1:s}\n\nToo many layers, there should only be copper1 then copper0\n'.format(str(InFile), str(Elem.sourceline)))

        # End of if len(TagStack) == 3 and 'seencopper1' in State:

    # End of if Id == 'copper0':

    logging.info (' Exiting SvgPcbLayers Level %s\n', Level)

# End of def SvgPcbLayers(Id, InFile, CurView, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def SvgCheckPcbLayers(InFile, Errors, Warnings, Info, FzpDict, TagStack, State):

    logging.info (' Entering SvgCheckPcbLayers\n')

    # This is only an svg file (we haven't seen the associated fzp)
    # so determine if this is likely SMD and if not output the no
    # hole messages in State and set SMD or Through hole in Info.

    logging.debug (' SvgCheckPcbLayers: No fzp file State %s\n', State)

    if 'seencopper0' in State and 'seencopper1' in State:

        # This is a through hole part so note that in Info and 
        # copy any no radius error messages to Errors. 

        Info.append('File\n\'{0:s}\'\n\nThis is a through hole part as both copper0 and copper1 views are present.\n'.format(str(InFile)))


        if State['noradius'] != '':

            # We have seen holes without a radius (which is normal for 
            # smd parts but an error in through hole) so report them 
            # by moving them from State in to Errors.

            for Message in State['noradius']:

                Errors.append(Message)

            # End of for Message in State['noradius']:

        # End of if State['noradius'] != '':

    elif 'seencopper1' in State:

        # This appears to be a normal SMD part so note that in Info.

        Info.append('File\n\'{0:s}\'\n\nThis is a smd part as only the copper1 view is present.\n'.format(str(InFile)))

    elif 'seencopper0' in State:

        # This appears to be a SMD part but on the bottom of the board
        # so note that in Errors.

        Errors.append('Error 75: File\n\'{0:s}\'\n\nThis is a smd part as only the copper0 view is present\nbut it is on the bottom layer, not the top.\n\n'.format(str(InFile)))

    elif 'seensilkscreen' in State:

        # This appears to be only a silkscreen so note that in Info.

        Info.append('File\n\'{0:s}\'\n\nThis is an only silkscreen part as has no copper layers present.\n'.format(str(InFile)))

    else:

        Warnings.append('Warning 21: File\n\'{0:s}\'\n\nThis appears to be a pcb svg but has no copper or silkscreen layers!\n'.format(str(InFile)))

    # End of if 'seencopper0' in State and 'seencopper1' in State:

    logging.info (' Exiting SvgCheckPcbLayers\n')

# End of def SvgCheckPcbLayers(InFile, Errors, Warnings, Info, FzpDict, TagStack, State):

def SvgGroup(InFile, CurView, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

    logging.info (' Entering SvgGroup Level %s\n', Level)

    logging.debug(' SvgGroup: On entry Errors: %s CurView %s TagStack %s State %s\n', Errors, CurView, TagStack, State)

    TspanRegex = re.compile(r'^tspan', re.IGNORECASE)

    NameSpaceRegex = re.compile(r'{.+}')

    # First get the tag to see if we are past the boiler plate and have seen
    # the initial group that starts the actual svg (so we can search for the
    # layerid before any constructs). 

    Tag = Elem.tag

    # Remove the namespace attribute from the tag

    Tag = NameSpaceRegex.sub('', str(Tag))

    Id =  Elem.get('id')
    
    logging.debug(' SvgGroup: Entry Id %s TagStack %s\n', Id, TagStack )

    if Id != None:

        # We have a tag value so pop the tag stack if needed.

        PopTag(TagStack, Level)

    # End of if Id != None:

    # Check for a Fritzing layerid and record we have seen it.

    if CurView == None:

        # This isn't from an fzp file so we don't have a layerid list to 
        # compare against. So see if this is likely a layerId (this will 
        # sometimes false error when a layerId is nonstandard). In addition
        # keep track of tspan ids to check for nested tspans which fritzing
        # doesn't support. Hopefully they will not occur in areas where the
        # tag stack values are checked (they shouldn't, but you never know)

        if Id in ['breadboard', 'icon', 'schematic', 'silkscreen', 'copper0', 'copper1'] or TspanRegex.match(str(Id)):
    
            # Push the Id and Level on to the tag stack.

            TagStack.append([Id, Level])

            if TspanRegex.match(str(Id)):

                # This is a tspan, so check if the last was as well.

                if TspanRegex.match(str(State['lastvalue'])):

                    # Nested tspan which fritzing doesn't support so issue a
                    # warning. 

                    Warnings.append('Warning 26: File\n\'{0:s}\'\nAt line {1:s}\n\nApparant nested tspan which fritzing doesn\'t support\nIf your text doesn\'t appear in Fritzing this is probably why\n'.format(str(InFile), str(Elem.sourceline)))

                # End of if TspanRegex.match(str(State['lastvalue'])):

            else:

                # This isn't a tspan element so check it the tag is a group 
                # and issue a warning if it is not. 

                if not Tag == 'g':

                    Warnings.append('Warning 27: File\n\'{0:s}\'\nAt line {1:s}\n\nFritzing layerId {2:s} isn\'t a group which it usually should be\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

                # End of if not Tag == 'g':

            # End of if re.match(r'^tspan', str(Id)) and re.match(r'^tspan', str(State['lastvalue'])):
    
            # Set the current layer in to State['lastvalue']
        
            State['lastvalue'] = Id
    
            if Id in ['silkscreen', 'copper0', 'copper1']:

                # Mark that this appears to be a pcb svg in State.

                State['pcbsvg'] = 'y'

                # Then check that the layers are in the correct order.

                SvgPcbLayers(Id, InFile, CurView, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)

            else:

                logging.debug(' SvgGroup: before test State %s\n', State)

                # If this Id is tspan, it isn't a layerid so don't trip the 
                # too many layerids warning. 

                if not TspanRegex.match(str(Id)) and 'LayerId' in State:

                    # Single layerId case, but more than one layerId. 

                    Warnings.append('Warning 22: File\n\'{0:s}\'\nAt line {1:s}\n\nAlready have a layerId\n'.format(str(InFile), str(Elem.sourceline)))
    
                    logging.debug(' SvgGroup: Warning dup layer issued\n')

                # End of if 'LayerId' in State:

            # End of if Id in ['silkscreen', 'copper0', 'copper1']:
    
            # and note we have seen a LayerId in State for later.
   
            State['LayerId'] = 'y'

        # End of if Id in ['breadboard', 'icon', 'schematic', 'silkscreen', 'copper0', copper1']:

    else:

        # We are processing svgs from an fzp and have a FzpDict with a list
        # of expected layers.

        if CurView != 'pcbView':

            if CurView == 'schematicView' and 'subparts' in FzpDict:

                # We are in a schematic svg that has subparts so check if this
                # is a subpart id and add it to the tag stack if so. 

                logging.debug(' SvgGroup: CurView %s subparts %s\n', CurView, FzpDict['subparts'])

                if Id in FzpDict['subparts']:

                    # Check that schematic is the only thing above this on 
                    # the tag stack and issue a warning if that isn't true.

                    if len(TagStack) != 2:

                        logging.debug(' SvgGroup: TagStack len %s not top level warning issued\n', len(TagStack))

                        Errors.append('Error 86: File\n\'{0:s}\'\nAt line {1:s}\n\nSubpart {2:s} isn\'t at the top level when it must be\nFollowing subpart errors may be invalid until this is fixed\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

                    # End of if len(TagStack) != 2:

                    logging.debug(' SvgGroup: subpart %s found and added\n', Id)
    
                    # Push the Id and Level on to the tag stack.

                    TagStack.append([Id, Level])
    
                    # Set the current layer in to State['lastvalue']
        
                    State['lastvalue'] = Id

                # End of if Id in FzpDict['subparts']:

            # End of if CurView == 'schematicView' and 'subparts' in FzpDict:

            # Only one layerid so check for it.

            logging.debug(' SvgGroup: CurView %s LayerId %s\n', CurView, FzpDict[CurView + '.LayerId'])

            if Id == FzpDict[CurView + '.LayerId']:

                # Push the Id and Level on to the tag stack.

                TagStack.append([Id, Level])

                if 'LayerId' in State:

                    # More than one layerid warning. 

                    Warnings.append('Warning 25: File\n\'{0:s}\'\nAt line {1:s}\n\nAlready have a layerId\n'.format(str(InFile), str(Elem.sourceline)))

                else:
    
                    # and note we have seen a LayerId in State for later.
       
                    State['LayerId'] = 'y'
    
                    # Set the current layer in to State['lastvalue']
        
                    State['lastvalue'] = Id
        
                    logging.debug(' SvgGroup: set State[\'view\'] to %s\n', Id)

                # End of if 'LayerId' in State:

                # Issue a warning if the layerId isn't a group. 

                if not Tag == 'g':

                    Warnings.append('Warning 27: File\n\'{0:s}\'\nAt line {1:s}\n\nFritzing layerId {2:s} isn\'t a group which it usually should be\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

                # End of if not Tag == 'g':

            # End of if Id == FzpDict[CurView + '.LayerId']:

        else:

            # This is pcbView so the LayerIds are a list, and life is more 
            # complex. For layerids other than copper0 and copper1, they must
            # be at the top of the tagstack (not under another layerid). If 
            # both copper0 and copper1 are present the order should be copper1 
            # copper0 so smd parts are by default on the top layer. So warn
            # about copper1 under copper0 and error for copper0 and copper1 on
            # the same level. 

            logging.debug(' SvgGroup: %s Curview %s LayerIds %s\n', Id, CurView, FzpDict[CurView + '.LayerId'])
    
            if Id in FzpDict[CurView + '.LayerId']:
    
                # Push the Id and Level on to the tag stack.

                TagStack.append([Id, Level])
    
                logging.debug(' SvgGroup: pushed %s on to tag stack\n', Id)
    
                # and note we have seen the LayerId in State for later.
    
                State['LayerId'] = 'y'
    
                State[CurView + 'LayerId'] = 'y'
    
                # Set the current layer in to State['lastvalue']
    
                State['lastvalue'] = Id

                SvgPcbLayers(Id, InFile, CurView, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level)
    
                logging.debug(' SvgGroup: set State[\'view\'] to %s\n', Id)

                # Issue a warning if the layerId isn't a group. 

                if not Tag == 'g':

                    Warnings.append('Warning 27: File\n\'{0:s}\'\nAt line {1:s}\n\nFritzing layerId {2:s} isn\'t a group which it usually should be\n'.format(str(InFile), str(Elem.sourceline), str(Id)))

                # End of if not Tag == 'g':
    
            # End of if Id in FzpDict[CurView + '.LayerId']:

        # End of if CurView == None:

        if Id in ['copper0', 'copper1']:

            # If this is copper0 or copper1, check for a transform as a 
            # transform in one but not the other is an error.

            Transform = Elem.get('transform')

            SvgCheckCopperTransform(Id, Transform, State, Level)

        # End of if Id in ['copper0', 'copper1']:

        if 'copper0' in TagStack and 'copper1' in TagStack and State['copper0_trans'] != State['copper1_trans']:

            # We have seen both coppers and they doesn't have  
            # identical transforms so set an error. 

            Errors.append('Error 76: File\n\'{0:s}\'\nAt line {1:s}\n\nCopper0 and copper1 have non identical transforms (no transforms is best)\n'.format(str(InFile), str(Elem.sourceline)))

            logging.debug(' SvgGroup: set copper transform error\n')

       # End of if 'copper0' in TagStack and 'copper1' in TagStack and State['copper0_trans'] != State['copper1_trans']:

    # End of if CurView == None:

    logging.debug(' SvgGroup: On exit Errors %s CurView %s TagStack %s len tagstack %s State %s\n', Errors, CurView, TagStack, len(TagStack), State)

    logging.info (' Exiting SvgGroup Level %s\n', Level)

# End of def SvgGroup(InFile, CurView, Elem, Errors, Warnings, Info, FzpDict, TagStack, State, Level):

def SvgInlineStyle(InFile, Elem, Warnings, State):

    # If there is a style command in the attributes, convert it to inline
    # xml (overwriting current values if present). 
    
    logging.info (' Entering SVGInlineStyle\n')

    # Get the current style values if any

    ElemAttributes = Elem.get('style')

    if not ElemAttributes == None: 

        # Delete the current style attribute

        logging.debug (' SVGInlineStyle: delete style: %s\n', ElemAttributes)

        Elem.attrib.pop("style", None)

        # Then add the elements back in inline (replacing current values if 
        # present, as style should overide inline values usually). 

        Attributes = ElemAttributes.split(';')

        logging.debug (' SVGInlineStyle: attributes %s line %s\n', Attributes, Elem.sourceline)

        for Attribute in Attributes:

            KeyValue = Attribute.split (':')

            # Then set the pair as attribute=value

            logging.debug (' SVGInlineStyle: attribute %s key len %s key[0] %s\n', Attribute, str(len(KeyValue)), KeyValue[0])

            if len(KeyValue) == 2:

                # The attribute has a value so set it. At least one file has
                # a trailing ';' without a tag / value pair which breaks here
                # if this test isn't made. Probably invalid xml but harmless.

                try:
                
                    Elem.set(KeyValue[0], KeyValue[1])

                except ValueError:

                    # This is typically an atribute like
                    # -inkscape-font-specification 'Droid Sans, Normal'
                    # or the previously mentioned trailing ";" and won't be
                    # missed (it is logged here in case there is something
                    # important being deleted at some time!)

                    if not KeyValue[0] in State['KeyErrors']:

                        logging.debug (' SVGInlineStyle: KeyValue\[0\] %s State %s\n', KeyValue[0], State)

                        # Haven't seen this one yet so log it.

                        Warnings.append('Warning 23: File\n\'{0:s}\'\nAt line {1:s}\n\nKey {2:s}\nvalue {3:s} is invalid and has been deleted\n'.format(str(InFile), str(Elem.sourceline), str(KeyValue[0]),  str(KeyValue[1])))

                        # Then add it to State to ignore more of them

                        State['KeyErrors'].append(KeyValue[0])

                        logging.debug (' SVGInlineStyle: attribute %s %s is invalid, deleted\n', KeyValue[0], KeyValue[1])

                    # End of if not KeyValue[0] in State['KeyErrors']:

                # End of try

            # End of if len(KeyValue) == 2:

        # End of for Attribute in Attributes:

    # end of if not ElemAttributes == None: 

    logging.info (' Exiting SvgInlineStyle\n')

# End of def SvgInlineStyle(InFile, Elem, Warnings, State):

def SvgRemoveInheritableAttribs(InFile, Elem, Errors, Warnings, Info, State, InheritedAttributes, Level):

    # Some part of Fritzing (probably the script to produce the gerber output)
    # does't deal with inheritance. The case that drove this change (and the
    # only translation currently being done) is to save the svg in Inkscape
    # as optimized svg (rather than plain) at which point the stroke-width
    # attribute is optimized in to copper0 or copper1 top Level and inherited.
    # The output geber missing the stroke-width parameter outputs an oversize
    # nonplated through hole. To fix that we copy the stroke length in to
    # the leaf nodes of all elements of copper0 or copper1 which should fix
    # the problem and allow us to use optimised svg in Inkscape.

    logging.info (' Entering SvgRemoveInheritableAttribs Level %s State[\'lastvalue\'] %s\n', Level, State['lastvalue'])

    if not (State['lastvalue'] == 'copper0' or State['lastvalue'] == 'copper1'):

        # Not in a pcb copper layer so don't do anything. 

        logging.debug(' Exiting SvgRemoveInheritableAttribs unchanged not pcb group\n')

        return

    # End of if not (State['lastvalue'] == 'copper0' or State['lastvalue'] == 'copper1'):

    # First Convert any style command to inline xml

    SvgInlineStyle(InFile, Elem, Warnings, State)

    # Then see if we have a stroke-width

    StrokeWidth = Elem.get('stroke-width')

    if StrokeWidth != None:

        # Overwrite any previous value with the current value. 

        InheritedAttributes = 'stroke-width:' + StrokeWidth

    # End of if StrokeWidth != None:

    logging.debug(' Exiting SvgRemoveInheritableAttribs set InheritedAttributes to %s\n', StrokeWidth)

    logging.info (' Exiting SvgRemoveInheritableAttribs Level %s\n', Level)

# End of def SvgRemoveInheritableAttribs(InFile, Elem, Errors, Warnings, Info, State, InheritedAttributes, Level):

def SvgSvgSetInheritedAttributes(InFile, Elem, InheritedAttributes):

    # Some part of Fritzing (probably the script to produce the gerber output)
    # can't deal with inheritance. The case that drove this change (and the
    # only translation currently being done) is to save the svg in Inkscape
    # as optimized svg (rather than plain) at which point the stroke-width 
    # attribute is optimized in to copper0 or copper1 top level and inherited.
    # The output geber missing the stroke-width parameter outputs an oversize
    # nonplated through hole. To fix that we copy the stroke length in to 
    # the leaf nodes of all elements of copper0 or copper1 which should fix
    # the problem and allow us to use optimised svg in Inkscape.

    logging.info (' Entering SvgSetInheritedAttributes\n')

    Info.append('Modified 5: File\n\'{0:s}\'\nAt line {1:s}\n\nConverted style to inline xml\n'.format(str(InFile), str(Elem.sourceline)))

    logging.debug ('SvgSetInheritedAttributes: Elem attributes on entry %s InheritedAttributes %s\n', Elem.attrib, InheritedAttributes)

    attributes = InheritedAttributes.split(';')

    for attribute in attributes:

        KeyValue = attribute.split(':')

        if not Elem.get(KeyValue[0]):

            # if the key doesn't currently exist then add it and its 
            # associated value. 

            logging.debug (' SvgSetInheritedAttributes: Set new element key %s to inherited attribute value: %s\n', KeyValue[0], KeyValue[1])

            Elem.set(KeyValue[0], KeyValue[1])

    logging.debug (' SvgSetInheritedAttributes: At end Elem attributes %s\n', Elem.attrib)

    logging.info (' Exiting SvgSetInheritedAttributes\n')

# End of def SvgSetInheritedAttributes(InFile, Elem, InheritedAttributes):

