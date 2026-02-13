import qrcode
import sys

def generate_qr_code(url, filename="qrcode_link.png"):
    """
    Generates a QR code for a given URL and saves it as a PNG file.
    """
    if not url:
        print("Error: URL cannot be empty.")
        return

    # Create QR code instance
    qr = qrcode.QRCode(
        version=1, # Controls the size of the QR Code; version=1 is 21x21 modules
        error_correction=qrcode.constants.ERROR_CORRECT_L, # About 7% error correction
        box_size=10, # Size of each box in the QR code grid
        border=4, # Size of the border (quiet zone)
    )

    # Add data (the URL) to the QR code
    qr.add_data(url)
    qr.make(fit=True) # Adjusts the size to fit all data

    # Create an image from the QR code instance
    # You can customize fill_color and back_color
    img = qr.make_image(fill_color="black", back_color="white")

    # Save the image file
    img.save(filename)
    print(f"QR Code generated and saved as {filename}")

if __name__ == "__main__":
    # Example usage:
    # You can hardcode the URL or take input from the user
    # For user input, uncomment the line below:
    # link = input("Enter the URL to encode: ").strip()

    link = "https://hisabkitabpos.netlify.app" # Replace with your link
    generate_qr_code(link)

