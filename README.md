
Description:

	FritzingCheckPart.py is a python script which checks parts files for
use by the Fritzing EDA program (fritzing.org). It started out to correct 
some of the issues that Fritzing has with the output from the Inkscape 
(inkscape.org) open source svg editor program. It then grew in to checking the
format of the various file (fzp and svg) that make up a fritzing part. 
	As a part of that it also prettyprints xml (with varying success), it 
does best with postprocessed fritzing svg files, because it understands their
format and has modified the xml (mostly moving CSS style commands in to inline
xml which as a side effect makes prettyprinting easier), to better suit 
fritzing. A standalone script PP.py, is included which will prettyprint a 
xml document without doing any of the fritzing related conversions.

Installation:

	The script uses python3 and the lxml library extensions to python.
Since Fritzing runs on Windows, linux and MacOS X the script should run on
those platforms too, and it may. I don't have MacOS X so I don't know that 
it will run there (although there is no reason that it shouldn't, I just
haven't done it.)

On Windows:

	I run the script from cygwin on Windows. It will likely run on one of
the native python implementations (you may need to use pip to install the lxml
extension) but I haven't done so. For cygwin you need to install cygwin 
(cygwin.org) using the setup program as detailed on cygwin.org. The basic 
install with the following additions does fine:

python3: Py3K language interpreter 
python3-lxml: Python XML2/XSLT bindings 

(and all their associated dependencies)

with that in place from a cygwin terminal copy the python scripts 

FritzingCheckPart.py
FritzingTools.py
PP.py
PPTools.py

to /usr/local/bin

chmod ugo+x /usr/local/bin/*.py

On Linux (Ubuntu 16.04 LTS):

copy the py scripts to /usr/local/bin via sudo:

sudo cp FritzingCheckPart.py /usr/local/bin 
sudo cp FritzingTools.py /usr/local/bin 
sudo cp PP.py /usr/local/bin 
sudo cp PPTools.py /usr/local/bin 

chmod ugo+x /usr/local/bin/*.py

The Ubuntu install appears to have lxml and python 3 already installed 

Note the script has problems with unicode under python 2.7 and probably won't
run there without modification (which I don't know how to make). 

Testing:

Assuming you have Fritzing installed the following will check (and complain
about!) the parts in core:

mkdir tst

FritzingCheckPart.py fritzing-0.9.3b.linux.AMD64/fritzing-parts/core tst

(replace the fritzing-0.9.3b.linux.AMD64/fritzing-parts/core with the path
 to your fritzing-parts core directory!)

which should produce output like this (in large volume) on the console:


**** Starting to process file 10x2-Epaper-Breakout-Board-v11.fzp


Error: File
'/cygdrive/c/fritzing/fritzing.0.9.3b.64.pc/fritzing.0.9.3b.64.pc/fritzing-parts/core/10x2-Epaper-Breakout-Board-v11.fzp'

Connector0 doesn't exist (connectors should start at 0)

...


Normal use:

PrettyPrinting:

PP.py xml_file [another_xml_file ...]

will pretty print the xml file to xml_file leaving the original file in 
xml_file.bak internally it sets the file type to svg so that it will split
blanks in lines such as attribute="value" attribute="value" in to 

attribute="value"
attribute="value"

with appropriate indenting. Since this is meant for post processed Fritzing 
svg file it may or may not do what you want. So try it and see. It won't 
split on blanks in text or quoted strings but may screw up on general xml 
sometimes, so use it if it is useful. 

FritzingCheckPart.py

There are several modes (selected internally by the number and type of 
the arguments to the script.):

1)

dir to dir:

FritzingCheckPart.py src_dir dst_dir

This processes all the fritzing files it finds in src_dir and writes their 
output in to dst_dir. Dst_dir needs to be empty to avoid damaging existing 
files. Subdirectories to match the fritzing file set up will be created in
the dst_dir. If you are processing part.fzp type files the output will go 
in to dst_dir at the top level and the svg and subdirectories will remain
empty. In the case of core in the example above the identical directory 
format will be recreated under dst_dir. To run this a second time you need
to empty the dst_dir via command like 

rm -R dst_dir/*

This is mostly used for testing (against core as a source of diverse files, 
many with errors) and to allow a mass correction of core if desired. Note 
you only want to run this mode against core as the other modes will change
files in core that are under git control and tend to break Fritzing. 

2)

FritzingCheckPart.py part.filename.fzp

part.filename.fzp format (from an unzipped .fzpz file which will have files
of the form 

part.filename.fzp
svg.breadboard.filename.svg
svg.icon.filename.svg
svg.schematic.filename.svg
svg.pcb.filename.svg

The input files will be renamed to filename.bak with the script output, the
fixed up (we hope) xml, written to the original file name ready to be rezipped
and loaded to fritzing. If something goes wrong, the original data is in the
.bak files (so long as you haven't run the script twice). First the fzp file
will be processed to get the connector information and the expected svg files,
then each svg file in turn will be processed. So you need to pay attention to 
the file name in the error messages, as it may not be referring to the input
file, but an svg file linked from the input file. 

3)

FritzingCheckPart.py parts/user/filename.fzp

the input file is in directory user/filename.fzp (and the user in the path 
is required to be present, the script will error out if it is not). The svg 
files are in 

user/svg/user/breadboard/filename.svg
user/svg/user/icon/filename.svg
user/svg/user/pcb/filename.svg
user/svg/user/schematic/filename.svg

which is the standard place where imported parts are stored by fritzing (in 
the core exampe at the start of this, the "core" directory is the same as 
"user" here). Again the fzp file will be processed followed by the associated
svgs. So again you need to pay attention to the file name in the error 
messages, as it may not be referring to the input file, but an svg file 
linked from the input file. 

4)

FritzingCheckPart.py filename.svg

this form does what checks it can on the svg file (which aren't that many as 
it lacks the data from the fzp file to know what connectors it should be 
checking for). What it does do is the original purpose of this script which
is to change the style(attribute:value;attirbute:value) commands to the 
equivelent inline xml attirbute="value" attribute="value" as parts 
of fritzing, (specifically bendable legs) don't support style type attributes 
and won't work if they are present. It changes font-size=3.5px to 
font-size=3.5 as the trailing px, required by CSS, causes font size errors 
in fritzing. It converts silkscreen (in pcb) items from the old standard 
white (which Inkscape with a white background won't display succcessfully) to
the new standard of black. It will discover and complain about (but not so
far, do anything about, due to positioning/scaling issues) terminals that 
have a zero height or width. These are not selectable by Inkscape making 
them difficult to move in the svg. Unfortunatly you need to manually change 
the size (which changes the position) and then move the teriminal to the 
correct position. It would be nice to automate this, but it isn't done now.
Last but not least, if this is a pcb svg file it moves stroke-width
commands which would be inherited by a lower level group in to that group. 
The scripts that produce gerber files are not able to access inherited values 
(as they aren't reading the xml) and thus if a stroke-width would be 
inherited from a higher level and thus is not present at the level the pad 
is generated at gerber production fails. I expect this will be the main use 
for this script. After modifiying a svg file with Inkscape you need to run 
this script to correct the modifications that Inkscape has made for CSS 
compliance before feeding it to Fritzing (which isn't CSS compliant in at 
least some cases). 

Configuration:

There are three internal configuration settings:

1) in file PPTools.py

DetailPP = 'y'

Enabled by default. If detail prettyprinting of an svg appears to have screwed
up, set this value to 'n' to disable detail prettyprinting and try again. If it
works without the detailed prettyprinting please file a bug.

2) in file FritzingTools.py

ModifyTerminal = 'n'

Disabled by default because it will make a change that will change the spacing
of the terminal position in the svg which you will manually need to correct 
using an svg editor if the width or height is 0. I enable this (by setting the
value to 'y') and then pay attention to the modifed messages to tell when it
has changed a terminal from 0. If the terminal is 0 width or height at least
Inkscape (which I use) will not select the element to move it. You have to
manually select the element and change its position with the tool bar which
I find annoying. With the value set to 'n (the default) you will get a warning
message like this one from a current core part:

Warning 16: File
'/cygdrive/c/fritzing/fritzing.0.9.3b.64.pc/fritzing-parts/core/../svg/core/schematic/4071_4_x_2_input_OR_gate_multipart_schematic.svg'
At line 66

Connector connector6terminal has a zero height
and thus is not selectable in Inkscape

This warning is all that it will do. It is up to you to edit the svg and set 
the height/width to something other than 0 and correct the x/y positioning. 

	With the value set to 'y' on the same file (in this case changed to an
exported part so as to not change core whihc will break parts update, but the 
same file as above) there is a different message in a different place:

Modified 2: File
'svg.schematic.prefix0000_fa1ebd566edf2f3d943a0046711f2d3c_1_schematic.svg'
At line 23

Connector connector6terminal had a zero height, set to 10
Check the alignment of this pin in the svg!

This message tells you the script has made a change that is going to have moved
the x/y position of the connector (and depending on what the scaling in the svg
is set to, perhaps made the height/width incorrect, as 10 isn't an appropiate 
value for all scale factors). The warning message is no longer present as there
is now this change notification instead. As a result you need to edit the svg 
and check that the terminal is 10 thou (or your preferred size, 10 thou is 
mine) and in the correct x/y position as expected by the part. The upside is 
that Inkscape will now select the terminal and move it if you move the entire 
terminal which it wouldn't before. 

3) in file FritzingCheckPart.py

Debug = 0

This value enables debug messages (set to 1 for enter/exit routine messages,
and to 2 for detailied but very verbose debug messages). It is used for 
debugging the script itself so you will normally leave it at 0 for normal 
operation. 



Likely bugs:

The most likely bug relates to prettyprinting. To prettyprint svg files the
lines are split on blanks (' ') and each element is indented and printed on 
a new line. Obviously (and for text, comments and referenceFile names so far,
detected and corrected for) lines with spaces that are supposed to be there
in the final document will get screwed up by the above and will need their 
tags added to the exemption regex in the code. 
	The original file(s) are saved in a .bak file (i.e. filename.svg will
be moved to filename.svg.bak with the script output in filename.svg). However
if you run the script a second time without copying the .bak file somewhere 
safe the original file will be overwritten without further warning, so be 
careful. In case of script error you will likely want the original file ...
	There also may be any number of other bugs I haven't found yet. If you
come across one please report it and I'll see if I can fix it.  

Known bugs:

1) Makeing a square pad in pcb via a path with a hole in it usually (but
   apparantly not always) works in Fritzing. This script however will toss

Error 74: File
'/cygdrive/c/fritzing/fritzing.0.9.3b.64.pc/fritzing-parts/core/../svg/core/pcb/DRV8825_breakout_pcb.svg'
At line 17

Connector connector136 has no radius no hole will be generated

   Which isn't correct (but also isn't easy to fix). You can either ignore this
   error as invalid (as long as the gerber export works which it does in this
   case) or replace the pad with a standard circle with a radius and stroke 
   width (which would be my choice in the matter!) which will remove this error.


Potential error messages and what to do about them:

First the dreaded trace back:

$ ./FritzingCheckPart.py Bean_revE.fzp
Traceback (most recent call last):
  File "./FritzingCheckPart.py", line 51, in <module>
    rc, FileType, Path, File = tools.ProcessArgs (sys.argv, Errors)
TypeError: 'int' object is not iterable

if you get a message like this, then I have screwed up and offended the python
gods and they have taken exception (this is basically a software error). The
best bet is to provide the call above and if possible a copy of the file that
caused it so I can try and fix it. 



now on to expected error messages:

Most (but not all, as the first few below show) error messages are of the 
form:

Error: File
'/cygdrive/c/fritzing/fritzing.0.9.3b.64.pc/fritzing.0.9.3b.64.pc/fritzing-parts/core/blend_micro1.0.fzp'
At line 444

which gives you the file name followed by the line number (if known, sometimes
it isn't) of where the error was detectd. 

	Of note is the filename will be blend_micro1.0.fzp.bak if you are 
processing an individual part (which will normally be the case). The reason 
for this is the output file 

blend_micro1.0.fzp

has been prettyprinted, and the line numbers won't match the input file 
(blend_micro1.0.fzp.bak) so you need to look for the error in the filename 
listed in the error message and then match it to the same text (which will 
have a different line number and possibly format very likely) in the output 
file if you need to. The input file will give you the place in the file that 
the error occurred and you should fix it there and then remove the .bak 
extension and re run the script in the corrected input file. 

Error messages in the order they occur in the code so essentially random
but numbered so you can index by the number to get the error description
and an explaination of the errror.  


Error 1: Can not rename filename os_error_message (os_error_number)

	The os routines returned an exception when the input file was 
        renamed. Hopefully the cause is obvious from the os messages. 


Error 2: Can not open filename  os_error_message (os_error_number)

	The os routines returned an exception when the input file was 
        opened. Hopefully the cause is obvious from the os messages. 


Error 3: Can not write filename  os_error_message (os_error_number)

	The os routines returned an exception when the input file was 
        written. Hopefully the cause is obvious from the os messages. 


Error 4: Can not close filename os_error_message (os_error_number) 

	The os routines returned an exception when the input file was 
        closed. Hopefully the cause is obvious from the os messages. 


Error 5: ParseFile can't read file filename

	The xml parser got an I/O error trying to parse the named file.


Error 6: ParseFile error parsing the input xml file filename

	The xml parser found illegal xml at the line and column listed after
	this. Note the lxml parser is more strict than either Inkscape or 
	Fritzing and will report errors that both Inkscape and Fritzing 
	will accept as valid xml. If you look however, there really is an 
	error there and you should correct it. Below is an example from the 
	Bean_revE.fzp file currently in core:

	/cygdrive/c/fritzing/fritzing.0.9.3b.64.pc/fritzing.0.9.3b.64.pc/fritzing-parts/core/Bean_revE.fzp:161:90:FATAL:PARSER:ERR_SPACE_REQUIRED: attributes construct error
 
	line 161 from Bean_revE.fzp

	<p layer='schematic' hybrid='yes' svgId='connector81pin' terminalId='connector81terminal'hybrid='yes' /></schematicView>

	there are two errors in this line. There is a missing space between 
	connector81terminal' and hybrid='yes' and the second hybrid='yes is 
	wrong. The line should be corrected to this:

	<p layer='schematic' hybrid='yes' svgId='connector81pin' terminalId='connector81terminal' /></schematicView>

	which is correct xml and the complaints from parser will stop. You 
	will get a lot more errors, but again they are really there, even 
	though the part with these errors loads and runs happily in Fritzing. 


Usage 7: PP.py filename (filename ...)

	Indicates you didn't give a filename to the PP.py script. It wants 
	one or more xml files such as

	PP.py test.svg 

	or 

	PP.py test1.svg test2.xml test3.fzp


Error 8: filename isn't a file: ignored

	The file name provided either isn't a file or isn't readable and has
	been ignored. 


Usage 9: FritzingTools.py filename.fzp or filename.svg or srcdir dstdir

	Either no or too many arguments to the script. It wants either a 
	single file name or 2 directories. 


Error 10: There must be a directory that is not '.' or '..' in the input name 
for a fzp file in order to find the svg files.

	Indicates that it needs a directory (for example core/file.fzp) in
	order to figure out where the svg files are (../svg/core/... in this
	case). Supply the directory and it will be happy. 


Usage 11: FritzingTools.py src_dir dst_dir

src_dir filename isn\'t a directory

	In this mode both arguments need to be directories and src isn't. 


Usage 12: FritzingTools.py src_dir dst_dir

dst_dir filename isn\'t a directory

	In this mode both arguments need to be directories and dst isn't. 


Error 13: dst dir

dst_dir

must be empty and it is not

	The dst_dir isn't empty (perhaps from a previous run). If you are sure
	the directory is expendable rm -R dst_dir/* will fix this.


Error 14: Creating dir

dir_name  os_error_message (os_error_number)

	A problem creating one of the dst directories. Hopefully the os error
	messages will make the cause clear. 


Error 15: Can not rename

'src_file'

to

'src_file.bak'

'file_name_from_os'

os_error_message (os_error_number)

	A problem occurred trying to rename the src_file to src_file.bak.
	Hopefully the os error messages indicate why. 


Error 16: File
'filename'
At line 20

Id xxx present more than once (and should be unique) 

	The listed id is present more than once and should be unique (often
	Fritzing ignores this but it is incorrect) 


Error 17: File
'filename'

No connectors found for view viewname.

	This is one of those messages without a line number as after all the
	connectors have been processed, no connectors were found. 


Error 18: File
'filename'

Connector connector2terminal is in the fzp file but not the svg file. (typo?)

	This connector is specified in the fzp file, but isn't in the 
	associated svg file. Depending on what type of connector it is
	this may or may not be fatal (a svgId is fatal a terminalId is not).
	In either case it is incorrect.


Error 19: File
'filename'

File type xxx is an unknown format (software error)


	Another case of software error where the type isn't svg, fzppart or
	fzpfritz. Shouldn't happen.


Error 20: File
'filename.svg'

During processing svgs from fzp, svg file doesn't exist 

	The filename referenced for this view in the fzp file doesn't exist. 
	Fritzing will try and find something to substitute, but this is still
	an error. 


Error 21: Svg file

'Filename.svg'

Has a different case in the file system than in the fpz file

'filename.svg'

	This doesn't matter on Windows as the file system is case insensitive
	however it does matter on Linux and probably MacOS where the file
	system is case sensitive and the wrong case file will not be found. 
	Change either the fzp or the file in the file system to the same 
	case and all will be well on all systems. While I could correct this
	in the fzp file it seems better to do it manually because it isn't 
	clear whether the fzp file is incorrect or this particular file system
	is incorrect, and thus is better left to a human decision rather than
	a program.


Error 22: File
'filename.fzp'
At line 1

No ModuleId found in fzp file

	There isn't a moduleId in the fzp file. This is likely fatal as I don't
	think the part can load without a moduleId. Add a moduleId to the file
	(preferably export a new part to get a Fritzing approved moduleId).


Error 23: File
'filename.fzp'
At line 20

A bus is already defined, schematic parts won't work with busses

	A non empty Bus definition has already been seen. Fritzing won't 
	currently support both busess and schematic parts.


Error 24: File
'filename'
At line 20

More than one copy of Tag sometag

	Tag sometag should only occur once in the fzp file and we have seen 
	another copy of it here.


Error 25: File
'filename.fzp'
At line 2

Multiple ModuleIds found in fzp file

	There is more than one moduleId set in the fzp file (there should only
	be one)


Error 26: File
'filename.fzp'
At line 20

State error, expected tag tag not a view name

	There is something wrong in the fzp file (or this code). The tag we
	have doesn't match the expected state of a correct fzp file. Best bet 
	is to check the format of the fzp file against a known good version, 
	as there is probably an extra or missing line in this file. 


Error 27: File
'filename.fzp'
At line 20

View name missing

	We have no viewname (iconView breadboardView schematicView pcbView)
	which should be present. 


Error 28: File
'filename.fzp'
At line 20

Multiple view tags schematicView present, ignored

	There is more than one view of this name defined in the file when there
	should only be one of each. 


Error 29: File
'filename.fzp'
At line 20

View tag scchematicView  not recognized (typo?)

	View tag isn't one of (iconView breadboardView schematicView pcbView)
	which it should be.


Error 30: File
'filename.fzp'
At line 20

No image name present

	The file name for the svg file is missing in the fzp file. 


Error 31: File
'filename.fzp'
At line 20

Multiple viewname image files present

	There is more than one image file name present, there should only be 
	one. 


Error 32: File
'filename.fzp'
At line 20

No layerId value present

	There is a layerId attribute present, but it has no value (and it needs
	one). 


Error 33: File
'filename.fzp'
At line 20

View viewname already has layerId layername, layername1 ignored

	The layerId isn't unique and it must be. 

 
Error 34: File
'filename.fzp'

No views found.

	There are no views found in the fzp file. There isn't a line number 
	because this occurs after we have seen all the lines that may contain
	a view.


Error 35: File
'filename.fzp'

Unknown view viewname found. (Typo?)

	Found a view name that isn't one of iconView breadboardView
	schematicView or pcbView (probably a typo)


Error 36: File
'filename.fzp'

No valid views found.

	Didn't find any of iconView breadboardView schematicView or pcbView
	in the list of view names.


Error 37: File
'filename.fzp'

This is a smd part as only the copper0 view is present but it is on the 
bottom layer, not the top. If you wanted a smd part change copper0 to 
copper 1 at line 20 If you wanted a through hole part add the copper1
definition after line 19

	This is a smd part but it is on the wrong layer (and thus likely an
	error). If you really want the part to be on the bottom for something
	this error can be ignored.


Error 38: File
'filename.fzp'
At line 20

State error, tag stack is at level 8 and should only go to level 7

	This error indicates that there are too many lines in the fzp file
	as the tags have gotten deeper than is possible for a valid file. 


Error 39: File
'filename.fzp'
At line 20

Connector has no id

	A connector has no id associated with it and it must have one.


Error 40: File
'filename.fzp'
At line 20

Connector has no Name

	A connector has no Name associated with it and it must have one.


Error 41: File
'filename.fzp'
At line 20

Connector connector3 has no Type

	A connector has to have type male or female and has neither.


Error 42: File
'filename.fzp'
At line 20

Connector connector3 has no description

	A connector doesn't have a description. When you hover on a pad in 
	breadboard or schematic you won't get a description. 


Error 43: File
'filename.fzp'
At line 20

Connector connector3 missing view name 

	The connector doesn't have a view name. 


Error 44: File
'filename.fzp'
At line 20

Viewname bbreadboardView invalid (typo?)

	The viewname isn't one of breadboardView schematicView pcbView and
	it should be. 


Error 45: File
'filename.fzp'
At line 20

Layer missing

	The layer attribute is missing in the fzp file. 


Error 46: File
'filename.fzp'
At line 20

No layerId for View SchematicView

	A layerId wasn't specified for this view earlier in the fzp file. 


Error 47: File
'filename.fzp'
At line 20

LayerId here doesn't match View schematicView layerId schematic

	A layerId here doesn't match the layerId specified earlier for this
	view (or views in the case of pcb view which can have multiple 
	layerids.) 


Error 48: File
'filename.fzp'
At line 20

Connector connector4 layer copper0 already defined, must be unique

	This connectorid layer combination is already defined and must be
	unique.


Error 49: File
'filename.fzp'
At line 20

hybrid is present but isn't 'yes' but yyes (typo?)

	The hybrid flag is present but with an invalid value (it must be yes).


Error 50: File
'filename.fzp'
At line 20

Tag svgId is present but has no value

	The listed tag is present but has no value set. 


Error 51: File
'filename.fzp'
At line 20

svgId missing

	There is no svgId present for this connector and one is required. 


Error 52: File
'filename.fzp'
At line 20

Bus bus2 already defined

	There is aready a bus with this id and ids must be unique. 


Error 53: File
'filename.fzp'
At line 20

Bus nodeMember connector2 does't exist

	The nodeMember specified doesn't exist and it must. 


Error 54: File
'filename.fzp'
At line 20

Bus nodeMember connector2 already in bus bus3

	The nodeMember specified is already in the specified bus and can't
	be in two at once. 


Error 55: File
'filename.fzp'
At line 20

Subpart has no id

	The subpart is missing the id field (required)


Error 56: File
'filename.fzp'
At line 20

Subpart id subpartid already exists (must be unique)

	The subpart is already in use for another subpart and must be unique.


Error 57: File
'filename.fzp'
At line 20

Subpart has no label

	The subpart has not label and it needs one. 


Error 58: File
'filename.fzp'
At line 20

Subpart subpartid already defined (duplicate?)

	The subpart has already been defined and must be unique. 


Error 59: File
'filename.fzp'
At line 20

Connector id missing, ignored

	The subpart definition is missing the id field. 


Error 60: File
'filename.fzp'
At line 20

Connector connector2 doesn't exist (and it must)

	The connector id isn't already defined in the fzp file and it must be.


Error 61: File
'filename.fzp'
At line 20

Subpart connector connector0 already in subpart sub1

	The connector id is already part of another subpart and can only be
	in one subpart. 


Error 62: File
'filename.fzp'

No connectors found to check

	There are no connectors defined when we tried to check that the
	connectors are in the correct sequence. 


Error 63: File
'filename.fzp'

Connector0 doesn't exist (connectors should start at 0)

	There isn't a connector0 and there should be. 


Error 64: File
'filename.fzp'

Connector connector5 doesn't exist when it must to stay in sequence

	Connectors 0 to 4 exist, then it skips to something above 5. This 
	causes label problems (as fritzing assumes the labels are in sequence
	and will misnumber the missing and following connections).


Error 65: File
'filename.fzp'
At line 20

Connector connector1pad is an ellipse not a circle, (gerber generation will 
break.)

	This indicates a connector in a pcb svg is an ellipse (i.e. has rx and
	ry rather than r as a radius in the xml). This is usually because of 
	a removed translate that has changed horizontal or vertical scale. The
	easiest fix is to copy one radius value to the other in xml editor
	(making sure the new radius value still keeps the intended hole size). 


Error 66: File
'filename.fzp'
At line 20

Connector connector2pin is a duplicate (and should be unique)

	The listed connector has already been seen in the svg file and should 
	be unique. As long as the two are defined identically fritzing seems
	to ignore this, but it should be corrected. 


Error 67: File
'filename.fzp'
At line 2

First Tag tag isn\'t an svg definition

	The first tag in an svg file should be svg. If it isn't there will 
	probably be a problem. Compare your file against a known correct one
	is probably the best bet here. 


Error 68: File
'filename.fzp'
At line 20

Found first group but without a svg definition

	Similar to the error above, we have found a group but haven't seen a 
	svg id yet. 


Error 69: File
'filename.fzp'
At line 20

Found a drawing element before a layerId (or no layerId)

	A drawing element (perhaps a connector) has been found before the
	layerId. If it is a visible part of the drawing, it likely won't be 
	present if the drawing is exported as a svg, so it is better to have
	the layerId first. This also may mean that the layerId is missing 
	entirely in which case one should be added befoe any drawing elements.


Error 70: File
'filename.fzp'
At line 20

More than one silkscreen/copper0/copper1 layer

	We have already seen a layer of this name in this svg, a second one is 
	an error. 


Error 71: File
'filename.fzp'
At line 20

Silkscreen layer should be at the top, not under group copper1

	As it says the silkscreen layer should be at the top not under any 
	other group. 


Error 72: File
'filename.fzp'
At line 20

copper0 should be under copper1 not the same level

	As it says copper0 should be under copper1 not at the same level.


Error 73: File
'filename.fzp'
At line 20

Too many layers, there should only be copper1 then copper0

	There is a layer under copper1/copper0 which there shouldn't be. 


Error 74: File
'filename.fzp'
At line 20

Connector connector1pad has no radius no hole will be generated

	This has been determined to be a through hole part (as no hole is 
	normal for a smd part) but there is no radius for the pad and thus
	no hole will be generated which is usually an error. 


Error 75: File
'filename.fzp'

This is a smd part as only the copper0 view is present
but it is on the bottom layer, not the top.

	Smd parts should normally be on the top side of the board so this is
	most likely an error. 


Error 76: File
'filename.fzp'
At line 20

Copper0 and copper1 have non identical transforms (no transforms is best)


	There is a transform in one or the other of the copper layers but not
	the other. What this breaks is moving a component from the top of the
	pcb to the bottom in inspector. The order of the transforms changes as
	does the scaling making the part wrong on the pcb. Ungrouping and then
	regrouping copper1/copper0 will usually fix this (the ungroup removes
	the transform).


Error 77: File
'filename.fzp'
At line 20

terminalId can't be a path as it won't work.

	The terminalId can't be of the specified type (currently path, but 
	there may be others that will get added). Unless it has a center such
	as a rectangle, line, or polygon fritzing won't take it as a terminalId
	and will default to the center of the svgId which likely isn't what you
	want. I prefer to use a rectangle of .01in by .01in for terminalID.

Error 78: Svg File
'filename.svg'

While looking for connector1pin, Subpart subpart2 has no connectors in the svg

	This subpart doesn't have any connectors defined in it and it should. 

Error 79: Svg File
'filename.svg'

Subpart subpart2 is missing connector connector1pin in the svg

	The listed pin is missing in the svg file (it may be defined in another
	subpart, in which case it will have a warning message there). 

Error 80: File
'filename.fzp'
At line 20

Both terminalId and legId present, only one or the other is allowed.

	As the message says, there are two terminal definitions and it must 
	be only one or the other.

Error 81: File
'filename.fzp'
At line 20

Subpart connector subpart1 has no pins defined

	This subpart has no pins defined and it usually needs at least one
	(there may be cases where this can be ignored though ...)

Error 82: File
'filename.svg'
At line 20

connector connector1pin isn't in a subpart

	This connector isn't part of a subpart groupname and it should be. 

Error 83: File
'filename.svg'
At line 20

Connector connector1pin shouldn't be in subpart subpart2 as it is

	The fzp file says this connector should be in another subpart, not 
	this one (at the time this error is issued we don't know what the 
	other subpart is which is why it isn't listed). 

Error 84: File
'filename.svg'
At line 20

Connector connector1pin in incorrect subpart subpart2

	This will usually accompany Error 83 above indicating that the
	connector is in a subpart where it isn't defined in the fzp file. 
	Again, because at this point we don't know where the connector should
	be, we can't list the subpart it should be in. 

Error 85: File
'filename.svg'
At line 20

subpart label subpart2 is already defined

	There is already a subpart with this label in the svg. I'm not sure 
	this error can actually occur. Inkscape won't allow you to set it (but
	a text edit would), but it may not get through the xml parser as valid
	xml if you did (but I haven't tested that so far). 

Error 86: File
'filename.svg'
At line 20

Subpart subpart1 isn\'t at the top level when it must be
Following subpart errors may be invalid until this is fixed

	While this may be legal in Fritzing, due to the complexity of checking
	subparts this script only supports subparts of the form:

	<g id='shematic'
          <g id='subpart1'
	
	where schematic is the top level group with the subpart under it. If 
	you have gotten this message the subpart errors that likely follow are
	may be invalid due to this error. You need to fix this particular 
	error and then rerun the script to find out if there are actually 
	subpart errors present. 

Error 87: File
'filename.svg'
At line 20

File test.fzp has already been processed (software error)

	We have already processed this fzp file and should not be doing so
	again. This indicates a software error of some kind that has duplicated
	filenames and should not occur. 




Warnings:

Warning 1: File

'filename'

Isn't a Fritzing file and has been ignored in processing the directory

	The listed file name is not a fritzing file and has been ignored in 
	processing the directory.


Warning 2: File
'filename.fzp'
At line 20

Text 'some text' isn't white space and may cause a problem

	Text is in an unusal place in this file, that may or may not cause a
	difficulty later. It is worth checking and perhaps removing the 
	listed text from the file to be safe.


Warning 3: File
'filename.fzp'
At line 20

ModuleId 'moduleid'

Doesn't match filename

'filename'

	The moduleId doesn't match the file name. Sometimes this is normal 
	(especially with core parts which have extra parts to the moduleId)
	and as long as fritzing is happy with the part can be ignored.


Warning 4: File
'filename.fzp'
At line 20

No referenceFile found in fzp file

	A reference file wasn't found in the fzp file. This is normally the 
	file name of the fzp file, but it not being there isn't known to 
	hurt anything.


Warning 5: File
'filename.fzp'
At line 20

Multiple referenceFile found in fzp file

	More than one reference file was found in the fzp file. There is
	normally only one which contains the filename of the fzp file. 
	Not known to hurt anything.


Warning 6: File
'filename.fzp'
At line 20


ReferenceFile name
'wrong filename'

Doesn\'t match fzp filename

'right filename'

	The reference file name should match the fzp filename but nothing 
	seems to care if it doesn't.


Warning 7: File
'filename.fzp'
At line 20

No Fritzing version in fzp file


	Normally a fzp file has the fritzing version that it was created with.
	Nothing bad is known to happen if it is missing but adding one is a 
	good idea.


Warning 8: File
'filename.fzp'
At line 20

Multiple fritzingVersion found in fzp file

	More than one fritzing version has been found. Not known to cause 
	problems but there should only be one version. 


Warning 9: File
'filename.fzp'
At line 20

One or more expected views missing (may be intended)

	We have at least one valid view, but one or more of the standard 4
	are missing. This may be intended for some parts but it is worth 
	checking that you intended to omit some views. 


Warning 10: File
'filename.fzp'
At line 20

Tag spice data
is not recognized and assumed to be spice data which is ignored
(but it might be a typo, thus this warning)

	There is a list of the known spice data that this doesn't fall in to 
	so it would be wise to check and make sure it really is spice data
	(and add the new spice data to the ignore list in this script if so)


Warning 11: File
'filename.fzp'
At line 20

Type female is not male (it usually should be)


	Usually (With some exceptions where pins on for instance an arduino 
	board would short other pins on a breadboard and breadboards) the 
	pin type should be male. Worth checking you intended it to be female.


Warning 12: File
'filename.fzp'
At line 20

Key ssvgId is not recognized

	The keyword in this connector line is not one of terminalId svgId 
	layer legId or hybrid and is thus likely a typo. 


Warning 13: File
'filename.fzp'
At line 20

Value connector2pin doesn\'t match Id connector3. (Typo?)

	The declared connector number doesn't match the number in the 
	connector statement. This is done (connectors out of order) in some
	parts in core but it is a bad practice and should be corrected although
	it is not known to harm anything except making the part hard to 
	understand. 


Warning 14: File
'filename.fzp'
At line 20

terminalId missing in schematicView (likely an error)

	There isn't a terminalId in the schematic connector definition. This
	will usually be an error, as you want one but it isn't an error because
	fritzing will use the center of the svgId position as the position of
	the terminalId (this is rarely what you want though.)


Warning 15: File
'filename.fzp'
At line 20

Empty bus definition, no id (remove?)

	There is a bus definition, but no bus actually defined (just a 
	<buses> </buses> pair). This may or may not interfere with creating 
	schematic-subparts, and isn't really needed unless you want to add
	a bus. As a result it could be removed to reduce clutter and size.


Warning 16: File
'filename.fzp'
At line 20

Connector connector1pin has a zero height or width
and thus is not selectable in Inkscape

	While connectors with 0 height or width work just fine, at least in 
	Inkscape they are not selectable by dragging a box around them and
	clicking on them. Thus you can't easily move them (you need to change
	their coordinates in the tool bar after selecting them in xml editor). 
	I prefer to use .01in by .01in rectangles for terminals because they 
	will select and move when selected with a dragged square in the gui. 
	Unfortunatly changing the height and width also changes the x/y
	position, so automatically correcting this will be more complex than
	just adding a value, so it is left for you to do at the moment. 

Warning 17: File
'filename.fzp'
At line 20

More than one svg tag found

	This may be perfectly valid (such as multiple name spaces for some 
	reason), but it is unusual enough to note in case it isn't intended. 


Warning 18: File
'filename.fzp'
At line 20

Height attribute missing

	This should probably be an error as I don't think it will work, but 
	there is no height attribute in the viewbox definition.


Warning 19: File
'filename.fzp'
At line 20

Height 200px is defined in px
in or mm is a better option (px can cause scaling problems!)

	While this is perfectly legal, it is unwise (but common!). If defined
	in px (and either no units or an explicit px is in px) fritzing will
	make a guess (and sometimes get it wrong) about how many px per inch
	the drawing used. Older Inkscapes (0.91 and older) used 90px per inch
	as of 0.92 they use the CSS standard of 96px per inch. Older copies 
	of Illustrator used 72px per inch. If you change this to being inches 
	or millimeters there is no guess required and it will scale correctly. 
	To do so in Inkscape do a edit select all and set the tool bar to in 
	or mm. Take the height and width (inches or mm) from the tool bar read 
	out and use xml editor to set those numbers in to the height and width 
	in the viewbox setting (with the in at the end to indicate this is in 
	inches). When you set them Inkscape will change the drawing to match 
	the new scale (note it is possible some part of the drawing may not 
	change correctly so visually check it). This is usually the cause of 
	a drawing that looks correct in Inkscape but is the wrong scale (i.e. 
	doesn't match the grid) in fritzing. To correct that, in Inkscape 
	you can recalculate the scaling like this: 
	
		heightpx * 72/90/96 = size in inches. 

	You will need to try the likely values 72, 90 or 96 til the scaling 
	in Fritzing is correct and then set the correct value in inches (or
	mm if you prefer) as the height and width in the first entry in xml 
	editor.  
Warning 20: File
'filename.fzp'
At line 20

copper1 layer should be at the top, not under group copper0

	If the second group is copper0 this is normal (or at least harmless)
	as the order doesn't really matter. However for smd parts the single
	copper layer needs to be copper1 so it is preferable to be copper1
	followed by copper0.


Warning 21: File
'filename.fzp'
At line 20

This appears to be a pcb svg but has no copper or silkscreen layers!

	As the message says there is no image data here at all which is likely
	an error (as the layer is defined in the fzp file).


Warning 22: File
'filename.fzp'
At line 20

Already have a layerId

	There is a second (or more) layerId in a view that only allows one 
	layer id. Likely an error. 


Warning 23: File
'filename.fzp'
At line 20

Key key_value
value '-inkscape-font-specification 'Droid Sans, Normal' is invalid and has 
been deleted

	This is the typical value that I have seen. The lxml parser appears to
	object to the leading - in the value. This warning is here in case at
	some point something less ignorable than this gets found here. 

Warning 24: File
'filename.fzp'
At line 20

Font family 'ArialMT' is not Droid Sans or OCRA
This likely won't render in Fritzing

	Fritzing only supports fonts Droid Sans or OCRA so this likely won't
	be rendered in Fritzging. If you really need this particular font you
	need to convert it to a path in your svg editor (but that is a pain to
	anyone trying to modify your part and thus undesirable). 

Warning 25: File
'filename.fzp'
At line 20

Silkscreen layer should be above the copper layers for easier selection in
pcb view

	If silkscreen is below the copper layers then part selection will
	favor the silkscreen layer making part selection more difficult. 
	Moving the silkscreen layer before the copper layers will fix this. 

Warning 26: File
'filename.fzp'
At line 20

Apparant nested tspan which fritzing doesn't support
If your text doesn't appear in Fritzing this is probably why

	As noted nested tspan don't work in Fritzing at least sometimes, in
	fact tspan is not supposed to work but usually does. 

Warning 27: File
'filename.fzp'
At line 20

Fritzing layerId silkscreen isn't a group which it usually should be

	This is a warning because (at least for silkscreen, don't know about
	the others) Fritzing will accept a path as the silkscreen (although
	it can only have one element and a group would be a better bet). 

Warning 28: File
'filename.fzp'
At line 20

name gnd present more than once (and should be unique)

	This id is duplicated in another name or description field. It is a 
	warning in this case because dups here (unlike connectors) are not
	typically fatal. The part file format document does say they should
	be unique though. 

Modified:

	These messages document the changes made by the script to the input 
	files. Note the line numbers refer to the input file (which will be
	usually in the filename.svg.bak file) as the output file has been 
	prettyprinted which changes the line numbers. As a result you need 
	to look at the input file at the line of the change and then search for
	that text in the output file to find the area of the change.

Warning 29: File
'filename.fzp'
At line 20

File test.svg
has already been processed
but will be processed again as part of this fzp file in case of new warnings.

	This svg file is likely shared by several parts. One downside of this
	is that the original of this file won't be in the .bak file as that
	will be replaced by the version from the last processing output. It 
	is processed again in case there are errors relative to this fzp file
	that are different than the first processing instance. Because 
	sometimes iconView is copied from breadboard (which would trip this 
	warning) and because we don't actually check anything in icon view
	icon view processing from the fzp is skipped. 

Modified 1: File
'filename.fzp'
At line 20

Removed px from font-size leaving 3.5

	Removed the px from font-size="3.5x" because Fritzing objects to the px
	on the font-size and sets the font-size to 0 when the part is edited.

Modified 2: File
'filename.fzp'
At line 20

Connector connector0terminal had a zero width (or height), set to 10
Check the alignment of this pin in the svg

	As it says, a 0 length height or width was set to 10 which may causee
	the location of the terminal to change. You need to verify (and move 
	if necessary) the location of this terminal in the svg. You may also
	need to adjust the size of the terminal to be 10 thou as the size of
	10 may not be correct depending on scaling and translates. 

Modified 3: File
'filename.fzp'
At line 20

Silkscreen, converted stoke/fill from white or not black to black

	Notification that we have changed the color of the silkscreen layer 
	in the svg from white (or not black) to black for both stroke and fill. 

Modified 4: File
'filename.fzp'
At line 20

ReferenceFile

'filename.svg'

doesn\'t match input file

'filename1.svg'

Corrected

	Notification that the reference file was updated to be the same as the
	file name of this svg file. Nothing much appears to care whether this
	field is correct or not.

Modified 5: File
'filename.fzp'
At line 20

Converted style to inline xml

	A style command such as

	style="fill:none;stroke:#787878;stroke-width:9.72220039

	has been converted to the equivelent xml:

	fill="none" stroke="#787878" stroke-width="9.72220039"

	(which prettyprinting will then break down to one element per properly
	 indented line changing the output line numbers substantially) because
	fritzing (specifically bendable legs) does not support the style 
	command syntax even though it is legal xml and Inkscape will convert
	the inline xml to a style command to be CSS complient.
