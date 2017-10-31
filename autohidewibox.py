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

superKeys = config.get("autohidewibox",
                       "superKeys",
                       fallback="133,134,66"
                      ).split(",")

wiboxes = config.get("autohidewibox",
                     "wiboxname",
                     fallback="mywibox"
                    ).split(",")
# (remove the following line if your wibox variables have strange characters)
wiboxes = [ w for w in wiboxes if re.match("^[a-zA-Z_][a-zA-Z0-9_]*$", w) ]
#python>=3.4: wiboxes = [ w for w in wiboxes if re.fullmatch("[a-zA-Z_][a-zA-Z0-9_]*", w) ]

customhide = config.get("autohidewibox",
                        "customhide",
                        fallback=None)
customshow = config.get("autohidewibox",
                        "customshow",
                        fallback=None)

delayShow = config.getfloat("autohidewibox",
                   "delayShow",
                   fallback=0)
delayHide = config.getfloat("autohidewibox",
                   "delayHide",
                   fallback=0)
delay = {True: delayShow, False: delayHide}
delayThread = None
waitingFor = False
cancel = threading.Event()

bashPath = ""
bashPotentialPaths = ["/usr/bin/bash", "/bin/bash"]
for p in bashPotentialPaths:
	if path.exists(p):
		bashPath = p
		break
if bashPath == "":
	print("Can't find bash in any of: " + ",".join(bashPotentialPaths), file=sys.stderr)
	sys.exit(1)

def setWiboxState(state=True, immediate=False):
	global delayThread, waitingFor, cancel
	if delay[not state] > 0:
		if type(delayThread) == threading.Thread and delayThread.is_alive():
			# two consecutive opposing events cancel out. second event should not be called
			cancel.set()
			return
	if delay[state] > 0 and not immediate:
		if not (type(delayThread) == threading.Thread and delayThread.is_alive()):
			waitingFor = state
			cancel.clear()
			delayThread = threading.Thread(group=None, target=waitDelay, kwargs={"state": state})
			delayThread.daemon = True
			delayThread.start()
		# a second event setting the same state is silently discarded
		return
	for wibox in wiboxes:
		subprocess.call(
			bashPath + " " +
			"-c \"echo '" +
			"for k,v in pairs("+wibox+") do " +
			"v.visible = " + ("true" if state else "false") + " " +
			"end"
			"' | awesome-client\"",
			shell=True)
	
	customcmd = customshow if state else customhide
	if customcmd:
		subprocess.call(
			bashPath + " " +
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
			# print(eventmatch)
			try:
				field = "event"
				keystate = eventmatch.group(1)
				# print("found event, waiting for detail...")
			except IndexError:
				field = None
				keystate = None
		
		if (field is "event") and detailmatch:
			# print(detailmatch)
			try:
				if detailmatch.group(1) in superKeys:
					# print("is a super key")
					if keystate == "13":  # press
						# print("showing wibox")
						setWiboxState(True)
					if keystate == "14":  # release
						# print("hiding wibox")
						setWiboxState(False)
			except IndexError:
				# print("Couldn't parse keystate number.")
				pass
			finally:
				field = None
				keystate = None
except KeyboardInterrupt:
	pass
finally:
	setWiboxState(True, True)
	# print("Shutting down")
