# Animation Timer

## Purpose

Ever had a timing in your head for your next animation ?
Or do you want to change a part of your animation with a timing you have in your head ?

If so, this program can help you.
To kick start your blocking process or test out if the timing you think about is good or bad.

Current version : 1.3.1

## Informations

When you think about your animation, every time you think about something (like a key pose for example),
you can save the time and frame that pose might need to happened.

Example :

Let's say you want to animate a ball.

When you start the timer, think as your animation starting in your head.
Then click "Capture Frame" every time the ball should hit the ground.

The program will keep those times and frames in the main window for your use.
(If you want to really keep it for later, do not forget to save them to a file !)

Now, you have a rough information where to put your frames to start your animation !

For a video tutorial, go : `http://yannschmidt.com/scripts/maya/animation-timer/docs/quick-start-guide/`


## Installation

It was tested with Maya 2014 on OSX and Windows. I cannot works easily on older Maya version because it needs a version of PySide and Qt to be installed. Since Maya 2014, those are packed with it when you installed the software.

It should be working on Maya 2015 but i didn't tested it.
If you want to test it on Linux, go head ! But please, report to me so i can update the documentation and track bugs.


1) New Installation process:

To make the plugin works, copy it into the script directory of Maya.
Do not forget to change `<username>` and `<version>` by what you have.

    Windows : \Users\<username>\Documents\maya\<version>\scripts
    OS X : /Users/<username>/Library/Preferences/Autodesk/maya/<version>/scripts

Then Follow the steps below:

1. Open Maya
2. Open the script editor
3. Write the code below and press enter:


    import animationtimer
    animationtimer.show()
    

To add a shortcut in a shelf:

1. Select the shelf you want to put the shortcut. 
2. Click on the Help menu at the top of the plugin window.
3. Select the "add to shelf" action.

That it !


2) Old Installation process:

To make the plugin works, copy it into a location where you will keep it safe.
I recommend the script directory of Maya.

Do not forget to change `<username>` and `<version>` by what you have.

    Windows : \Users\<username>\Documents\maya\<version>\scripts
    OS X : /Users/<username>/Library/Preferences/Autodesk/maya/<version>/scripts

Then follow the steps below:

1. Open Maya.
2. Open the script editor.
3. Open the script inside the editor.
4. Create a shelf button for a better way to open it in the future.
5. Click the shelf button to open the plugin !
6. The installation process may change in the future.


## Controls

Just launch it.

For using it. You can use the timer controls:

- Start : Start the timer / Capture current time and frame is already started.
- Stop : Stop the timer.
- Reset : Erase all time captured and reset the timer and frame counter. / Stop the timer beforehand if not stopped.

I added 3 shortcuts keyboard keys to use those actions
(for now, they are not editable)

- Space : Can be used like the start button.
- Escape : Can be used like the stop button.
- Backspace : Delete row(s) if selected, otherwise acts like the reset button.

Tip : The "24 fps" and the "No auto stop" texts are actually buttons !

Have fun ;)


## Contact

If you want to send me suggestion or for a technical problem.
Go to my website : http://yannschmidt.com/contact/
