### gbaload.py

This is a script that helps load GBA ROMs.

To load a GBA ROM into IDA, first open the ROM in IDA. Set **ARM processors: ARM** as your processor, then go into **Processor options**. Click **Edit ARM architecture options**, then choose radio button **ARMv4T**. Now complete the load, keeping the default settings. After IDA finishes loading, run this script to set up the memory map.

Steals comments from the no$ docs (generated with gbaio.sh).

TODO:
* fix truncated comments
* verify the other ARM architecture options to make sure they are right
