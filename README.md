# JSON to LibreOffice Impress Slide Generator

This app turns a JSON file into an `.odp` presentation using LibreOffice Impress + UNO.

## Features
- Create multiple slides from one JSON file.
- Add headings, subheadings, paragraphs, and generic text blocks.
- Add images from local file paths or URLs.
- Add charts (`bar`, `line`, `pie`) by rendering with matplotlib and inserting as images.

## Requirements
- LibreOffice installed.
- Python with UNO bindings available (`python3-uno` on many Linux distros).
- `matplotlib` installed for chart blocks.

## Start LibreOffice headless server
```bash
libreoffice --headless --accept="socket,host=127.0.0.1,port=2002;urp;" --norestore --nodefault
```

## Run
```bash
python main.py sample_slides.json -o demo.odp
```

## JSON format
Top-level structure:

```json
{
  "slides": [
    {
      "blocks": [
        {"type": "heading", "text": "Title"},
        {"type": "subheading", "text": "Subtitle"},
        {"type": "paragraph", "text": "Body text"},
        {"type": "image", "path": "./image.png"},
        {
          "type": "chart",
          "chart": {
            "type": "bar",
            "title": "Revenue",
            "labels": ["Q1", "Q2"],
            "values": [100, 130]
          }
        }
      ]
    }
  ]
}
```

Each block can optionally include positioning/sizing fields in Impress units:
- `x`, `y`, `width`, `height`
- `font_size` for text blocks

This makes it easy to have GPT generate JSON payloads and feed them directly into this script.
