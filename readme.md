# Animation Timer

*Get timings out of your head !*

## Purpose

This script aims to help animators get rough timings they have inside their head into usable information like times and frames to speed up the blocking process.

## Informations

- Version : 1.4
- Maya : 2014+
- License : GPL

*Note: The version 1.4 is not compatible with previous versions.*

**This script DOES NOT animate for you.**

The version 1.4 was mainly tested with Maya 2016 in OS X.
But it should work fine from Maya 2014 to Maya 2016.
If you encounter strange behaviors in Windows and other versions, let me know.


## Installation

To install the script, copy the script `animationtimer.py` into Maya's script folder.

    Windows : \Users\<username>\Documents\maya\<version>\scripts
    OS X : /Users/<username>/Library/Preferences/Autodesk/maya/<version>/scripts

*Note: Replace `<username>` and `<version>` with you own values.*2

Then:

1. Copy the images from the `icons` folder into Maya's icons folder:

    Windows : \Users\<username>\Documents\maya\<version>\prefs\icons
    OS X : /Users/<username>/Library/Preferences/Autodesk/maya/<version>/prefs/icons

2. Open Maya
3. Open the script editor
4. Write the code below and press enter:

    import animationtimer
    animationtimer.show()


### To add a shortcut in a shelf

1. Select the shelf you want to put the shortcut into.
2. Click on the Help menu at the top of the script's window.
3. Select the "add to shelf" action.

*Note: the shelf icon will automatically show itself if you copied it into Maya's icon folder.*


## Usage
## Changelog

### 1.4:

- **Important:** Complete rewrite of the script.
- **Add:** Interval column
- **Add:** Possibility to show / hide columns
- **Add:** Possibility to offset the timer or/and the frame counter
- **Add:** Remember the main window size
- **Add:** Button to reset the main window size
- **Add:** Possibility to play the animation in a file from the current frame when clicking on the line number
- **Add:** Button to toggle on/off the sound during the playback.
- **Add:** Possibility to see the frames on the timeline !
- **Add:** Button to Clear the recent timings list.
- **Add:** Reset offset button.
- **Change:** Unified Options Window.
- **Change:** Buttons are now using icons.
- **Change:** File name area at the button for better visualization.
- **Change:** Shelf icon
- **Change:** Better file management.
- **Change:** Recent timings better management.
- **Change:** Minor re-factorization in the User Preferences Panel.
- **Fix:** Stop timer when the main window lose focus (+ option in preference window available)
- **Remove:** Auto stop function. There are now securities which invalidates the need for this function.

## Contact

**Website :** http://www.yannschmidt.com/contact/
**Email :** contact@yannschmidt.com








## Purpose

Ever had a timing in your head for your next animation ?
Or do you want to change a part of your animation with a timing you have in your head ?

If so, this program can help you.
To kick start your blocking process or test out if the timing you think about is good or bad.

Current version : 1.4

## Informations

When you think about your animation, every time you think about something (like a key pose for example),
you can save the time and frame that pose might need to happened.

Example :

Let's say you want to animate a ball.

When you start the timer, think as your animation starting in your head.
Then click "Capture" every time the ball should hit the ground.

The program will keep those times and frames in the main window for your use.
(If you want to really keep it for later, do not forget to save them to a file !)

Now, you have a rough information where to put your frames to start your animation !

For a video tutorial, go : `http://www.yannschmidt.com/scripts/maya/animation-timer/docs/quick-start-guide/`
