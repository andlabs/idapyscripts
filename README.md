### gbaload.py

This is a script that helps load GBA ROMs.

To load a GBA ROM into IDA, first open the ROM in IDA. Set **ARM processors: ARM** as your processor, then go into **Processor options**. Click **Edit ARM architecture options**, then choose radio button **ARMv4T**. Now complete the load, keeping the default settings. After IDA finishes loading, run this script to set up the memory map.

Steals comments from the no$ docs (generated with gbaio.sh).

TODO:
* fix truncated comments
* verify the other ARM architecture options to make sure they are right

### selparse.py

This is a script that loads the symbol table stored in the SEL files associated with GameCube/Wii DOL files.

Simply load your DOL file, wait for IDA to finish processing it, and then run this script. It will ask you to locate the SEL file to load, and then load it. Pay attention to the CLI at the bottom of the IDA window, as it will point out labels it could not set for whatever reason (IDA doesn't seem to provide a way to determine why MakeLabelEx() failed...).

Based on sel_parser.py from [Megazig/WiiTools](https://github.com/Megazig/WiiTools/tree/master/PythonTools); this was originally written by [Ninjifox](https://github.com/Ninjifox).

TODO:
* TODOs in source
* (also for gbaload.py) make panic() more proper
* verify license with Megazig (Ninjifox said it was fine on IRC)
```
[16:00] <Ninjifox> looks ok to me, though I am not sure about licensing on Struct.py
[16:00] <Ninjifox> (I didn't write that)
[16:01] <Ninjifox> ((iirc, daeken wrote it a really long time ago and I have no idea how it falls))
```
