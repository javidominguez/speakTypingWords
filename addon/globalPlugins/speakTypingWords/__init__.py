# -*- coding: UTF-8 -*-

"""
NVDA reads the entire word if it is modified, instead of just the added part, which is the default behavior.

This code has been extracted from NVDAExtensionGlobalPlugin add-on by Paulber19.
https://github.com/paulber19/NVDAExtensionGlobalPlugin
According to the GNU General Public License.
All credit belongs to its original authors: Paulber19 and Leonardder.

The function that executes this code was removed from the original addon in version 13.3, however, some users missed it.
This fork recovers the function by adapting it to work independently in a small addon for those users.

Copyright of this adaptation by Javi Dominguez (2024)
"""

import globalPluginHandler
import speech
import textInfos
import config
import editableText
import contentRecog.recogUi
import eventHandler
import globalVars
from logHandler import log 
from controlTypes import *
from typing import Tuple, Optional

NON_BREAKING_SPACE = 160
_classNamesToCheck = [
	"Edit", "RichEdit", "RichEdit20", "REComboBox20W", "RICHEDIT50W", "RichEditD2DPT",
	"Scintilla", "TScintilla", "AkelEditW", "AkelEditA", "_WwG", "_WwN", "_WwO",
	"SALFRAME", "ConsoleWindowClass"]
_rolesToCheck = [ROLE_DOCUMENT, ROLE_EDITABLETEXT, ROLE_TERMINAL]
def chooseNVDAObjectOverlayClasses(obj, clsList):
	useRecogResultNVDAObjectEx = False
	useEditableTextUseTextInfoToSpeakTypedWords = False
	for cls in clsList:
		if contentRecog.recogUi.RecogResultNVDAObject in cls.__mro__:
			useRecogResultNVDAObjectEx = True
		if editableText.EditableText in cls.__mro__:
			useEditableTextUseTextInfoToSpeakTypedWords = True

	if useRecogResultNVDAObjectEx:
		clsList.insert(0, RecogResultNVDAObjectEx)
	# to fix the Access8Math  problem with the "alt+m" virtual menu
	# for the obj, the informations are bad: role= Window, className= Edit, not states
	#  tand with no better solution, we check the length of obj.states
	elif (obj.role in _rolesToCheck or obj.windowClassName in _classNamesToCheck) and len(obj.states):
		# newer revisions of Windows 11 build 22000 moves focus to emoji search field.
		# However this means NVDA's own edit field scripts will override emoji panel commands.
		# Therefore remove text field movement commands so emoji panel commands can be used directly.
		if hasattr(obj, "UIAAutomationId")\
			and obj.UIAAutomationId == "Windows.Shell.InputApp.FloatingSuggestionUI.DelegationTextBox":
			pass
		else:
			if True: # toggleTypedWordSpeakingEnhancementAdvancedOption(False) and useEditableTextUseTextInfoToSpeakTypedWords:
				clsList.insert(0, EditableTextUseTextInfoToSpeakTypedWords)
			else:
				clsList.insert(0, EditableTextEx)
		return

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super(GlobalPlugin, self).__init__()

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if globalVars.appArgs.secure == False and hasattr(obj, "windowClassName"):
			chooseNVDAObjectOverlayClasses(obj, clsList)
		
class EditableTextEx(editableText.EditableText):
	characterTyped = False
	_commandToScript = {
		"copy": "copyToClipboard",
		"cut": "cutAndCopyToClipboard",
		"paste": "pasteFromClipboard",
		"undo": "undo",
	}

	def getSelectionInfo(self):
		obj = api.getFocusObject()
		treeInterceptor = obj.treeInterceptor
		if hasattr(treeInterceptor, 'TextInfo') and not treeInterceptor.passThrough:
			obj = treeInterceptor
		try:
			info = obj.makeTextInfo(textInfos.POSITION_SELECTION)
		except (RuntimeError, NotImplementedError):
			info = None
		if not info or info.isCollapsed:
			return None
		return info

	def script_copyToClipboard(self, gesture):
		def callback(gesture):
			clearDelayScriptTask()
			info = self.getSelectionInfo()
			if not info:
				# Translators: Reported when there is no text selected (for copying).
				ui.message(NVDAString("No selection"))
				gesture.send()
				return

			def finaly():
				cm = clipboard.ClipboardManager()
				gesture.send()
				time.sleep(0.1)
				if cm.changed():
					queueHandler.queueFunction(
						queueHandler.eventQueue,
						ui.message, _msgCopy)
			# to check if clipboard has changed, we, now (nvda 2023.2), must use a thread !!!!
			from threading import Thread
			Thread(target=finaly).start()

		stopDelayScriptTask()
		# to filter out too fast script calls while holding down the command gesture.
		delayScriptTaskWithDelay(80, callback, gesture)

	def script_cutAndCopyToClipboard(self, gesture):
		def callback():
			clearDelayScriptTask()
			if STATE_READONLY in self.states or (
				STATE_EDITABLE not in self.states
				and STATE_MULTILINE not in self.states):
				gesture.send()
				return
			info = self.getSelectionInfo()
			if not info:
				# Translators: Reported when there is no text selected (for copying).
				ui.message(NVDAString("No selection"))
				gesture.send()
				return
			cm = clipboard.ClipboardManager()
			gesture.send()
			time.sleep(0.1)
			if cm.changed():
				queueHandler.queueFunction(
					queueHandler.eventQueue,
					ui.message, _msgCut)

		stopDelayScriptTask()
		# to filter out too fast script calls while holding down the command gesture.
		delayScriptTaskWithDelay(80, callback)

	def script_pasteFromClipboard(self, gesture):
		def callback():
			clearDelayScriptTask()
			if (
				STATE_READONLY in self.states or (
				STATE_EDITABLE not in self.states
				and not STATE_MULTILINE)):
				gesture.send()
				return
			cm = clipboard.ClipboardManager()
			time.sleep(0.1)
			if cm.isEmpty:
				# Translators: message to report clipboard is empty
				ui.message(_("Clipboard is empty"))
				gesture.send()
				return
			queueHandler.queueFunction(
				queueHandler.eventQueue,
				ui.message, _msgPaste)
			queueHandler.queueFunction(
				queueHandler.eventQueue,
				self.processGesture, textInfos.UNIT_LINE, gesture)

		stopDelayScriptTask()
		# to filter out too fast script calls while holding down the command gesture.
		delayScriptTaskWithDelay(80, callback)

	def processGesture(self, unit, gesture):
		try:
			info = self.makeTextInfo(textInfos.POSITION_CARET)
		except Exception:
			gesture.send()
			return
		bookmark = info.bookmark
		info.expand(textInfos.UNIT_WORD)
		word = info.text
		gesture.send()
		# We'll try waiting for the caret to move, but we don't care if it doesn't.
		caretMoved, newInfo = self._hasCaretMoved(bookmark, retryInterval=0.01, timeout=2.0, origWord=word)
		self._caretScriptPostMovedHelper(unit, gesture, newInfo)
		braille.handler.handleCaretMove(self)

	def script_undo(self, gesture):
		def callback():
			clearDelayScriptTask()
			if (
				STATE_READONLY in self.states or (
				STATE_EDITABLE not in self.states
				and not STATE_MULTILINE)):
				gesture.send()
				return
			queueHandler.queueFunction(
				queueHandler.eventQueue,
				ui.message, _msgUnDo)
			gesture.send()

		stopDelayScriptTask()
		# to filter out too fast script calls while holding down the command gesture.
		delayScriptTaskWithDelay(80, callback)

	def _caretScriptPostMovedHelper(self, speakUnit, gesture, info=None):
		# Forget the word currently being typed as the user has moved the caret somewhere else.
		speech.speech.clearTypedWordBuffer()
		super(EditableTextEx, self)._caretScriptPostMovedHelper(speakUnit, gesture, info)
		try:
			info = self.makeTextInfo(textInfos.POSITION_CARET)
		except Exception:
			return

	def _caretMovementScriptHelper(self, gesture, unit):
		# caret move but no character is typed. moving by arrow keys for exemple
		self.characterTyped = False
		try:
			info = self.makeTextInfo(textInfos.POSITION_CARET)
		except Exception:
			gesture.send()
			return
		bookmark = info.bookmark
		curLevel = config.conf["speech"]["symbolLevel"]
		gesture.send()
		caretMoved, newInfo = self._hasCaretMoved(bookmark)
		if not caretMoved and self.shouldFireCaretMovementFailedEvents:
			eventHandler.executeEvent("caretMovementFailed", self, gesture=gesture)
		self._caretScriptPostMovedHelper(unit, gesture, newInfo)
		config.conf["speech"]["symbolLevel"] = curLevel


# this code comes from leonardder  work for issue #8110, see at:
# Speak typed words based on TextInfo if possible #8110
class EditableTextUseTextInfoToSpeakTypedWords(EditableTextEx):
	#: A cached bookmark for the caret.
	#: This is cached until L{hasNewWordBeenTyped} clears it
	_cachedCaretBookmark = None

	def _caretScriptPostMovedHelper(self, speakUnit, gesture, info=None):
		# Forget the word currently being typed as the user has moved the caret somewhere else.
		speech.speech.clearTypedWordBuffer()
		# Also clear our latest cachetd caret bookmark
		# log.debug("_caretScriptPostMovedHelper clear cached caret bookmark")
		# self._clearCachedCaretBookmark()
		self.script_preTypedCharacter(None)
		super()._caretScriptPostMovedHelper(speakUnit, gesture, info)
		log.debug("cached caret bookmark updated: %s" % self._cachedCaretBookmark)

	def getScript(self, gesture):
		script = super().getScript(gesture)
		log.debug("script: %s" % script)
		if script or not self.useTextInfoToSpeakTypedWords:
			return script
		if gesture.isCharacter and gesture.vkCode != 231:
			return self.script_preTypedCharacter
		return None

	def script_preTypedCharacter(self, gesture):
		log.debug("script_preTypedCharacter")
		try:
			self._cachedCaretBookmark = self.caret.bookmark
			log.debug("cached caret bookmark set to: %s" % self._cachedCaretBookmark)
		except (LookupError, RuntimeError):
			pass  # Will still be None
		if gesture:
			gesture.send()

	def _get_caretMovementDetectionUsesEvents(self) -> bool:
		"""Returns whether or not to rely on caret and textChange events when
		finding out whether the caret position has changed after pressing a caret movement gesture.
		Note that if L{_useEvents_maxTimeoutMs} is elapsed,
		relying on events is no longer reliable in most situations.
		Therefore, any event should occur before that timeout elapses.
		"""
		# This class is a mixin that usually comes before other relevant classes in the mro.
		# Therefore, try to call super first, and if that fails, return the default (C{True}.
		try:
			res = super().caretMovementDetectionUsesEvents
			log.debug("_get_caretMovementDetectionUsesEvents super res: %s" % res)
			return res
		except AttributeError:
			log.debug("_get_caretMovementDetectionUsesEvents exception")
			return True

	def _get_useTextInfoToSpeakTypedWords(self) -> bool:
		"""Returns whether or not to use textInfo to announce newly typed words."""
		# This class is a mixin that usually comes before other relevant classes in the mro.
		# Therefore, try to call super first, and if that fails, return the default (C{True}.
		try:
			return super().useTextInfoToSpeakTypedWords
		except AttributeError:
			return True

	def _clearCachedCaretBookmark(self):
		self._cachedCaretBookmark = None
		log.debug("cached caret bookmark cleared: %s" % self._cachedCaretBookmark)

	def hasNewWordBeenTyped(self, wordSeparator: str) -> Tuple[Optional[bool], textInfos.TextInfo]:
		"""
		Returns whether a new word has been typed during this core cycle.
		It relies on self._cachedCaretBookmark, which is cleared after every core cycle.
		@param wordSeparator: The word seperator that has just been typed.
		@returns: a tuple containing the following two values:
			1. Whether a new word has been typed. This could be:
				* False if a caret move has been detected, but no word has been typed.
				* True if a caret move has been detected and a new word has been typed.
				* None if no caret move could be detected.
			2. If the caret has moved and a new word has been typed, a TextInfo
				expanded to the word that has just been typed.
		"""
		debug = False
		log.debug("hasNewWordBeenTyped: wordSeparator= %s (%s)" % (wordSeparator, ord(wordSeparator)))
		if not self.useTextInfoToSpeakTypedWords:
			return (None, None)
		bookmark = self._cachedCaretBookmark
		if not bookmark:
			log.debug("no bookmark")
			return (None, None)
		log.debug("bookmark: %s" % bookmark)
		self._clearCachedCaretBookmark()
		# on carriage return,  we don't want to announce the word  if no  character has been typed previously.
		if ord(wordSeparator) == 13 and not self.characterTyped:
			return (None, None)
		caretMoved, caretInfo = self._hasCaretMoved(bookmark, retryInterval=0.005, timeout=0.030)
		if not caretMoved or not caretInfo or not caretInfo.obj:
			log.debug("not caret moved")
			return (None, None)
		if debug:
			info = caretInfo.copy()
			info.expand(textInfos.UNIT_LINE)
			log.debug("caretInfo line: %s" % [ord(x) for x in info.text])
			log.debug("caretInfo: %s, bookmark= %s" % (info.text, info.bookmark))
		tempInfo = caretInfo.copy()
		if ord(wordSeparator) == 13:
			# in notepad, after return, caret bookmark is on new  line and crlf on previous line
			# lf is the last character of previous line
			info1 = caretInfo.copy()
			info1.collapse()
			# move to last character of previous line
			res = info1.move(textInfos.UNIT_CHARACTER, -1)
			if res:
				info1.expand(textInfos.UNIT_CHARACTER)
				log.debug("last character of previous line: %s" % [ord(x) for x in info1.text])
				# in notepad++, we get 2 characters and not oly one ???
				if len(info1.text) == 1 and ord(info1.text) == 10:  # character lf
					tempInfo.move(textInfos.UNIT_CHARACTER, -1)
			else:
				# no previous line
				return (False, None)

				# let's position on the last character typed
		res = tempInfo.move(textInfos.UNIT_CHARACTER, -2)
		if res != 0:
			tempInfo.expand(textInfos.UNIT_CHARACTER)
			ch = tempInfo.text
			log.debug("character caret-2: %s (%s)" % (ch, ord(ch)))
			# if there is a space (but no a Non-breaking space) before last character, return no word
			if len(ch) and ord(ch) != NON_BREAKING_SPACE and ch.isspace():
				log.debug("caret -2 is a space")
				return (False, None)
			# if the last character typed is not a letter or number, the word has been probably already reported
			if not ch.isalnum() and ord(ch) != NON_BREAKING_SPACE:
				log.debug("caret-2 is not alphanumericc")
				return (False, None)
		wordInfo = self.makeTextInfo(bookmark)
		if debug:
			info = wordInfo.copy()
			info.expand(textInfos.UNIT_WORD)
			log.debug("wordInfo: %s" % info.text)
		# The bookmark is positioned after the end of the word.
		# Therefore, we need to move it one character backwards.
		res = wordInfo.move(textInfos.UNIT_CHARACTER, -1)
		log.debug("wordInfo moved: %s, %s" % (res, wordInfo.text))
		wordInfo.expand(textInfos.UNIT_WORD)
		log.debug("wordInfo moved 2: %s, %s" % (res, wordInfo.text))
		diff = wordInfo.compareEndPoints(caretInfo, "endToStart")
		log.debug("diff: %s" % diff)
		# if diff >= 0 and not wordSeparator.isspace():
		if diff >= 0 and wordSeparator.isalnum():
			# This is no word boundary.
			return (False, None)
		if wordInfo.text.isspace():
			# There is only space, which is not considered a word.
			# For example, this can occur in Notepad++ when auto indentation is on.
			log.debug("Word before caret contains only spaces")
			return (None, None)
		caretInfo.collapse()
		wordInfo.setEndPoint(caretInfo, "endToStart")
		log.debug("word1: %s" % wordInfo.text)
		# with notepad editor, wordSeparator is at the end of word.  So we need to suppress it
		# not same thing with other editor as notepad++, wordpad, word.
		log.debug("word: %s, sep: %s" % (wordInfo.text, ord(wordSeparator)))
		if len(wordInfo.text) and not wordInfo.text[-1].isalnum():
			# the word is before the wordSeparator
			res = wordInfo.move(textInfos.UNIT_CHARACTER, -1, endPoint="end")
			log.debug("word2: %s, %s" % (res, wordInfo.text))
		return (True, wordInfo)

	def _get_caret(self):
		return self.makeTextInfo(textInfos.POSITION_CARET)

	def _updateSelectionAnchor(self, oldInfo, newInfo):
		# Only update the value if the selection changed.
		try:
			if newInfo.compareEndPoints(oldInfo, "startToStart") != 0:
				self.isTextSelectionAnchoredAtStart = False
			elif newInfo.compareEndPoints(oldInfo, "endToEnd") != 0:
				self.isTextSelectionAnchoredAtStart = True
		except Exception:
			pass

	def event_typedCharacter(self, ch: str):
		if (
			config.conf["documentFormatting"]["reportSpellingErrors"]
			and config.conf["keyboard"]["alertForSpellingErrors"]
			and (
				# Not alpha, apostrophe or control.
				ch.isspace() or (ch >= " " and ch not in "'\x7f" and not ch.isalpha())
			)
		):
			# Reporting of spelling errors is enabled and this character ends a word.
			self._reportErrorInPreviousWord()
		from .speechEx import speakTypedCharacters
		speakTypedCharacters(ch)
		# keep trace that a character has been typed
		self.characterTyped = True
		import winUser
		if (
			config.conf["keyboard"]["beepForLowercaseWithCapslock"]
			and ch.islower()
			and winUser.getKeyState(winUser.VK_CAPITAL) & 1
		):
			import tones
			tones.beep(3000, 40)


