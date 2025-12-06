# clean_connection.py
import os
import re
from dotenv import load_dotenv

load_dotenv()

def clean_database_url():
    database_url = os.environ.get('DATABASE_URL', '')
    
    if not database_url:
        print("❌ DATABASE_URL vacía")
        return
    
    print(f"URL original: {database_url}")
    
    # Limpiar caracteres problemáticos
    cleaned_url = re.sub(r'[^\x20-\x7E]', '', database_url)
    
    if cleaned_url != database_url:
        print(f"URL limpia: {cleaned_url}")
        
        # Actualizar .env
        with open('.env', 'r') as f:
            content = f.read()
        
        with open('.env', 'w') as f:
            content = content.replace(database_url, cleaned_url)
            f.write(content)
        
        print("✅ .env actualizado")
    else:
        print("✅ URL ya está limpia")

if __name__ == "__main__":
    clean_database_url()