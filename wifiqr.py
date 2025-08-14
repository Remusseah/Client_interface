import qrcode

# === Fill in your Wi-Fi details here ===
SSID = "Rockstead-Guest"           # Wi-Fi network name
PASSWORD = "2c93afffc866"   # Wi-Fi password
SECURITY = "WPA2"                  # Options: WPA, WPA2, WPA3, WEP, or leave "" for open network

# Create the Wi-Fi QR code data string
wifi_data = f"WIFI:T:{SECURITY};S:{SSID};P:{PASSWORD};;"

# Generate the QR code
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(wifi_data)
qr.make(fit=True)

# Create an image of the QR code
img = qr.make_image(fill_color="black", back_color="white")

# Save it to a file
img.save("wifi_qr.png")

print("✅ Wi-Fi QR code saved as wifi_qr.png")
