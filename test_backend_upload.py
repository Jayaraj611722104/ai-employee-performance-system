import requests
import io
import json

def test_backend_upload():
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    print("Attempting to hit ATS upload without login (to check if endpoint responds)...")
    try:
        files = {'resume': ('test.pdf', b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources << >>\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<< /Length 51 >>\nstream\nBT /F1 12 Tf 100 700 Td (Python Developer Experience) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000062 00000 n \n0000000119 00000 n \n0000000201 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n302\n%%EOF', 'application/pdf')}
        r = session.post(f"{base_url}/api/hr/ats-upload", files=files)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_backend_upload()
