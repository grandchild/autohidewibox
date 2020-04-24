#!/usr/bin/env python3
import configparser
import os.path as path
import re
import subprocess
import sys
import threading

MODE_TRANSIENT = "transient"
MODE_TOGGLE = "toggle"

config = configparser.ConfigParser()
try:
    user_awesome_conf = path.join(
        path.expanduser("~"), ".config/awesome/autohidewibox.conf"
    )
    user_conf = path.join(path.expanduser("~"), ".config/autohidewibox.conf")
    system_conf = "/etc/autohidewibox.conf"
    if len(sys.argv) > 1 and path.isfile(sys.argv[1]):
        config.read(sys.argv[1])
    elif path.isfile(user_awesome_conf):
        config.read(user_awesome_conf)
    elif path.isfile(user_conf):
        config.read(user_conf)
    else:
        config.read(system_conf)
except configparser.MissingSectionHeaderError:
    pass


awesome_version = config.get("autohidewibox", "awesome_version", fallback=4)
super_keys = config.get("autohidewibox", "super_keys", fallback="133,134").split(",")
wiboxes = config.get("autohidewibox", "wiboxname", fallback="mywibox").split(",")
custom_hide = config.get("autohidewibox", "custom_hide", fallback=None)
custom_show = config.get("autohidewibox", "custom_show", fallback=None)
delay_show = config.getfloat("autohidewibox", "delay_show", fallback=0)
delay_hide = config.getfloat("autohidewibox", "delay_hide", fallback=0)
mode = config.get("autohidewibox", "mode", fallback=MODE_TRANSIENT)
debug = config.getboolean("autohidewibox", "debug", fallback=False)

# (remove the following line if your wibox variables have strange characters)
wiboxes = [w for w in wiboxes if re.match("^[a-zA-Z_][a-zA-Z0-9_]*$", w)]
### python>=3.4:
# wiboxes = [ w for w in wiboxes if re.fullmatch("[a-zA-Z_][a-zA-Z0-9_]*", w) ]

delay = {True: delay_show, False: delay_hide}
delay_thread = None
wibox_is_currently_visible = False
waiting_for = False
non_super_key_was_pressed = False
cancel = threading.Event()

sh_path = ""
sh_potential_paths = ["/usr/bin/sh", "/bin/sh"]
for p in sh_potential_paths:
    if path.exists(p):
        sh_path = p
        break
if sh_path == "":
    print("Can't find sh in any of: " + ",".join(sh_potential_paths), file=sys.stderr)
    sys.exit(1)

hide_command_v3 = "for k,v in pairs({wibox}) do v.visible = {state} end"
hide_command_v4 = "for s in screen do s.{wibox}.visible = {state} end"
try:
    hide_command = hide_command_v4 if int(awesome_version) >= 4 else hide_command_v3
except ValueError:
    hide_command = hide_command_v4


def _debug(*args):
    if debug:
        print(*args)


def set_wibox_state(state=True, immediate=False):
    global delay_thread, waiting_for, cancel, wibox_is_currently_visible
    wibox_is_currently_visible = state
    dbg_pstate = "show" if state else "hide"
    if delay[not state] > 0:
        _debug(dbg_pstate, "delay other")
        if type(delay_thread) == threading.Thread and delay_thread.is_alive():
            # two consecutive opposing events cancel out. second event should not be
            # called
            _debug(dbg_pstate, "delay other, thread alive -> cancel")
            cancel.set()
            return
    if delay[state] > 0 and not immediate:
        _debug(dbg_pstate + " delay same")
        if not (type(delay_thread) == threading.Thread and delay_thread.is_alive()):
            _debug(dbg_pstate, "delay same, thread dead -> start wait")
            waiting_for = state
            cancel.clear()
            delay_thread = threading.Thread(
                group=None, target=wait_delay, kwargs={"state": state}
            )
            delay_thread.daemon = True
            delay_thread.start()
        # a second event setting the same state is silently discarded
        return
    _debug("state:", dbg_pstate)
    for wibox in wiboxes:
        subprocess.call(
            sh_path
            + " "
            + "-c \"echo '"
            + hide_command.format(wibox=wibox, state="true" if state else "false")
            + "' | awesome-client\"",
            shell=True,
        )

    customcmd = custom_show if state else custom_hide
    if customcmd:
        subprocess.call(
            sh_path + " " + "-c \"echo '" + customcmd + "' | awesome-client\"",
            shell=True,
        )


def wait_delay(state=True):
    if not cancel.wait(delay[state] / 1000):
        set_wibox_state(state=state, immediate=True)


try:
    set_wibox_state(False)

    proc = subprocess.Popen(
        ["xinput", "--test-xi2", "--root", "3"], stdout=subprocess.PIPE
    )

    field = None
    key_state = None

    for line in proc.stdout:
        l = line.decode("utf-8").strip()
        event_match = re.match("EVENT type (\\d+) \\(.+\\)", l)
        detail_match = re.match("detail: (\\d+)", l)

        if event_match:
            _debug(event_match)
            try:
                field = "event"
                key_state = event_match.group(1)
                _debug("found event, waiting for detail...")
            except IndexError:
                field = None
                key_state = None

        if (field == "event") and detail_match:
            _debug(detail_match)
            try:
                if detail_match.group(1) in super_keys:
                    _debug("is a super key")
                    if key_state == "13":  # press
                        non_super_key_was_pressed = False
                        if mode == MODE_TRANSIENT:
                            _debug("showing wibox")
                            set_wibox_state(True)
                    if key_state == "14":  # release
                        if mode == MODE_TRANSIENT:
                            _debug("hiding wibox")
                            set_wibox_state(False)
                        # Avoid toggling the wibox when a super key is used in
                        # conjunction with another key.
                        elif mode == MODE_TOGGLE and not non_super_key_was_pressed:
                            _debug("toggling wibox")
                            set_wibox_state(not wibox_is_currently_visible)
                            non_super_key_was_pressed = False
                else:
                    non_super_key_was_pressed = True
            except IndexError:
                _debug("Couldn't parse key_state number.")
                pass
            finally:
                field = None
                key_state = None
except KeyboardInterrupt:
    pass
finally:
    set_wibox_state(True, True)
    _debug("Shutting down")
