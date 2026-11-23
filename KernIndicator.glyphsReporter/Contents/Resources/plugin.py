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
from GlyphsApp.plugins import ReporterPlugin
from Foundation import NSColor, NSPoint, NSRect, NSAttributedString
from AppKit import NSEvent, NSEventModifierFlagControl, NSEventModifierFlagCommand, NSBezierPath, NSFont, NSFontAttributeName, NSForegroundColorAttributeName

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
			activePosition = tabView.activePosition()
			if Glyphs.versionNumber >= 4:
				# Glyphs 4 renamed cachedGlyphAtIndex_ and added the writing direction to the kerning lookup
				direction = tab.writingDirection()
				previousLayer = tabView.cachedLayerAtIndex_(0)
			else:
				previousLayer = tabView.cachedGlyphAtIndex_(0)
			for i in range(1,layerCount):
				if Glyphs.versionNumber >= 4:
					thisLayer = tabView.cachedLayerAtIndex_(i)
				else:
					thisLayer = tabView.cachedGlyphAtIndex_(i)
				thisLayerPosition = tabView.cachedPositionAtIndex_(i)
				# no culling against tab.viewPort: in Glyphs 4 it left values only in a zone
				# near the bottom center of the window (see forum report)
				if not isinstance(thisLayer, GSControlLayer) and not isinstance(previousLayer, GSControlLayer):
					previousMasterID = previousLayer.master.id
					thisMasterID = thisLayer.master.id
					if thisMasterID == previousMasterID:
						leftGlyph = previousLayer.glyph()
						rightGlyph = thisLayer.glyph()
						if leftGlyph and rightGlyph:
							if Glyphs.versionNumber >= 4:
								kerningValue = font.kerningForFontMasterID_firstGlyph_secondGlyph_direction_( thisMasterID, leftGlyph, rightGlyph, direction )
							else:
								kerningValue = font.kerningForFontMasterID_firstGlyph_secondGlyph_( thisMasterID, leftGlyph, rightGlyph )
							kerningFound = kerningValue is not None and kerningValue < 10000 #notfound

							pairName = leftGlyph.name + " " + rightGlyph.name
							independentPairs = thisLayer.master.userData["KernOnIndependentPairs"]
							isIndependent = bool(independentPairs) and pairName in independentPairs
							modelPairs = thisLayer.master.userData["KernOnModels"]
							isModelPair = bool(modelPairs) and pairName in modelPairs
							userSetAutopairs = thisLayer.master.userData["KernOnUserSetAutopairs"]
							isUserSetAutopair = bool(userSetAutopairs) and pairName in userSetAutopairs

							if kerningFound or isIndependent:
								offsetVector = subtractPoints(thisLayerPosition, activePosition)
								textPoint = NSPoint( offsetVector.x/self.getScale() - 0.5*(kerningValue if kerningFound else 0), offsetVector.y/self.getScale() + offset )
								if kerningFound and kerningValue != 0:
									textColor = negativeColor if kerningValue < 0 else positiveColor
									if isModelPair:
										self.drawBoldTextAtPoint( str(int(kerningValue)), textPoint, fontColor=textColor, align="bottomcenter" )
									else:
										self.drawTextAtPoint( str(int(kerningValue)), textPoint, fontColor=textColor, align="bottomcenter" )
									if isUserSetAutopair:
										self.drawInvertedVIndicator( textPoint, textColor )
								if isIndependent:
									if kerningFound and kerningValue != 0:
										dotColor = negativeColor if kerningValue < 0 else positiveColor
									else:
										dotColor = NSColor.systemPinkColor()
									self.drawIndependentIndicator(textPoint, dotColor)

				previousLayer = thisLayer

	@objc.python_method
	def drawIndependentIndicator(self, textPoint, dotColor):
		scale = self.getScale()
		dotDiameter = 3.0/scale
		dotGap = 1.0/scale
		x = textPoint.x - 0.5*dotDiameter
		y = textPoint.y - dotGap - dotDiameter
		dotColor.set()
		NSBezierPath.bezierPathWithOvalInRect_( NSRect((x, y), (dotDiameter, dotDiameter)) ).fill()

	@objc.python_method
	def drawInvertedVIndicator(self, textPoint, lineColor):
		scale = self.getScale()
		width = 6.0/scale
		height = 3.0/scale
		gap = 1.0/scale
		yTop = textPoint.y - gap
		yBottom = yTop - height
		xLeft = textPoint.x - 0.5*width
		xRight = textPoint.x + 0.5*width
		path = NSBezierPath.bezierPath()
		path.moveToPoint_( NSPoint(xLeft, yBottom) )
		path.lineToPoint_( NSPoint(textPoint.x, yTop) )
		path.lineToPoint_( NSPoint(xRight, yBottom) )
		path.setLineWidth_(1.0/scale)
		lineColor.set()
		path.stroke()

	@objc.python_method
	def drawBoldTextAtPoint(self, text, textPosition, fontSize=10.0, fontColor=NSColor.textColor(), align="bottomleft"):
		alignment = {
			'topleft': 6,
			'topcenter': 7,
			'topright': 8,
			'left': 3,
			'center': 4,
			'right': 5,
			'bottomleft': 0,
			'bottomcenter': 1,
			'bottomright': 2
		}
		currentZoom = self.getScale()
		fontAttributes = {
			NSFontAttributeName: NSFont.boldSystemFontOfSize_(fontSize / currentZoom),
			NSForegroundColorAttributeName: fontColor,
		}
		displayText = NSAttributedString.alloc().initWithString_attributes_(text, fontAttributes)
		textAlignment = alignment.get(align, 6)
		displayText.drawAtPoint_alignment_(textPosition, textAlignment)

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
