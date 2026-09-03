# encoding: utf-8
from __future__ import division, print_function, unicode_literals

###########################################################################################################
#
#
#	Reporter Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Reporter
#
#
###########################################################################################################

import objc
from GlyphsApp import Glyphs, GSControlLayer, subtractPoints
from GlyphsApp.plugins import *
from Foundation import NSColor, NSPointInRect, NSPoint, NSRect, NSInsetRect
from AppKit import NSEvent, NSEventModifierFlagControl, NSEventModifierFlagCommand, NSBezierPath

class KernIndicator(ReporterPlugin):

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Kerning Values',
			'de': u'Kerning-Werte',
			'es': u'valores de Kerning',
			'fr': u'les valeurs de crénage',
		})

		# offset value
		Glyphs.registerDefault( "com.mekkablue.KernIndicator.offset", -50 )
		if Glyphs.defaults["com.mekkablue.KernIndicator.offset"] is None:
			del Glyphs.defaults["com.mekkablue.KernIndicator.offset"]

	@objc.python_method
	def foreground(self, layer):
		scale = self.getScale()
		if not 0.0299 < scale < 0.9001:
			return

		font = layer.font()
		if not font: # sometimes font is empty, don't know why
			return

		tab = font.currentTab
		tabView = tab.graphicView()
		if not tabView.doKerning():
			# don't draw if kerning is off
			return

		# Don't show kerning values when Control and Command keys are held down simultaneously
		if (NSEvent.modifierFlags() & NSEventModifierFlagControl) and (NSEvent.modifierFlags() & NSEventModifierFlagCommand):
			return

		positiveColor = NSColor.systemOrangeColor()
		negativeColor = NSColor.systemBlueColor()
		if hasattr(Glyphs, 'versionNumber') and Glyphs.versionNumber >= 3 :
			# GLYPHS 3
			offset = layer.master.defaultAscender()
		else:
			# GLYPHS 2
			offset = layer.master.ascender

		try:
			offset += int(Glyphs.defaults["com.mekkablue.KernIndicator.offset"])
		except:
			pass

		# go through tab content
		layerCount = tabView.cachedLayerCount()
		if layerCount>1:
			viewPort = NSInsetRect(tab.viewPort,-20,-20)
			viewPort.origin.y -= offset*scale
			activePosition = tabView.activePosition()
			previousLayer = tabView.cachedGlyphAtIndex_(0)
			for i in range(1,layerCount):
				thisLayer = tabView.cachedGlyphAtIndex_(i)
				thisLayerPosition = tabView.cachedPositionAtIndex_(i)
				if NSPointInRect( thisLayerPosition, viewPort ) and type(thisLayer) != GSControlLayer and type(previousLayer) != GSControlLayer:
					previousMasterID = previousLayer.master.id
					thisMasterID = thisLayer.master.id
					if thisMasterID == previousMasterID:
						leftGlyph = previousLayer.glyph()
						rightGlyph = thisLayer.glyph()
						if leftGlyph and rightGlyph:
							kerningValue = font.kerningForFontMasterID_firstGlyph_secondGlyph_( thisMasterID, leftGlyph, rightGlyph )
							kerningFound = kerningValue is not None and kerningValue < 10000 #notfound

							independentPairs = thisLayer.master.userData["KernOnIndependentPairs"]
							isIndependent = bool(independentPairs) and (leftGlyph.name + " " + rightGlyph.name) in independentPairs

							if kerningFound or isIndependent:
								offsetVector = subtractPoints(thisLayerPosition, activePosition)
								textPoint = NSPoint( offsetVector.x/self.getScale() - 0.5*(kerningValue if kerningFound else 0), offsetVector.y/self.getScale() + offset )
								if kerningFound and kerningValue != 0:
									if kerningValue < 0:
										self.drawTextAtPoint( str(int(kerningValue)), textPoint, fontColor=negativeColor, align="bottomcenter" )
									else:
										self.drawTextAtPoint( str(int(kerningValue)), textPoint, fontColor=positiveColor, align="bottomcenter" )
								if isIndependent:
									self.drawIndependentIndicator(textPoint)

				previousLayer = thisLayer

	@objc.python_method
	def drawIndependentIndicator(self, textPoint):
		scale = self.getScale()
		lineLength = 7.0/scale
		lineGap = 3.0/scale
		x = textPoint.x
		y1 = textPoint.y - lineGap
		y2 = y1 - lineLength
		NSColor.tertiaryLabelColor().set()
		NSBezierPath.setDefaultLineWidth_(1.2/scale)
		NSBezierPath.strokeLineFromPoint_toPoint_( NSPoint(x, y1), NSPoint(x, y2) )

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
