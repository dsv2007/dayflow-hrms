import urllib.request
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

# 1. Download fonts
font_dir = "fonts"
os.makedirs(font_dir, exist_ok=True)
cursive_font_path = os.path.join(font_dir, "DancingScript-Regular.ttf")
sans_font_path = os.path.join(font_dir, "Inter-Regular.ttf")

if not os.path.exists(cursive_font_path):
    urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/dancingscript/DancingScript-SemiBold.ttf", cursive_font_path)
if not os.path.exists(sans_font_path):
    urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/inter/Inter-Medium.ttf", sans_font_path)

# 2. Setup Image (1584 x 396 is LinkedIn standard)
width, height = 1584, 396
image = Image.new("RGBA", (width, height), "#f8f9fa")
draw = ImageDraw.Draw(image)

# 3. Draw an elegant light gradient/geometric background
# Draw subtle soft circles for a premium tech vibe
def draw_soft_circle(d, x, y, radius, color):
    # PIL doesn't do soft edges easily without filtering, so we draw on a separate layer and blur
    overlay = Image.new("RGBA", (width, height), (255,255,255,0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color)
    overlay = overlay.filter(ImageFilter.GaussianBlur(100))
    image.alpha_composite(overlay)

draw_soft_circle(draw, 150, 100, 300, (226, 232, 240, 150)) # light silver/blue
draw_soft_circle(draw, 1400, 300, 400, (241, 245, 249, 180)) # lighter silver
draw_soft_circle(draw, 800, -100, 250, (238, 242, 255, 120)) # subtle indigo tint

# 4. Draw Text
try:
    font_name = ImageFont.truetype(cursive_font_path, 110)
    font_details = ImageFont.truetype(sans_font_path, 32)
except IOError:
    print("Error loading fonts.")
    exit(1)

text_name = "Santhivarshini D"
text_details = "6369083465   |   santhivarshinidevan@gmail.com"

# Measure text to center it
# getbbox returns (left, top, right, bottom)
name_bbox = draw.textbbox((0,0), text_name, font=font_name)
name_w = name_bbox[2] - name_bbox[0]
name_h = name_bbox[3] - name_bbox[1]

details_bbox = draw.textbbox((0,0), text_details, font=font_details)
details_w = details_bbox[2] - details_bbox[0]
details_h = details_bbox[3] - details_bbox[1]

# Coordinates
name_x = (width - name_w) / 2
name_y = (height - name_h - details_h - 40) / 2 - 20

details_x = (width - details_w) / 2
details_y = name_y + name_h + 40

# Draw text (dark charcoal gray)
draw.text((name_x, name_y), text_name, font=font_name, fill="#1e293b")
draw.text((details_x, details_y), text_details, font=font_details, fill="#475569")

# Add a subtle line between name and details
line_y = name_y + name_h + 20
line_width = 300
line_x_start = (width - line_width) / 2
draw.line([(line_x_start, line_y), (line_x_start + line_width, line_y)], fill="#cbd5e1", width=2)

# Save the banner
out_path = "C:\\Users\\SRCE\\.gemini\\antigravity\\brain\\0477b2f9-057e-48f8-9699-e33fbe7668c7\\linkedin_banner_perfect_fit.png"
image.save(out_path)
print(f"Banner saved to {out_path}")
