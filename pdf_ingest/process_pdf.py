# process_pdf.py

import base64
import requests
import sys

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"
API_KEY = "YOUR_GEMINI_API_KEY"

HEADERS = {
    "Content-Type": "application/json"
}

PROMPT = {
    "parts": [
        {
            "text": "You are an intelligent document reader. Extract readable structured text from this document for LLM-based metadata extraction."
        },
        {
            "inline_data": {
                "mime_type": "application/pdf",
                "data": None
            }
        }
    ]
}

def encode_pdf_to_base64(pdf_path):
    with open(pdf_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def call_gemini_vision_api(pdf_path):
    encoded = encode_pdf_to_base64(pdf_path)
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    PROMPT["parts"][0],
                    {
                        "inline_data": {
                            "mime_type": "application/pdf",
                            "data": encoded
                        }
                    }
                ]
            }
        ]
    }

    response = requests.post(f"{API_URL}?key={API_KEY}", headers=HEADERS, json=body)
    if response.status_code == 200:
        candidates = response.json().get("candidates", [])
        return candidates[0]["content"]["parts"][0]["text"] if candidates else ""
    else:
        raise Exception(f"Gemini API error: {response.status_code} {response.text}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_pdf.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    extracted_text = call_gemini_vision_api(pdf_path)
    print(extracted_text)