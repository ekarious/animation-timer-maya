# Animation Timer

*Get timings out of your head !*

## Purpose

This script aims to help animators get rough timings they have inside their head into usable information like times and frames to speed up the blocking process.

## Informations

- Version : 1.4.3
- Maya : 2014 ~ 2016
- License : GPL

*The version 1.4 is not compatible with previous versions.*

**This script DOES NOT animate for you.**

_The version 1.4 was mainly tested with Maya 2016 in OS X._


## Installation

To install the script, copy the script `animationtimer.py` into Maya's script folder.

```
    Windows : \Users\<username>\Documents\maya\<version>\scripts
    OS X : /Users/<username>/Library/Preferences/Autodesk/maya/<version>/scripts
```

*Note: Replace `<username>` and `<version>` with you own values.*

It should be working on Maya 2015 but i didn't tested it.
If you want to test it on Linux, go head ! But please, report to me so i can update the documentation and track bugs.

Then:

1. Copy the images from the `icons` folder into Maya's icons folder:
```
    Windows : \Users\<username>\Documents\maya\<version>\prefs\icons
    OS X : /Users/<username>/Library/Preferences/Autodesk/maya/<version>/prefs/icons
```

2. Open Maya
3. Open the script editor
4. Write the code below and press enter:
```
    import animationtimer
    animationtimer.show()
```

### To add a shortcut in a shelf

1. Select the shelf you want to put the shortcut into.
2. Click on the Help menu at the top of the script's window.
3. Select the "add to shelf" action.

*Note: the shelf icon will automatically show itself if you copied it into Maya's icon folder.*


## Usage

The main usage of this script is to help animator decide of the timing of their shots.
The script was made to be simply used with minimal effort.


## Changelog

See [CHANGELOG.md](CHANGELOG.md) file.

## Contact

**Website :** http://www.yannschmidt.com/       
**Email :** contact@yannschmidt.com
