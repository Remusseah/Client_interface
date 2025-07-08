import requests

postal_code = "312081"

url = f"https://developers.onemap.sg/commonapi/search?searchVal={postal_code}&returnGeom=Y&getAddrDetails=Y"

try:
    print("Sending request to OneMap...")
    response = requests.get(url)
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)
except Exception as e:
    print("Error:", e)
