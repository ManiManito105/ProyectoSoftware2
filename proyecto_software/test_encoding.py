# test_encoding.py
import os
from dotenv import load_dotenv

load_dotenv()

def test_encoding():
    database_url = os.environ.get('DATABASE_URL', '')
    print(f"URL original: {database_url}")
    
    # Probar diferentes formas de codificar
    encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
    
    for encoding in encodings:
        try:
            encoded = database_url.encode(encoding)
            decoded = encoded.decode(encoding)
            print(f"✅ {encoding}: {decoded}")
        except Exception as e:
            print(f"❌ {encoding}: {e}")

if __name__ == "__main__":
    test_encoding()