### Auto-hide the awesome-wibox/taskbar
If you ever wanted to squeeze out that last bit of screen real estate in awesome and only show the wibox when needed, this is for you.

Since awesome doesn't allow easy access to the states of the Super/Mod-Key itself in rc.lua, one cannot simply show the wibox while the ModKey is pressed and hide it again on release.
This little python daemon will sit in the background and do just that.


### Installation
Download [the python script](https://raw.githubusercontent.com/grandchild/autohidewibox/master/autohidewibox.py) directly and put it somewhere nice – `~/.config/awesome/` seems fitting – and make it executable.

Arch Linux users can also install the AUR package [autohidewibox](https://aur.archlinux.org/packages/autohidewibox/).

### Usage
You can simply add `autohidewibox.py` to your autostart list on window manager load. It doesn't require special permissions to run.

Should you want to kill the script, simply `killall xinput` and the script will restore the wibox and shut down.

Note that if you use the little `run_once`-script that floats around, the safeguard doesn't work and you should therefore add `killall xinput` to the autostart list before `autohidewibox.py` so the old script will shutdown before awesome **re**starts.

### Dependencies
```
xorg-xinput
```

#### TODO
This is just a quick thing I just wrote, so it's still raw. You'll probably have to tailor the scripts in some places to fit your need.
```
config file
independence from xinput
???
```

#### Credits
Inspired by the first idea in http://stackoverflow.com/a/21837280 . Thanks :)
