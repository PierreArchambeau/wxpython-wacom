import wx
from wx import glcanvas
from OpenGL import GL


class PressureCanvas(glcanvas.GLCanvas):
    def __init__(self, parent, on_pressure_change):
        super().__init__(parent, attribList=[glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER, glcanvas.WX_GL_DEPTH_SIZE, 16, 0])
        self._context = glcanvas.GLContext(self)
        self._initialized = False
        self._pressure = 0.0
        self._position = wx.Point(0, 0)
        self._on_pressure_change = on_pressure_change

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)

        for evt_name in (
            "EVT_TABLET",
            "EVT_TABLET_DOWN",
            "EVT_TABLET_UP",
            "EVT_TABLET_ENTER",
            "EVT_TABLET_LEAVE",
            "EVT_TABLET_MOTION",
        ):
            evt = getattr(wx, evt_name, None)
            if evt is not None:
                self.Bind(evt, self.on_tablet_event)

    @property
    def pressure(self):
        return self._pressure

    @property
    def position(self):
        return self._position

    def _extract_pressure(self, event):
        value = None
        for name in ("GetPressure", "Pressure", "GetRawPressure"):
            attr = getattr(event, name, None)
            if callable(attr):
                value = attr()
                break
            if attr is not None and not callable(attr):
                value = attr
                break

        if value is None:
            return 1.0 if event.LeftIsDown() else 0.0

        try:
            pressure = float(value)
        except (TypeError, ValueError):
            return 0.0

        if pressure > 1.0:
            max_pressure = None
            getter = getattr(event, "GetPressureMax", None)
            if callable(getter):
                try:
                    max_pressure = float(getter())
                except (TypeError, ValueError):
                    max_pressure = None

            if not max_pressure or max_pressure <= 0:
                max_pressure = 1024.0
            pressure = pressure / max_pressure

        return max(0.0, min(pressure, 1.0))

    def _update_input(self, event):
        self._position = event.GetPosition()
        self._pressure = self._extract_pressure(event)
        self._on_pressure_change(self._position, self._pressure)
        self.Refresh(False)

    def on_mouse_motion(self, event):
        self._update_input(event)
        event.Skip()

    def on_mouse_down(self, event):
        self._update_input(event)
        self.SetFocus()
        event.Skip()

    def on_mouse_up(self, event):
        self._update_input(event)
        event.Skip()

    def on_tablet_event(self, event):
        self._update_input(event)
        event.Skip()

    def on_resize(self, _event):
        self.Refresh(False)

    def _init_gl(self):
        self.SetCurrent(self._context)
        GL.glClearColor(0.08, 0.08, 0.11, 1.0)
        self._initialized = True

    def _setup_projection(self):
        width, height = self.GetClientSize()
        width = max(width, 1)
        height = max(height, 1)
        GL.glViewport(0, 0, width, height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, width, 0, height, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        return width, height

    def _draw_pressure_bar(self, width, height):
        bar_w = max(24, int(width * 0.08))
        bar_h = int(height * 0.7)
        x0 = width - bar_w - 24
        y0 = int(height * 0.15)

        GL.glColor3f(0.25, 0.25, 0.3)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex2f(x0, y0)
        GL.glVertex2f(x0 + bar_w, y0)
        GL.glVertex2f(x0 + bar_w, y0 + bar_h)
        GL.glVertex2f(x0, y0 + bar_h)
        GL.glEnd()

        filled_h = bar_h * self._pressure
        GL.glColor3f(0.1, 0.7, 1.0)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex2f(x0, y0)
        GL.glVertex2f(x0 + bar_w, y0)
        GL.glVertex2f(x0 + bar_w, y0 + filled_h)
        GL.glVertex2f(x0, y0 + filled_h)
        GL.glEnd()

    def _draw_pressure_circle(self, width, height):
        radius = 10 + (self._pressure * min(width, height) * 0.25)
        cx = width * 0.35
        cy = height * 0.5
        segments = 64

        GL.glColor3f(0.95, 0.95 - (self._pressure * 0.5), 0.3)
        GL.glBegin(GL.GL_TRIANGLE_FAN)
        GL.glVertex2f(cx, cy)
        for i in range(segments + 1):
            angle = (i / segments) * 6.28318530718
            GL.glVertex2f(cx + radius * wx.Cos(angle), cy + radius * wx.Sin(angle))
        GL.glEnd()

    def on_paint(self, _event):
        if not self._initialized:
            self._init_gl()

        self.SetCurrent(self._context)
        width, height = self._setup_projection()

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self._draw_pressure_bar(width, height)
        self._draw_pressure_circle(width, height)

        self.SwapBuffers()


class PressureFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="wxPython + OpenGL Wacom Pressure Test", size=(900, 600))
        self.CreateStatusBar()
        self.SetStatusText("Déplacez le stylet et appuyez pour tester la pression")

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.canvas = PressureCanvas(panel, self._on_pressure_change)
        info = wx.StaticText(panel, label="Pression: 0.00 | Position: (0, 0)")

        font = info.GetFont()
        font.MakeBold()
        info.SetFont(font)

        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(info, 0, wx.EXPAND | wx.ALL, 8)
        panel.SetSizer(sizer)

        self._info_label = info
        self.Centre()

    def _on_pressure_change(self, pos, pressure):
        message = f"Pression: {pressure:.3f} | Position: ({pos.x}, {pos.y})"
        self._info_label.SetLabel(message)
        self.SetStatusText(message)


class PressureApp(wx.App):
    def OnInit(self):
        frame = PressureFrame()
        frame.Show(True)
        self.SetTopWindow(frame)
        return True


if __name__ == "__main__":
    app = PressureApp(False)
    app.MainLoop()
