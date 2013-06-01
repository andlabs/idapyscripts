### gbaload.py

This is a script that helps load GBA ROMs.

To load a GBA ROM into IDA, first open the ROM in IDA. Set **ARM processors: ARM** as your processor, then go into **Processor options**. Click **Edit ARM architecture options**, then choose radio butotn **ARMv7-A&R**. Now complete the load, keeping the default settings. After IDA finishes loading, run this script to set up the memory map.

Steals comments from the no$ docs (generated with gbaio.sh).

TODO:
* move the cursor to $80000000 at the end
