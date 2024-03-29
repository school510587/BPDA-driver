#A part of NonVisual Desktop Access (NVDA)
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
#Copyright (C) 2012/15 Ulf Beckmann <beckmann@flusoft.de>
#Copyright (C) 2020-2021 Bo-Cheng Jhan <school510587@yahoo.com.tw>


# This file represents the braille display driver for
# Seika Mini, a product from Nippon Telesoft
# see www.seika-braille.com for more details
# 09.06.2012
# Dec14/Jan15 add BrilleInput
# 2019-04-23 (Accessolutions):
#  - Repackaging as an NVDA add-on.
#  - Amend driver description to mention newer models

from collections import OrderedDict
from ctypes import *
import os
import sys
import wx

import addonHandler
import braille
import brailleInput
import inputCore
import hwPortUtils
from logHandler import log


addonHandler.initTranslation()


if sys.version_info[0] < 3:
	to_bytes = lambda cells: "".join(chr(cell) for cell in cells)
else: # Python 3, NVDA 2019.3 or later
	to_bytes = lambda cells: bytes(cells)
	xrange = range


READ_INTERVAL = 50

DOT_1 = 0x1
DOT_2 = 0x2
DOT_3 = 0x4
DOT_4 = 0x8
DOT_5 = 0x10
DOT_6 = 0x20
DOT_7 = 0x40
DOT_8 = 0x80


_keyNames = OrderedDict([
	(0x000001, "BACKSPACE"),
	(0x000002, "SPACE"),
	(0x000004, "LB"),
	(0x000008, "RB"),
	(0x000010, "LJ_CENTER"),
	(0x000020, "LJ_LEFT"),
	(0x000040, "LJ_RIGHT"),
	(0x000080, "LJ_UP"),
	(0x000100, "LJ_DOWN"),
	(0x000200, "RJ_CENTER"),
	(0x000400, "RJ_LEFT"),
	(0x000800, "RJ_RIGHT"),
	(0x001000, "RJ_UP"),
	(0x002000, "RJ_DOWN"),
])

_dotNames = OrderedDict()
for i in xrange(1, 9):
	key = globals()["DOT_%d" % i]
	_dotNames[key] = "d%d" % i


# try to load the SeikaDevice.dll
# first get the path of the SeikaMini.py
# get the current work directory
# change to this directory
# load the .dll, the SeikaDevice.dll can also load by Pathname + dllname
#      but not the SLABxxx.dll's
# after loading, set the path back to the work path 

BASE_PATH = os.path.dirname(__file__)
DLLNAME = "SeikaDevice.dll"
WORK_PATH = os.getcwd()

if not os.path.isfile(BASE_PATH+"\\"+DLLNAME):
	BASE_PATH = "brailleDisplayDrivers"
os.chdir(BASE_PATH)
try:
	seikaDll=cdll.LoadLibrary(DLLNAME)
except:
	seikaDll=None
	log.error("LoadLibrary failed " + DLLNAME)
	raise
finally:
	os.chdir(WORK_PATH)

class BrailleDisplayDriver(braille.BrailleDisplayDriver):
	name = "seikamini"
	# Translators: The name of a series of braille displays.
	description = _("Seika notetakers (Mini16, Mini24, V6 and V7)")

	numCells = 0
	# numBtns = 0

	@classmethod
	def check(cls):
		return bool(seikaDll)

	def seika_errcheck(res, func, args):
		if res != 0:
			raise RuntimeError("seikamini: %s: code %d" % (func.__name__, res))
		return res

	def __init__(self):
		super(BrailleDisplayDriver, self).__init__()
		pint = c_int * 1
		nCells = pint(0)
		nBut = pint(0)

		# seikaDll.BrailleOpen.errcheck=self.seika_errcheck
		seikaDll.BrailleOpen.restype=c_int
		seikaDll.BrailleOpen.argtype=(c_int, c_int)

		# seikaDll.GetBrailleDisplayInfo.errcheck=self.seika_errcheck
		seikaDll.GetBrailleDisplayInfo.restype=c_int
		seikaDll.GetBrailleDisplayInfo.argtype=(c_void_p, c_void_p)

		# seikaDll.UpdateBrailleDisplay.errcheck=self.seika_errcheck
		seikaDll.UpdateBrailleDisplay.restype=c_int
		seikaDll.UpdateBrailleDisplay.argtype=(c_char_p, c_int)

		# seikaDll.GetBrailleKey.errcheck=self.seika_errcheck
		seikaDll.GetBrailleKey.restype=c_int
		seikaDll.GetBrailleKey.argtype=(c_void_p, c_void_p)

		seikaDll.BrailleClose.restype=c_int

		if seikaDll.BrailleOpen(2, 0): # test USB
			seikaDll.GetBrailleDisplayInfo(nCells, nBut)
			log.info("seikamini an USB-HID, Cells {c} Buttons {b}".format(c=nCells[0], b=nBut[0]))
			self.numCells=nCells[0]
			# self.numBtns=nBut[0]
		else: # search the blutooth ports
			for portInfo in sorted(hwPortUtils.listComPorts(onlyAvailable=True), key=lambda item: "bluetoothName" in item):
				port = portInfo["port"]
				hwID = portInfo["hardwareID"]
				if not hwID.startswith(r"BTHENUM"): # Bluetooth Ports
					continue
				bName = ""
				try:
					bName = portInfo["bluetoothName"]
				except KeyError:
					continue
				if not bName.startswith(r"TSM"): # seikamini and then the 4-Digits
					continue

				try:
					pN = port.split("COM")[1]
				except IndexError:
					pN = "0"
				portNum = int(pN)
				log.info("seikamini test {c}, {b}".format(c=port, b=bName))
		
				if seikaDll.BrailleOpen(0, portNum):
					seikaDll.GetBrailleDisplayInfo(nCells, nBut)
					log.info("seikamini via Bluetooth {p} Cells {c} Buttons {b}".format(p=port, c=nCells[0], b=nBut[0]))
					self.numCells=nCells[0]
					# self.numBtns=nBut[0]
					break
			else:
				raise RuntimeError("No MINI-SEIKA display found")
		self._readTimer = wx.PyTimer(self.handleResponses)
		self._readTimer.Start(READ_INTERVAL)

	def terminate(self):
		try:
			super(BrailleDisplayDriver, self).terminate()
			self._readTimer.Stop()
			self._readTimer = None
		finally:
			seikaDll.BrailleClose()

	def display(self, cells):
		# every transmitted line consists of the preamble SEIKA_SENDHEADER and the Cells
		line = to_bytes(cells)
		line += b'\0' * (self.numCells - len(line))
		seikaDll.UpdateBrailleDisplay(line, self.numCells)

	def handleResponses(self):
		pint = c_int * 1
		nKey = pint(0)
		nRou = pint(0)
		if seikaDll.GetBrailleKey(nKey, nRou):
			Rou = nRou[0]
			Btn = (nKey[0] & 0xff) << 16 # unused, because Mini Seika has no Btn ....
			Brl = (nKey[0] >> 8) & 0xff
			Key = (nKey[0] >> 16) & 0xffff
			log.debug("Seika Brl {brl} Key {c} Buttons {b} Route {r}".format(brl=Brl, c=Key, b=Btn, r=Rou))
			if Key or Brl or Rou:
				gesture = InputGesture(Key, Brl, Rou)
				try:
					inputCore.manager.executeGesture(gesture)
				except inputCore.NoInputGestureAction:
					log.debug("No action for keys {0}".format(gesture.id), exc_info=True)


	gestureMap = inputCore.GlobalGestureMap({
		"globalCommands.GlobalCommands": {
			"braille_routeTo": ("br(seikamini):routing",),
			"braille_scrollBack": ("br(seikamini):LB",),
			"braille_scrollForward": ("br(seikamini):RB",),
			"braille_previousLine": ("br(seikamini):LJ_UP",),
			"braille_nextLine": ("br(seikamini):LJ_DOWN",),
			"braille_toggleTether": ("br(seikamini):LJ_CENTER",),
			"sayAll": ("br(seikamini):SPACE+BACKSPACE",),
			"showGui": ("br(seikamini):RB+LB",),
			"kb:tab": ("br(seikamini):LJ_RIGHT",),
			"kb:shift+tab": ("br(seikamini):LJ_LEFT",),
			"kb:upArrow": ("br(seikamini):RJ_UP",),
			"kb:downArrow": ("br(seikamini):RJ_DOWN",),
			"kb:leftArrow": ("br(seikamini):RJ_LEFT",),
			"kb:rightArrow": ("br(seikamini):RJ_RIGHT",),
			"kb:shift+upArrow": ("br(seikamini):SPACE+RJ_UP",),
			"kb:shift+downArrow": ("br(seikamini):SPACE+RJ_DOWN",),
			"kb:shift+leftArrow": ("br(seikamini):SPACE+RJ_LEFT",),
			"kb:shift+rightArrow": ("br(seikamini):SPACE+RJ_RIGHT",),
			"kb:escape": ("br(seikamini):SPACE+RJ_CENTER",),
			"kb:shift+upArrow": ("br(seikamini):BACKSPACE+RJ_UP",),
			"kb:shift+downArrow": ("br(seikamini):BACKSPACE+RJ_DOWN",),
			"kb:shift+leftArrow": ("br(seikamini):BACKSPACE+RJ_LEFT",),
			"kb:shift+rightArrow": ("br(seikamini):BACKSPACE+RJ_RIGHT",),
			"kb:windows": ("br(seikamini):BACKSPACE+RJ_CENTER",),
			"kb:pageup": ("br(seikamini):SPACE+LJ_RIGHT",),
			"kb:pagedown": ("br(seikamini):SPACE+LJ_LEFT",),
			"kb:home": ("br(seikamini):SPACE+LJ_UP",),
			"kb:end": ("br(seikamini):SPACE+LJ_DOWN",),
			"kb:control+home": ("br(seikamini):BACKSPACE+LJ_UP",),
			"kb:control+end": ("br(seikamini):BACKSPACE+LJ_DOWN",),
			"kb:enter": ("br(seikamini):RJ_CENTER",),
		},
	})


class InputGesture(braille.BrailleDisplayGesture, brailleInput.BrailleInputGesture):
	source = BrailleDisplayDriver.name

	def __init__(self, keys, dots, routing):
		super(braille.BrailleDisplayGesture, self).__init__()
		# see what thumb keys are pressed:
		names = []
		if routing:
			if keys == dots == 0: # Pure routing gesture
				self.routingIndex = routing - 1
				names.append("routing")
			else:
				names.append("r%d" % routing)
		else:
			if keys in (0x0, 0x1, 0x2):
				self.dots = dots
				# when BACKSPACE and/or SPACE is pressed, the gesture may be dots + space
				if keys:
					self.space = True
		names.extend(_keyNames[k] for k in _keyNames if (k & keys))
		names.extend(_dotNames[k] for k in _dotNames if (k & dots))
		self.id = "+".join(names)
		log.debug("Keys {0}".format(self.id))
