import qrcode
import socket

# Get local IP address
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

# Create URL for uploading
url = f"http://{local_ip}:5000"

# Generate QR code
img = qrcode.make(url)
img.save("flask_qr.png")

print(f"QR code generated. Scan it to visit: {url}")
