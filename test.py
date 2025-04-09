import requests
api_key = "AIzaSyAdZf_dtGTSdU2DpYyHzWE4O8C9GkCeNyI"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
payload = {
    "contents": [{"parts": [{"text": "Hello world"}]}]
}
response = requests.post(url, json=payload)
print(response.status_code)
print(response.json())