# MacImageMount
GUI tool for easy mounting of RAW hard drive, cdrom, floppy images under macOS.

It is just an wrapper for macOS cli `hdiutil` but a pretty handy one.
Written in python using PySide6 GUI.

## Features
* Recursively list images in a directory. Supported extensions: "*.img, *.hda, *.iso".
* Mount any image to directory in `/Volumes`. Unmount mounted.
* Create empty image file of a given size.

## TODO
* Display image partition info
* Format empty image to FAT32/exFAT/etc.
* Add support for mounting in Read-only mode.
