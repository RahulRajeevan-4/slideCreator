import uno
import time

print("Connecting to LibreOffice...")

# Connect
local_ctx = uno.getComponentContext()
resolver = local_ctx.ServiceManager.createInstanceWithContext(
    "com.sun.star.bridge.UnoUrlResolver", local_ctx
)

ctx = resolver.resolve(
    "uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext"
)

print("Connected!")

smgr = ctx.ServiceManager
desktop = smgr.createInstanceWithContext(
    "com.sun.star.frame.Desktop", ctx
)

# Create presentation
doc = desktop.loadComponentFromURL(
    "private:factory/simpress", "_blank", 0, ()
)

time.sleep(1)

slides = doc.getDrawPages()
slide = slides.getByIndex(0)

# Ensure layout
slide.setPropertyValue("Layout", 1)
time.sleep(1)

print("Total shapes on slide:", slide.getCount())

text_set = False

# Iterate shapes correctly
for i in range(slide.getCount()):
    shape = slide.getByIndex(i)

    if shape.supportsService("com.sun.star.drawing.Text"):
        shape.String = "HI"
        shape.CharHeight = 80
        print("Text inserted into existing shape")
        text_set = True
        break

# Fallback
if not text_set:
    print("No text shape found, creating one...")

    textbox = doc.createInstance("com.sun.star.drawing.TextShape")

    textbox.setPosition(
        uno.createUnoStruct("com.sun.star.awt.Point", 2000, 2000)
    )
    textbox.setSize(
        uno.createUnoStruct("com.sun.star.awt.Size", 20000, 8000)
    )

    textbox.String = "HI"
    textbox.CharHeight = 120

    slide.add(textbox)

# Force refresh
controller = doc.getCurrentController()
frame = controller.getFrame()
window = frame.getContainerWindow()
window.invalidate(0)

print("Done. The 'HI' better be there now.")