import os
import requests
import json

def test_key(key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents":[{"parts":[{"text":"say hi"}]}]}
    response = requests.post(url, headers=headers, json=data)
    print(f"Key ends in {key[-4:] if key else 'None'}: {response.status_code} - {response.text}")

test_key("AIzaSyAFJFHUAODTgqiKRJs-coZSJ0rkN8VrdKc")
