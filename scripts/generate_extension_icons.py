#!/usr/bin/env python3
"""
Generate Chrome extension icons for Agencity.

Creates 16x16, 48x48, and 128x128 PNG icons with gradient background and "A" letter.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Icon configuration
ICON_SIZES = [16, 48, 128]
GRADIENT_START = (99, 102, 241)  # #6366f1
GRADIENT_END = (139, 92, 246)    # #8b5cf6
TEXT_COLOR = (255, 255, 255)     # White
BORDER_RADIUS_RATIO = 0.2        # 20% rounded corners

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__),
    '..',
    'agencity',
    'chrome-extension',
    'icons'
)


def create_gradient_background(size: int) -> Image.Image:
    """Create a vertical gradient background."""
    img = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(img)

    # Draw vertical gradient
    for y in range(size):
        # Calculate color for this row
        ratio = y / size
        r = int(GRADIENT_START[0] + (GRADIENT_END[0] - GRADIENT_START[0]) * ratio)
        g = int(GRADIENT_START[1] + (GRADIENT_END[1] - GRADIENT_START[1]) * ratio)
        b = int(GRADIENT_START[2] + (GRADIENT_END[2] - GRADIENT_START[2]) * ratio)

        draw.line([(0, y), (size, y)], fill=(r, g, b))

    return img


def add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
    """Add rounded corners to an image."""
    size = img.size[0]

    # Create a mask for rounded corners
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size, size)], radius=radius, fill=255)

    # Apply mask
    result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0))
    result.putalpha(mask)

    return result


def add_letter(img: Image.Image, size: int) -> Image.Image:
    """Add white 'A' letter to the center."""
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default if not available
    font_size = int(size * 0.65)  # Letter takes up 65% of icon

    try:
        # Try system fonts
        font_paths = [
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
            'C:\\Windows\\Fonts\\arial.ttf',  # Windows
        ]

        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                break

        if font is None:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Draw the letter 'A' centered
    text = "A"

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate position (centered)
    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]

    # Draw text with slight shadow for depth
    shadow_offset = max(1, size // 32)
    draw.text((x + shadow_offset, y + shadow_offset), text, fill=(0, 0, 0, 50), font=font)
    draw.text((x, y), text, fill=TEXT_COLOR, font=font)

    return img


def generate_icon(size: int, output_path: str):
    """Generate a single icon of the specified size."""
    print(f"Generating {size}x{size} icon...")

    # Create gradient background
    img = create_gradient_background(size)

    # Add rounded corners
    radius = int(size * BORDER_RADIUS_RATIO)
    img = add_rounded_corners(img, radius)

    # Add letter 'A'
    img = add_letter(img, size)

    # Save
    img.save(output_path, 'PNG')
    print(f"  Saved to {output_path}")


def main():
    """Generate all icon sizes."""
    print("=" * 60)
    print("Agencity Chrome Extension Icon Generator")
    print("=" * 60)
    print()

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate each icon size
    for size in ICON_SIZES:
        output_path = os.path.join(OUTPUT_DIR, f'icon{size}.png')
        generate_icon(size, output_path)

    print()
    print("✅ All icons generated successfully!")
    print(f"📁 Location: {OUTPUT_DIR}")
    print()
    print("Next steps:")
    print("  1. Load the extension in Chrome (chrome://extensions)")
    print("  2. Enable 'Developer mode'")
    print("  3. Click 'Load unpacked' and select the chrome-extension directory")


if __name__ == '__main__':
    main()
