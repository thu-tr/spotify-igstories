from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

# ---------- CONFIG ----------
CANVAS_W, CANVAS_H = 1080, 1920
BG_COLOR = (11, 11, 69)  # hex #0B0B45
PRIMARY_COLOR = (255,255,255)
SECONDARY_COLOR = (244,241,134)

TITLE_LINE1 = "last week s"
TITLE_LINE2 = "On repeat"

FONTS = {
    "line1": ("~/Library/Fonts/theseasons-reg.otf", 50),   # provide this TTF
    "line2": ("~/Library/Fonts/Burgues Script Regular.otf", 200),  # provide this TTF
    "song":  ("~/Library/Fonts/Bruney Season.otf", 38),                # fallback font
    "artist":("Arial.ttf", 32),
}


# Title positions
TITLE_LINE1_POS = (345, 300)
TITLE_LINE2_POS = (115, 300)

# Album covers
COVER_SIZE = (175, 175)
COVER_X, COVER_Y_START = 115, 590
COVER_Y_STEP = 200  # 172px tall + 70px spacing

# Text relative to covers
TEXT_X_OFFSET = 40
SONG_Y_OFFSET = 20
ARTIST_Y_OFFSET = 75

OUTPUT = "images/story.png"
IMAGES_DIR = "images"
# ----------------------------

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()

def fit_image(img, w, h):
    iw, ih = img.size
    scale = max(w/iw, h/ih)
    img = img.resize((int(iw*scale), int(ih*scale)), Image.LANCZOS)
    iw, ih = img.size
    left = (iw - w)//2
    top  = (ih - h)//2
    return img.crop((left, top, left+w, top+h))

def draw_text_with_blurred_shadow(base, text, pos, font,
                                  shadow_offset=(6,6),
                                  shadow_color=(0,0,0,255),
                                  blur_radius=6,
                                  fill=(255,255,255)):
    """
    Draw text with a blurred shadow onto an image.
    - base: PIL.Image (the canvas)
    - text: string
    - pos: (x, y) position for main text
    - font: PIL.ImageFont instance
    - shadow_offset: (dx, dy) offset for the shadow
    - shadow_color: RGBA tuple for shadow color
    - blur_radius: Gaussian blur radius for shadow softness
    - fill: main text color
    """
    x, y = pos

    # Shadow layer (transparent)
    shadow_layer = Image.new("RGBA", base.size, (0,0,0,0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    # Draw shadow text
    sx = x + shadow_offset[0]
    sy = y + shadow_offset[1]
    shadow_draw.text((sx, sy), text, font=font, fill=shadow_color)

    # Blur shadow
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))

    # Composite onto base
    base.paste(shadow_layer, (0,0), shadow_layer)

    # Draw main text on top
    draw = ImageDraw.Draw(base)
    draw.text((x, y), text, font=font, fill=fill)

def generate_story(tracks, image_dir=IMAGES_DIR, output=OUTPUT):
    # 1) Canvas
    base = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(base)

    # 2) Title
    font_line1 = load_font(FONTS["line1"][0], FONTS["line1"][1])
    font_line2 = load_font(FONTS["line2"][0], FONTS["line2"][1])
    draw.text(TITLE_LINE1_POS, TITLE_LINE1, fill=PRIMARY_COLOR, font=font_line1)
    draw_text_with_blurred_shadow(
    base,
    TITLE_LINE2,
    TITLE_LINE2_POS,
    font_line2,
    shadow_offset=(6,6),
    shadow_color=SECONDARY_COLOR,
    blur_radius=5,
    fill=PRIMARY_COLOR
)

    # 3) Covers + text
    font_song = load_font(FONTS["song"][0], FONTS["song"][1])
    font_artist = load_font(FONTS["artist"][0], FONTS["artist"][1])

    # cover_files = sorted(
    #     [os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR)
    #      if f.lower().endswith((".jpg",".jpeg",".png"))]
    # )[:5]

    for i, track in enumerate(tracks):
        cx, cy = COVER_X, COVER_Y_START + i*COVER_Y_STEP
        w,h = COVER_SIZE
        print("the track is", track)
        cover = Image.open(track["image"])
        cover = fit_image(cover, w, h)
        # Rounded mask
        mask = Image.new("L", (w,h), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle((0,0,w,h), radius=30, fill=255)
        base.paste(cover, (cx,cy), mask)

        # Song + artist
        tx = cx + w + TEXT_X_OFFSET
        draw.text((tx, cy + SONG_Y_OFFSET), track["name"] if len(track["name"]) <= 25 else track["name"][:25], font=font_song, fill=SECONDARY_COLOR)
        draw.text((tx, cy + ARTIST_Y_OFFSET), track["artist"], font=font_artist, fill=PRIMARY_COLOR)

    base.save(OUTPUT, quality=95)
    print("Saved", OUTPUT)

