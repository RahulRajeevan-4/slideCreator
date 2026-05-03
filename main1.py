import uno
import time
import urllib.request
import os

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

# ---- TITLE ----
title_box = doc.createInstance("com.sun.star.drawing.TextShape")
title_box.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", 2000, 1000))
title_box.setSize(uno.createUnoStruct("com.sun.star.awt.Size", 20000, 3000))

title_box.String = "Introduction to JavaScript"
title_box.CharHeight = 60

slide.add(title_box)

# ---- PARAGRAPH ----
para_box = doc.createInstance("com.sun.star.drawing.TextShape")
para_box.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", 2000, 5000))
para_box.setSize(uno.createUnoStruct("com.sun.star.awt.Size", 20000, 5000))

para_box.String = (
    "JavaScript is a versatile programming language used to build "
    "interactive and dynamic web applications. It runs in the browser "
    "and powers modern websites with features like animations, real-time updates, and APIs."
)

para_box.CharHeight = 28

slide.add(para_box)

# ---- DOWNLOAD IMAGE ----
image_url = "https://upload.wikimedia.org/wikipedia/commons/6/6a/JavaScript-logo.png"
image_path = "/tmp/js_logo.png"

# urllib.request.urlretrieve(image_url, image_path)
req = urllib.request.Request(
    image_url,
    headers={"User-Agent": "Mozilla/5.0"}
)

with urllib.request.urlopen(req) as response, open(image_path, "wb") as out_file:
    out_file.write(response.read())

# ---- INSERT IMAGE ----
image = doc.createInstance("com.sun.star.drawing.GraphicObjectShape")

image.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", 15000, 2000))
image.setSize(uno.createUnoStruct("com.sun.star.awt.Size", 6000, 6000))

# Convert file path to URL format
image_url_path = uno.systemPathToFileUrl(image_path)
image.GraphicURL = image_url_path

slide.add(image)

# ---- REFRESH ----
controller = doc.getCurrentController()
frame = controller.getFrame()
window = frame.getContainerWindow()
window.invalidate(0)

print("Slide created: JavaScript intro with text + image.")