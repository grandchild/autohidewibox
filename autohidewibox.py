#!/usr/bin/python3

import subprocess
import re
import configparser
import os.path as path
import sys
import threading

MODE_TRANSIENT = "transient"
MODE_TOGGLE = "toggle"

config = configparser.ConfigParser()
try:
	userawesomeconf = path.join(path.expanduser("~"), ".config/awesome/autohidewibox.conf")
	userconf = path.join(path.expanduser("~"), ".config/autohidewibox.conf")
	systemconf = "/etc/autohidewibox.conf"
	if len(sys.argv)>1 and path.isfile(sys.argv[1]):
		config.read(sys.argv[1])
	elif path.isfile(userawesomeconf):
		config.read(userawesomeconf)
	elif path.isfile(userconf):
		config.read(userconf)
	else:
		config.read(systemconf)
except configparser.MissingSectionHeaderError:
	pass


awesomeVersion = config.get(       "autohidewibox", "awesomeVersion", fallback=4)
superKeys =      config.get(       "autohidewibox", "superKeys",      fallback="133,134").split(",")
wiboxes =        config.get(       "autohidewibox", "wiboxname",      fallback="mywibox").split(",")
customhide =     config.get(       "autohidewibox", "customhide",     fallback=None)
customshow =     config.get(       "autohidewibox", "customshow",     fallback=None)
delayShow =      config.getfloat(  "autohidewibox", "delayShow",      fallback=0)
delayHide =      config.getfloat(  "autohidewibox", "delayHide",      fallback=0)
mode =           config.get(       "autohidewibox", "mode",           fallback=MODE_TRANSIENT)
debug =          config.getboolean("autohidewibox", "debug",          fallback=False)

# (remove the following line if your wibox variables have strange characters)
wiboxes = [ w for w in wiboxes if re.match("^[a-zA-Z_][a-zA-Z0-9_]*$", w) ]
#python>=3.4: wiboxes = [ w for w in wiboxes if re.fullmatch("[a-zA-Z_][a-zA-Z0-9_]*", w) ]

delay = {True: delayShow, False: delayHide}
delayThread = None
wiboxIsCurrentlyVisible = False
waitingFor = False
nonSuperKeyWasPressed = False
cancel = threading.Event()

shPath = ""
shPotentialPaths = ["/usr/bin/sh", "/bin/sh"]
for p in shPotentialPaths:
	if path.exists(p):
		shPath = p
		break
if shPath == "":
	print("Can't find sh in any of: " + ",".join(shPotentialPaths), file=sys.stderr)
	sys.exit(1)

hideCommand3 = "for k,v in pairs({wibox}) do v.visible = {state} end"
hideCommand4 = "for s in screen do s.{wibox}.visible = {state} end"
try:
	hideCommand = hideCommand4 if int(awesomeVersion) >= 4 else hideCommand3
except ValueError:
	hideCommand = hideCommand4


def _debug(*args):
	if debug:
		print(*args)


def setWiboxState(state=True, immediate=False):
	global delayThread, waitingFor, cancel, wiboxIsCurrentlyShown
	wiboxIsCurrentlyShown = state
	dbgPstate = "show" if state else "hide"
	if delay[not state] > 0:
		_debug(dbgPstate, "delay other")
		if type(delayThread) == threading.Thread and delayThread.is_alive():
			# two consecutive opposing events cancel out. second event should not be called
			_debug(dbgPstate, "delay other, thread alive -> cancel")
			cancel.set()
			return
	if delay[state] > 0 and not immediate:
		_debug(dbgPstate + " delay same")
		if not (type(delayThread) == threading.Thread and delayThread.is_alive()):
			_debug(dbgPstate, "delay same, thread dead -> start wait")
			waitingFor = state
			cancel.clear()
			delayThread = threading.Thread(group=None, target=waitDelay, kwargs={"state": state})
			delayThread.daemon = True
			delayThread.start()
		# a second event setting the same state is silently discarded
		return
	_debug("state:", dbgPstate)
	for wibox in wiboxes:
		subprocess.call(
			shPath + " " +
			"-c \"echo '" +
			hideCommand.format(wibox=wibox, state="true" if state else "false") +
			"' | awesome-client\"",
			shell=True)
	
	customcmd = customshow if state else customhide
	if customcmd:
		subprocess.call(
			shPath + " " +
			"-c \"echo '" +
			customcmd +
			"' | awesome-client\"",
			shell=True)


def waitDelay(state=True):
	if not cancel.wait(delay[state]/1000):
		setWiboxState(state=state, immediate=True)


try:
	setWiboxState(False)
	
	proc = subprocess.Popen(['xinput', '--test-xi2', '--root', '3'], stdout=subprocess.PIPE)

	field = None
	keystate = None

	for line in proc.stdout:
		l = line.decode("utf-8").strip()
		eventmatch = re.match("EVENT type (\\d+) \\(.+\\)", l)
		detailmatch = re.match("detail: (\\d+)", l)
		
		if eventmatch:
			_debug(eventmatch)
			try:
				field = "event"
				keystate = eventmatch.group(1)
				_debug("found event, waiting for detail...")
			except IndexError:
				field = None
				keystate = None
		
		if (field is "event") and detailmatch:
			_debug(detailmatch)
			try:
				if detailmatch.group(1) in superKeys:
					_debug("is a super key")
					if keystate == "13":  # press
						nonSuperKeyWasPressed = False
						if mode == MODE_TRANSIENT:
							_debug("showing wibox")
							setWiboxState(True)
					if keystate == "14":  # release
						if mode == MODE_TRANSIENT:
							_debug("hiding wibox")
							setWiboxState(False)
						# Avoid toggling the wibox when a super key is used in conjunction
						# with another key.
						elif mode == MODE_TOGGLE and not nonSuperKeyWasPressed:
							_debug("toggling wibox")
							setWiboxState(not wiboxIsCurrentlyShown)
							nonSuperKeyWasPressed = False
				else:
					nonSuperKeyWasPressed = True
			except IndexError:
				_debug("Couldn't parse keystate number.")
				pass
			finally:
				field = None
				keystate = None
except KeyboardInterrupt:
	pass
finally:
	setWiboxState(True, True)
	# print("Shutting down")
