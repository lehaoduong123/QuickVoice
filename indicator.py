"""
QuickVoice Recording Indicator
===============================
A small floating overlay at the top-center of the screen
that shows when QuickVoice is recording.

Uses native macOS APIs (AppKit) for a clean, always-on-top overlay.
"""

import threading

import objc
from AppKit import (
    NSApplication,
    NSWindow,
    NSView,
    NSColor,
    NSFont,
    NSScreen,
    NSBezierPath,
    NSMutableParagraphStyle,
    NSMutableDictionary,
    NSForegroundColorAttributeName,
    NSFontAttributeName,
    NSParagraphStyleAttributeName,
    NSWindowStyleMaskBorderless,
    NSBackingStoreBuffered,
    NSFloatingWindowLevel,
    NSString,
)
from Foundation import NSMakeRect, NSTimer, NSRunLoop, NSDefaultRunLoopMode
from PyObjCTools import AppHelper

class RecordingIndicatorView(NSView):
    """Custom view that draws a red recording pill with pulsing animation."""

    def initWithFrame_(self, frame):
        self = objc.super(RecordingIndicatorView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._alpha = 1.0
        self._increasing = False
        self._label = "● REC"
        return self

    def drawRect_(self, rect):
        """Draw the recording indicator pill."""
        # Rounded rect background
        bg_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            rect, 12, 12
        )

        # Semi-transparent dark background
        bg_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(
            0.1, 0.1, 0.1, 0.85
        )
        bg_color.setFill()
        bg_path.fill()

        # Red recording dot + text
        text_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(
            1.0, 0.3, 0.3, self._alpha
        )

        attrs = NSMutableDictionary.alloc().init()
        attrs[NSForegroundColorAttributeName] = text_color
        attrs[NSFontAttributeName] = NSFont.systemFontOfSize_weight_(13, 0.5)

        para = NSMutableParagraphStyle.alloc().init()
        para.setAlignment_(1)  # Center
        attrs[NSParagraphStyleAttributeName] = para

        ns_string = NSString.stringWithString_(self._label)
        text_rect = NSMakeRect(0, 4, rect.size.width, rect.size.height - 4)
        ns_string.drawInRect_withAttributes_(text_rect, attrs)

    def setLabel_(self, label):
        self._label = label
        self.setNeedsDisplay_(True)

    def pulse(self):
        """Animate the alpha for a pulsing effect."""
        if self._increasing:
            self._alpha += 0.08
            if self._alpha >= 1.0:
                self._alpha = 1.0
                self._increasing = False
        else:
            self._alpha -= 0.08
            if self._alpha <= 0.4:
                self._alpha = 0.4
                self._increasing = True
        self.setNeedsDisplay_(True)


class RecordingIndicator:
    """Manages the floating recording indicator window."""

    def __init__(self):
        self._window = None
        self._view = None
        self._timer = None
        self._create_window()

    def _create_window(self):
        """Create the floating indicator window (must be called on main thread)."""
        # Window size and position (top-center of screen)
        width, height = 80, 28
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        x = (screen_frame.size.width - width) / 2
        y = screen_frame.size.height - height - 5  # 5px from top

        frame = NSMakeRect(x, y, width, height)

        # Create borderless, transparent, always-on-top window
        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setLevel_(NSFloatingWindowLevel + 1)  # Above everything
        self._window.setOpaque_(False)
        self._window.setBackgroundColor_(NSColor.clearColor())
        self._window.setIgnoresMouseEvents_(True)  # Click-through
        self._window.setCollectionBehavior_(1 << 0 | 1 << 4)  # All spaces + fullscreen

        # Create the custom view
        self._view = RecordingIndicatorView.alloc().initWithFrame_(
            NSMakeRect(0, 0, width, height)
        )
        self._window.setContentView_(self._view)

    def show(self):
        """Show the recording indicator."""
        def _show_on_main():
            self._view.setLabel_("● REC")
            self._window.orderFront_(None)
            # Start pulse animation
            self._timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.05, self._view, objc.selector(RecordingIndicatorView.pulse, signature=b"v@:"),
                None, True,
            )
        AppHelper.callAfter(_show_on_main)

    def show_transcribing(self):
        """Switch indicator to 'transcribing' state."""
        def _update():
            if self._timer:
                self._timer.invalidate()
                self._timer = None
            self._view._alpha = 1.0
            self._view.setLabel_("⏳")
        AppHelper.callAfter(_update)

    def hide(self):
        """Hide the recording indicator."""
        def _hide_on_main():
            if self._timer:
                self._timer.invalidate()
                self._timer = None
            self._window.orderOut_(None)
        AppHelper.callAfter(_hide_on_main)

