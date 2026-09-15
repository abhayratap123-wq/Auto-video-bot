# Python का बेस इमेज यूज़ करेंगे
FROM python:3.10-slim

# FFmpeg इंस्टॉल करने की परमिशन (ये Docker में आराम से हो जाएगा)
RUN apt-get update && apt-get install -y ffmpeg

# वर्किंग डायरेक्टरी सेट करना
WORKDIR /app

# Requirements फाइल को कॉपी करके पाइथन लाइब्रेरी इंस्टॉल करना
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# तुम्हारा main.py कोड कॉपी करना
COPY . .

# सर्वर स्टार्ट करने का कमांड
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
