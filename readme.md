# Animation Timer

## Installation

It was tested with Maya 2014 on OSX. I cannot works easily on older Maya version because it needs a version of PySide and Qt to be installed. Since Maya 2014, those are packed with it when you installed the software.

It sould be working on Maya 2015 but i didn't tested it.
If you want to test on different systems like Window or Linux, go head ! But please, report to me so i can update the documentation and track bugs.

---

The installation is really simple.

To make the plugin works, copy it into a location where you will keep it safe.
I recommand the script direcory of Maya.

Do not forget the change <username> and <version> by the version you are using.

Windows : \Users\<username>\Documents\maya\<version>\scripts
OS X : /Users/<username>/Library/Preferences/Autodesk/maya/<version>/scripts
Then follow the steps below:

Open Maya.
Open the script editor.
Open the script inside the editor.
Create a shelf button for a better way to open it in the future.
Clic the shelf button to open the plugin !
The installation process may change in the future.

## Use

Just launch it.

For using it. You can use the timer controls:

- Start : Start the timer / Capture current time and frame is already started.
- Stop : Start the timer / Capture current time and frame is already started.
- Reset : Erase all time captured and reset the timer and frame counter. / Stop the timer beforhand if not stopped.

I added 3 shortcuts keyboard keys to use those actions
(for now, they are not editable)

- Space : Can be used like the start button.
- Escape : Can be used like the stop button.
- Backspace : Delete row(s) if selected, otherwise acts like the reset button.

Tip : The "24 fps" and the "No auto stop" texts are actually buttons !

Have fun :)

## Contact

If you want to send me suggestion or for a technical problem.
Go to my website : http://yannschmidt.com/contact/
