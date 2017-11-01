#!/usr/bin/python3

import subprocess
import re
import configparser
import os.path as path
import sys
import threading


config = configparser.ConfigParser()
try:
	userconf = path.join(path.expanduser("~"), ".config/autohidewibox.conf")
	if len(sys.argv)>1 and path.isfile(sys.argv[1]):
		config.read(sys.argv[1])
	elif path.isfile(userconf):
		config.read(userconf)
	else:
		config.read("/etc/autohidewibox.conf")
except configparser.MissingSectionHeaderError:
	pass

# (remove the following line if your wibox variables have strange characters)
wiboxes = [ w for w in wiboxes if re.match("^[a-zA-Z_][a-zA-Z0-9_]*$", w) ]
#python>=3.4: wiboxes = [ w for w in wiboxes if re.fullmatch("[a-zA-Z_][a-zA-Z0-9_]*", w) ]

awesomeVersion = config.get(       "autohidewibox", "awesomeVersion", fallback=4)
superKeys =      config.get(       "autohidewibox", "superKeys",      fallback="133,134").split(",")
wiboxes =        config.get(       "autohidewibox", "wiboxname",      fallback="mywibox").split(",")
customhide =     config.get(       "autohidewibox", "customhide",     fallback=None)
customshow =     config.get(       "autohidewibox", "customshow",     fallback=None)
delayShow =      config.getfloat(  "autohidewibox", "delayShow",      fallback=0)
delayHide =      config.getfloat(  "autohidewibox", "delayHide",      fallback=0)
debug =          config.getboolean("autohidewibox", "debug",          fallback=False)

delay = {True: delayShow, False: delayHide}
delayThread = None
waitingFor = False
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


def setWiboxState(state=True, immediate=False):
	global delayThread, waitingFor, cancel
	if debug:
		dbgPstate = "show" if state else "hide"
	if delay[not state] > 0:
		if debug:
			print(dbgPstate, "delay other")
		if type(delayThread) == threading.Thread and delayThread.is_alive():
			# two consecutive opposing events cancel out. second event should not be called
			if debug:
				print(dbgPstate, "delay other, thread alive -> cancel")
			cancel.set()
			return
	if delay[state] > 0 and not immediate:
		if debug:
			print(dbgPstate + " delay same")
		if not (type(delayThread) == threading.Thread and delayThread.is_alive()):
			if debug:
				print(dbgPstate, "delay same, thread dead -> start wait")
			waitingFor = state
			cancel.clear()
			delayThread = threading.Thread(group=None, target=waitDelay, kwargs={"state": state})
			delayThread.daemon = True
			delayThread.start()
		# a second event setting the same state is silently discarded
		return
	if debug:
		print("state:", dbgPstate)
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
			if debug:
				print(eventmatch)
			try:
				field = "event"
				keystate = eventmatch.group(1)
				if debug:
					print("found event, waiting for detail...")
			except IndexError:
				field = None
				keystate = None
		
		if (field is "event") and detailmatch:
			if debug:
				print(detailmatch)
			try:
				if detailmatch.group(1) in superKeys:
					if debug:
						print("is a super key")
					if keystate == "13":  # press
						if debug:
							print("showing wibox")
						setWiboxState(True)
					if keystate == "14":  # release
						if debug:
							print("hiding wibox")
						setWiboxState(False)
			except IndexError:
				if debug:
					print("Couldn't parse keystate number.")
				pass
			finally:
				field = None
				keystate = None
except KeyboardInterrupt:
	pass
finally:
	setWiboxState(True, True)
	# print("Shutting down")
