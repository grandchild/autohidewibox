#!/usr/bin/python3

import subprocess
import re


superKeys = [
				"133",  # Meta-L
				"134",  # Meta-R
				"66",   # CapsLock
				# "37",   # Ctrl-L
				# "105",  # Ctrl-R
			]

wiboxname = "mywibox"


def setWiboxState(visible=True):
	subprocess.call(
			"/usr/bin/bash " +
			"-c \"echo '" +
			"for k,v in pairs("+wiboxname+") do " +
			"v.visible = " + ("true" if visible else "false") + " " +
			"end"
			"' | awesome-client\"",
			shell=True)


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
				print("index error")
			finally:
				field = None
				keystate = None
except KeyboardInterrupt:
	pass
finally:
	setWiboxState(True)
	print("shutting down")
