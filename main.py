import argparse
import json
import os
import tempfile
import urllib.request
from pathlib import Path

import uno
from com.sun.star.awt import FontWeight
from com.sun.star.beans import PropertyValue


def connect_to_libreoffice(host: str = "127.0.0.1", port: int = 2002):
    local_ctx = uno.getComponentContext()
    resolver = local_ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_ctx
    )
    ctx = resolver.resolve(
        f"uno:socket,host={host},port={port};urp;StarOffice.ComponentContext"
    )
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    return desktop


def point(x: int, y: int):
    return uno.createUnoStruct("com.sun.star.awt.Point", x, y)


def size(width: int, height: int):
    return uno.createUnoStruct("com.sun.star.awt.Size", width, height)


def download_if_url(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://")):
        suffix = Path(path_or_url).suffix or ".img"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        req = urllib.request.Request(path_or_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response, open(tmp_path, "wb") as out_file:
            out_file.write(response.read())
        return tmp_path
    return path_or_url


def _create_text_capable_shape(doc):
    # TextShape can behave inconsistently across LibreOffice builds; fallback to RectangleShape.
    for service_name in ("com.sun.star.drawing.TextShape", "com.sun.star.drawing.RectangleShape"):
        shape = doc.createInstance(service_name)
        if hasattr(shape, "setString") or hasattr(shape, "String"):
            return shape
    raise RuntimeError("Could not create a text-capable shape")


def add_text_shape(doc, slide, block: dict):
    text = _create_text_capable_shape(doc)
    x, y = block.get("x", 2000), block.get("y", 2000)
    w, h = block.get("width", 18000), block.get("height", 3000)
    text.setPosition(point(x, y))
    text.setSize(size(w, h))

    # Ensure text is visible and not clipped or hidden by style defaults
    text.FillStyle = 0  # NONE
    text.LineStyle = 0  # NONE
    text.TextAutoGrowHeight = True
    text.TextAutoGrowWidth = False
    text.TextWordWrap = True

    content = block.get("text", "")
    if hasattr(text, "setString"):
        text.setString(content)
    else:
        text.String = content

    cursor = text.createTextCursor()
    cursor.gotoStart(False)
    cursor.gotoEnd(True)
    cursor.CharHeight = float(block.get("font_size", 28))
    cursor.CharColor = int(block.get("color", 0x000000))

    if block.get("type") == "heading":
        cursor.CharWeight = FontWeight.BOLD
    elif block.get("type") == "subheading":
        cursor.CharWeight = FontWeight.SEMIBOLD

    slide.add(text)

    # Ensure text stays above background elements.
    try:
        text.ZOrder = 1000
    except Exception:
        pass


def add_image_shape(doc, slide, block: dict):
    image_path = download_if_url(block["path"])
    image = doc.createInstance("com.sun.star.drawing.GraphicObjectShape")
    x, y = block.get("x", 14000), block.get("y", 2000)
    w, h = block.get("width", 7000), block.get("height", 7000)
    image.setPosition(point(x, y))
    image.setSize(size(w, h))
    image.GraphicURL = uno.systemPathToFileUrl(str(Path(image_path).resolve()))
    slide.add(image)


def add_chart_shape(doc, slide, block: dict):
    import matplotlib.pyplot as plt

    chart = block.get("chart", {})
    chart_type = chart.get("type", "bar")
    labels = chart.get("labels", [])
    values = chart.get("values", [])
    title = chart.get("title", "")

    fig, ax = plt.subplots(figsize=(6, 3.5))
    if chart_type == "line":
        ax.plot(labels, values, marker="o")
    elif chart_type == "pie":
        ax.pie(values, labels=labels, autopct="%1.1f%%")
    else:
        ax.bar(labels, values)

    ax.set_title(title)
    if chart_type != "pie":
        ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()

    fd, chart_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    fig.savefig(chart_path, dpi=180)
    plt.close(fig)

    add_image_shape(
        doc,
        slide,
        {
            "path": chart_path,
            "x": block.get("x", 2000),
            "y": block.get("y", 8000),
            "width": block.get("width", 12000),
            "height": block.get("height", 7000),
        },
    )


def add_block(doc, slide, block: dict):
    block_type = block.get("type")
    if block_type in {"heading", "subheading", "paragraph", "text"}:
        add_text_shape(doc, slide, block)
    elif block_type == "image":
        add_image_shape(doc, slide, block)
    elif block_type == "chart":
        add_chart_shape(doc, slide, block)
    else:
        raise ValueError(f"Unsupported block type: {block_type}")


def apply_slide_content(doc, slide, slide_spec: dict):
    for block in slide_spec.get("blocks", []):
        add_block(doc, slide, block)


def generate_presentation_from_json(spec: dict, output_path: str, host: str, port: int):
    desktop = connect_to_libreoffice(host=host, port=port)
    doc = desktop.loadComponentFromURL("private:factory/simpress", "_blank", 0, ())

    slides = doc.getDrawPages()
    # Reuse first slide for first spec, add additional slides as needed
    for i, slide_spec in enumerate(spec.get("slides", [])):
        if i == 0:
            slide = slides.getByIndex(0)
        else:
            slides.insertNewByIndex(i)
            slide = slides.getByIndex(i)
        apply_slide_content(doc, slide, slide_spec)

    output_file = Path(output_path).resolve()
    output_url = uno.systemPathToFileUrl(str(output_file))

    # Defensive cleanup: some LibreOffice builds may still reject overwrite on store APIs.
    if output_file.exists():
        output_file.unlink()

    overwrite = PropertyValue()
    overwrite.Name = "Overwrite"
    overwrite.Value = True

    doc.storeAsURL(output_url, (overwrite,))
    doc.close(True)


def main():
    parser = argparse.ArgumentParser(
        description="Generate LibreOffice Impress slides from a JSON specification."
    )
    parser.add_argument("input_json", help="Path to JSON slide spec")
    parser.add_argument("-o", "--output", default="generated_presentation.odp")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2002)
    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        spec = json.load(f)

    generate_presentation_from_json(spec, args.output, args.host, args.port)
    print(f"Presentation generated at: {args.output}")


if __name__ == "__main__":
    main()
