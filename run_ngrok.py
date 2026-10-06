import os
from pyngrok import ngrok

# أدخلي الـ Auth Token الخاص بكِ هنا بين التنصيص
NGROK_AUTH_TOKEN = "ضعِ_الـ_TOKEN_الخاص_بكِ_هنا"

def start_ngrok():
    if NGROK_AUTH_TOKEN and NGROK_AUTH_TOKEN != "ضعِ_الـ_TOKEN_الخاص_بكِ_هنا":
        ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    
    # فتح نفق لشبكة Streamlit التي تعمل على المنفذ 8501
    public_url = ngrok.connect(8501)
    print("\n==================================================")
    print(f"🚀 Streamlit App is Live Publicly At: {public_url}")
    print("==================================================\n")

if __name__ == "__main__":
    start_ngrok()