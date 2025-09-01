from PIL import Image, ImageDraw, ImageFont
import os

# ---------- CONFIG ----------
CANVAS_W, CANVAS_H = 1080, 1920
BG_COLOR = (0, 53, 122)  # hex #00357A

TITLE_LINE1 = "last week's"
TITLE_LINE2 = "On repeat"

FONTS = {
    "line1": ("TheSeasons-Regular.ttf", 50),   # provide this TTF
    "line2": ("BurguesScript-Bold.ttf", 163),  # provide this TTF
    "song":  ("Arial.ttf", 40),                # fallback font
    "artist":("Arial.ttf", 32),
}

# Title positions
TITLE_LINE1_POS = (346, 225)
TITLE_LINE2_POS = (108, 225)

# Album covers
COVER_SIZE = (172, 172)
COVER_X, COVER_Y_START = 165, 598
COVER_Y_STEP = 242  # 172px tall + 70px spacing

# Text relative to covers
TEXT_X_OFFSET = 70
SONG_Y_OFFSET = 20
ARTIST_Y_OFFSET = 70

OUTPUT = "story.png"
IMAGES_DIR = "images"

# Example track metadata (replace with Spotify results)
tracks = [
    {"title": "Song One", "artist": "Artist A"},
    {"title": "Song Two", "artist": "Artist B"},
    {"title": "Song Three", "artist": "Artist C"},
    {"title": "Song Four", "artist": "Artist D"},
    {"title": "Song Five", "artist": "Artist E"},
]
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

def main():
    # 1) Canvas
    base = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(base)

    # 2) Title
    font_line1 = load_font(FONTS["line1"][0], FONTS["line1"][1])
    font_line2 = load_font(FONTS["line2"][0], FONTS["line2"][1])
    draw.text(TITLE_LINE1_POS, TITLE_LINE1, fill=(255,255,255), font=font_line1)
    draw.text(TITLE_LINE2_POS, TITLE_LINE2, fill=(255,255,255), font=font_line2)

    # 3) Covers + text
    font_song = load_font(FONTS["song"][0], FONTS["song"][1])
    font_artist = load_font(FONTS["artist"][0], FONTS["artist"][1])

    cover_files = sorted(
        [os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR)
         if f.lower().endswith((".jpg",".jpeg",".png"))]
    )[:5]

    for i, track in enumerate(tracks[:5]):
        cx, cy = COVER_X, COVER_Y_START + i*COVER_Y_STEP
        w,h = COVER_SIZE

        if i < len(cover_files):
            cover = Image.open(cover_files[i]).convert("RGB")
            cover = fit_image(cover, w, h)
            # Rounded mask
            mask = Image.new("L", (w,h), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.rounded_rectangle((0,0,w,h), radius=30, fill=255)
            base.paste(cover, (cx,cy), mask)

        # Song + artist
        tx = cx + w + TEXT_X_OFFSET
        draw.text((tx, cy + SONG_Y_OFFSET), track["title"], font=font_song, fill=(255,255,255))
        draw.text((tx, cy + ARTIST_Y_OFFSET), track["artist"], font=font_artist, fill=(200,200,200))

    base.save(OUTPUT, quality=95)
    print("Saved", OUTPUT)

if __name__ == "__main__":
    main()
