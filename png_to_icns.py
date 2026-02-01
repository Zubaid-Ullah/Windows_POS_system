from PIL import Image
import os

INPUT_PNG = "src/ui/assets/logo.png"
OUTPUT_ICNS = "logo.icns"

# Required macOS icon sizes
ICON_SIZES = [
    (16, 16),
    (32, 32),
    (64, 64),
    (128, 128),
    (256, 256),
    (512, 512),
    (1024, 1024),
]

def png_to_icns(input_png, output_icns):
    img = Image.open(input_png).convert("RGBA")

    icon_images = []
    for size in ICON_SIZES:
        icon_images.append(img.resize(size, Image.LANCZOS))

    icon_images[0].save(
        output_icns,
        format="ICNS",
        append_images=icon_images[1:]
    )

    print(f"✅ macOS icon created: {output_icns}")

if __name__ == "__main__":
    if not os.path.exists(INPUT_PNG):
        raise FileNotFoundError("logo.png not found")

    png_to_icns(INPUT_PNG, OUTPUT_ICNS)
