from PIL import Image, ImageDraw, ImageFont
import datetime

OUTPUT_DIR = "output"

def test_thumbnail():
    # Canvas — 1280x720 dark blue background
    img  = Image.new("RGB", (1280, 720), color=(10, 20, 60))
    draw = ImageDraw.Draw(img)

    # Background gradient stripes
    for i in range(0, 720, 3):
        shade = int(40 * (i / 720))
        draw.rectangle(
            [0, i, 1280, i + 2],
            fill=(10 + shade, 20 + shade, 80 + shade)
        )

    # Left accent bar
    draw.rectangle([0, 0, 8, 720], fill=(255, 180, 0))

    # Try loading Windows system font — fallback to default if not found
    try:
        font_large  = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 90)
        font_medium = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 55)
        font_small  = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   38)
    except:
        font_large  = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small  = ImageFont.load_default()

    today     = datetime.date.today().strftime("%d %b %Y")
    day_name  = datetime.date.today().strftime("%A")

    # FINANCE DAILY — main title
    draw.text((60, 80),  "FINANCE",       font=font_large,  fill=(255, 210, 0))
    draw.text((60, 180), "DAILY",         font=font_large,  fill=(255, 255, 255))

    # Divider line
    draw.rectangle([60, 300, 700, 305], fill=(255, 180, 0))

    # Subtitle
    draw.text((60, 325), "Market Update", font=font_medium, fill=(180, 220, 255))
    draw.text((60, 395), "Top Stories",   font=font_medium, fill=(150, 190, 230))

    # Date top right
    draw.text((900, 90),  day_name,       font=font_small,  fill=(180, 180, 255))
    draw.text((900, 135), today,          font=font_small,  fill=(255, 255, 255))

    # Bottom ticker bar
    draw.rectangle([0, 620, 1280, 720],   fill=(255, 60, 60))
    draw.text((40, 648), "NIFTY  |  SENSEX  |  RBI  |  MARKETS  |  ECONOMY",
            font=font_small, fill=(255, 255, 255))

    # Save
    path = f"{OUTPUT_DIR}/thumbnail.jpg"
    img.save(path, "JPEG", quality=95)
    print(f"Thumbnail saved: {path}")
    print(f"Size: {img.size}")

test_thumbnail()