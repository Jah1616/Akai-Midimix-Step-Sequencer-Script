#name=AKAI Midimix2

import channels
import midi
import device
import general
import time
import ui
import transport

# All arrays shown here map the controls from left to right on the midimix
faderInputs  = [19, 23, 27, 31, 49, 53, 57, 61]
masterFader  = 62
panInputs    = [18, 22, 26, 30, 48, 52, 56, 60]
muteButtons  = [1, 4, 7, 10, 13, 16, 19, 22]
soloButtons  = [2, 5, 8, 11, 14, 17, 20, 23]
armButtons   = [3, 6, 9, 12, 15, 18, 21, 24]
bankLeft     = 25 # channel up
bankRight    = 26 # channel down
soloSwitch   = 27

# CONSTANTS
potInput          = 176
buttonPress       = midi.MIDI_NOTEON
buttonRelease     = midi.MIDI_NOTEOFF
minimumAPIVersion = 7

# VARS
noteOffset = 0

def OnInit():
	armLEDsOff()
	noteOffset = 0
	device.midiOutMsg(midi.MIDI_NOTEON + (3 << 8) + (127 << 16))
	print("init")
	if general.getVersion() >= minimumAPIVersion:
		print("API up to date.")
	else:
		raise Exception("Your version of FL Studio is too old to use this script. Please update to a newer version.")

def OnDeInit():
	for i in range(0,8):
		try:
			for f in range(0,3):
				try:
					device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + f << 8) + (0 << 16))
				except:
					break
		except:
			break
		device.midiOutMsg(midi.MIDI_NOTEON + (bankLeft << 8) + (0 << 16))
		device.midiOutMsg(midi.MIDI_NOTEON + (bankRight << 8) + (0 << 16))
		device.midiOutMsg(midi.MIDI_NOTEON + (soloSwitch << 8) + (0 << 16))
	print("deinit")

def OnMidiMsg(event):
	global buttonPress, buttonRelease, noteOffset
	event.handled = False
	print(event.midiId, event.data1, event.data2, event.status, event.note, event.progNum, event.controlNum, event.controlVal)
	if (event.midiId == buttonPress) or (event.midiId == buttonRelease):

		if event.data1 in muteButtons:
			if event.midiId == buttonPress:
				notePos = muteButtons.index(event.data1) + noteOffset
				if channels.getGridBit(channels.channelNumber(1), notePos) == 0:	# is note on?
					channels.setGridBit(channels.channelNumber(1), notePos, 1)	# note on
					ui.setHintMsg("Step On: " + str(notePos + 1))
					device.midiOutMsg(midi.MIDI_NOTEON + (event.data1 << 8) + (127 << 16))	# LED feedback
				else:
					channels.setGridBit(channels.channelNumber(1), notePos, 0)	# note off
					device.midiOutMsg(midi.MIDI_NOTEON + (event.data1 << 8) + (0 << 16))	# LED feedback
					ui.setHintMsg("Step Off: " + str(notePos + 1))
				event.handled = True
			elif event.midiId == buttonRelease:
				event.handled = True

		elif event.data1 in armButtons:
			if event.midiId == buttonPress:
				noteOffset = armButtons.index(event.data1) * 8	# set note offset
				armLEDsOff()	# mute unwanted LEDs
				device.midiOutMsg(midi.MIDI_NOTEON + (event.data1 << 8) + (127 << 16))	# LED feedback
				muteLEDsCheck()	# check new channel LEDs
				print(noteOffset)
				ui.setHintMsg("Step Sequencer Selection: " + str(noteOffset) + " - " + str(noteOffset + 8))
				event.handled = True
			elif event.midiId == buttonRelease:
				event.handled = True

		elif event.data1 == bankLeft:
			if event.midiId == buttonPress:
				if channels.channelNumber(1) >> 0:	# can channel move up?
					channels.selectOneChannel(channels.channelNumber(1) - 1) # select new channel
					muteLEDsCheck() # update LEDs
					device.midiOutMsg(midi.MIDI_NOTEON + (bankLeft << 8) + (127 << 16))	# LED feedback
					ui.setHintMsg(channels.getChannelName(channels.channelNumber(1)))
					print("channel down")
					event.handled = True
				else:
					ui.setHintMsg("Already At First Channel (" + str(channels.getChannelName(channels.channelNumber(1))) + ")")
					event.handled = True
			elif event.midiId == buttonRelease:
				device.midiOutMsg(midi.MIDI_NOTEON + (bankLeft << 8) + (0 << 16))	# LED feedback
				event.handled = True

		elif event.data1 == bankRight:
			if event.midiId == buttonPress:
				if (channels.channelNumber(1) != channels.channelCount(0) - 1):	# can channel move down?
					channels.selectOneChannel(channels.channelNumber(1) + 1)	# select new channel
					muteLEDsCheck()	# update LEDs
					device.midiOutMsg(midi.MIDI_NOTEON + (bankRight << 8) + (127 << 16)) # LED feedback
					ui.setHintMsg(channels.getChannelName(channels.channelNumber(1)))
					print("channel down")
					event.handled = True
				else:
					ui.setHintMsg("Already At Last Channel (" + str(channels.getChannelName(channels.channelNumber(1))) + ")")
					event.handled = True
			elif event.midiId == buttonRelease:
				device.midiOutMsg(midi.MIDI_NOTEON + (bankRight << 8) + (0 << 16))	# LED feedback
				event.handled = True

		elif event.data1 == soloSwitch:
			if event.midiId == buttonPress:
				channels.midiNoteOn(channels.channelNumber(1), 60, 100)	# preview sample of selected channel
				print("sample preview")
				ui.setHintMsg("Previewing: " + str(channels.getChannelName(channels.channelNumber(1))))
				event.handled = True
			if event.midiId == buttonRelease:
				event.handled = True

		else:
			event.handled = True

	elif event.midiId == potInput:

		if event.data1 == masterFader:
			channels.setChannelVolume(channels.channelNumber(1), event.data2 / 127)	# alter current channel volume
			print("channel volume")

		else:
			event.handled = True

def armLEDsOff():
	for i in range(0,8):
		try:
			device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 3 << 8) + (0 << 16))
		except:
			break
def muteLEDsCheck():
	for i in range(0,8):
		try:
			if channels.getGridBit(channels.channelNumber(1), i + noteOffset) == 1:
				device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 1 << 8) + (127 << 16))
			elif channels.getGridBit(channels.channelNumber(1), i + noteOffset) == 0:
				device.midiOutMsg(midi.MIDI_NOTEON + ((i * 3) + 1 << 8) + (0 << 16))
		except:
			break

def OnRefresh(flags):
	muteLEDsCheck()


# end