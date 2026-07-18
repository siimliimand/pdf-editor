import requests
import sys

import os

def test_upload():
    url = "http://localhost:8001/upload"
    pdf_path = os.path.join(os.path.dirname(__file__), 'data', 'test_invoice.pdf')
    files = {'file': ('test_invoice.pdf', open(pdf_path, 'rb'), 'application/pdf')}
    
    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            json_resp = response.json()
            html = json_resp.get("html", "")
            print(f"Response contains HTML: {len(html)} chars")
            
            # Basic validation
            if "INVOICE" in html and "Total:" in html:
                print("SUCCESS: Key invoice elements found in HTML.")
            else:
                print("FAILURE: Key invoice elements missing in HTML.")
                
            # Check for data URL (images)
            if "data:image" in html:
                print("SUCCESS: Images embedded as data URLs.")
            else:
                print("WARNING: No data URLs found (Check if PDF had images that were rasterized).")
                
            out_path = os.path.join(os.path.dirname(__file__), "response_output.html")
            with open(out_path, "w") as f:
                f.write(html)
            print(f"Saved output to {out_path}")
            
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_upload()
