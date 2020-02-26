### Auto-hide the awesome-wibox/taskbar
If you ever wanted to squeeze out that last bit of screen real estate in awesome and
only show the wibox when needed (i.e when pressing the ModKey), this is for you.

Since awesome doesn't allow easy access to the states of the Super/Mod-Key itself in
*rc.lua*, one cannot simply show the wibox while the ModKey is pressed and hide it again
on release.
This little python daemon will sit in the background and do just that.

Extending away from what the name suggests it can also execute any custom lua code on
hide or show, specified in the config file.

### Installation
Install the `xinput` binary. The package is named `xinput` in Debian/Ubuntu and
`xorg-xinput` in Arch. (Some other popular distros don't seem to readily provide this
package, according to [pkgs.org](https://pkgs.org/search/?q=xinput)).

Download [the python script](
https://raw.githubusercontent.com/grandchild/autohidewibox/master/autohidewibox.py)
directly and put it somewhere nice – `~/.config/awesome/` seems fitting – and make it
executable.

Arch Linux users can also install the AUR package [autohidewibox](
https://aur.archlinux.org/packages/autohidewibox/).

### Usage
```
autohidewibox.py [configfile.conf]
```
Config files will be tried in the order
 * commandline parameter
 * `~/.config/awesome/autohidewibox.conf`
 * `~/.config/autohidewibox.conf`
 * `/etc/autohidewibox.conf`

Otherwise settings default to *SuperL* and *SuperR* toggling *mywibox*.

You can simply add `autohidewibox.py` to your autostart list in rc.lua. It doesn't
require special permissions to run.

To terminate the script, simply `killall xinput` and the script will restore the wibox
and shut down.

Note that if, for autostarting programs, you use that little `run_once`-script that
floats around, the safeguard doesn't work and you should therefore add `killall xinput`
to the autostart list before `autohidewibox.py` so the old script instance will shutdown
before awesome *re*starts.

### Dependencies
 * xorg-xinput

#### TODO
 * independence from xinput
 * leave wibox visible on run/lua_exec etc.
 * show wibox when mouse hits bottom of the screen
 * ???

#### Credits
Inspired by the first idea in http://stackoverflow.com/a/21837280 . Thanks :)

### License

[![License](https://img.shields.io/github/license/grandchild/autohidewibox.svg)](
https://creativecommons.org/publicdomain/zero/1.0/)

You may use this code without attribution, that is without mentioning where it's from or
who wrote it. I would actually prefer if you didn't mention me. You may even claim it's
your own.
