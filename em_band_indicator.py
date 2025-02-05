import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import sys
from mailjet_rest import Client

# Mailjet API bilgileri
MAILJET_API_KEY = 'cb974525a7d6d38f8cd2b4f48aedb892'
MAILJET_API_SECRET = '77ebf1b85ad4771ec0597c07df9e5a31'
FROM_EMAIL = 'gsorkanozmen@hotmail.com'
TO_EMAIL = 'gsorkanozmen@gmail.com'

def calculate_bands(df, sma_period=100, atr_period=500, 
                   atr_multiplier1=3.2, atr_multiplier2=6.4, atr_multiplier3=9.5):
    # Copy DataFrame to avoid SettingWithCopyWarning
    df = df.copy()
    
    # SMA hesaplama
    df['sma'] = df['Close'].rolling(window=sma_period).mean()
    
    # ATR hesaplama
    df['TR'] = np.maximum(
        np.maximum(
            df['High'] - df['Low'],
            abs(df['High'] - df['Close'].shift(1))
        ),
        abs(df['Low'] - df['Close'].shift(1))
    )
    df['atr'] = df['TR'].rolling(window=atr_period).mean()
    
    # Bantları hesapla
    df['upper1'] = df['sma'] + df['atr'] * atr_multiplier1
    df['upper2'] = df['sma'] + df['atr'] * atr_multiplier2
    df['upper3'] = df['sma'] + df['atr'] * atr_multiplier3
    
    df['lower1'] = df['sma'] - df['atr'] * atr_multiplier1
    df['lower2'] = df['sma'] - df['atr'] * atr_multiplier2
    df['lower3'] = df['sma'] - df['atr'] * atr_multiplier3
    
    # NaN değerleri 0 ile doldur
    df = df.fillna(0)
    
    # BOSC değerini hesapla
    df['bosc'] = 0  # Default değer
    
    # Her satır için BOSC değerini hesapla
    for i in range(len(df)):
        close = df['Close'].iloc[i].item()
        upper3 = df['upper3'].iloc[i].item()
        upper2 = df['upper2'].iloc[i].item()
        upper1 = df['upper1'].iloc[i].item()
        lower1 = df['lower1'].iloc[i].item()
        lower2 = df['lower2'].iloc[i].item()
        lower3 = df['lower3'].iloc[i].item()
        
        if close > upper3:
            df.iloc[i, df.columns.get_loc('bosc')] = 3
        elif close > upper2:
            df.iloc[i, df.columns.get_loc('bosc')] = 2
        elif close > upper1:
            df.iloc[i, df.columns.get_loc('bosc')] = 1
        elif close >= lower1 and close <= upper1:
            df.iloc[i, df.columns.get_loc('bosc')] = 0
        elif close < lower1 and close > lower2:
            df.iloc[i, df.columns.get_loc('bosc')] = -1
        elif close < lower2 and close > lower3:
            df.iloc[i, df.columns.get_loc('bosc')] = -2
        else:
            df.iloc[i, df.columns.get_loc('bosc')] = -3
    
    return df

def analyze_stock(symbol, start_date, end_date):
    try:
        # Veriyi indir
        df = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        if df.empty:
            return {
                'symbol': symbol,
                'error': 'Veri bulunamadı'
            }
        
        # Göstergeleri hesapla
        df = calculate_bands(df)
        
        # Son günün BOSC değerini kontrol et
        last_row = df.iloc[-1]
        bosc = last_row['bosc'].item()
        
        # BOSC değeri 1 veya daha büyükse AL sinyali
        if bosc >= 1:
            return {
                'symbol': symbol,
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'price': last_row['Close'].item(),
                'bosc': bosc,
                'error': None
            }
        
        return {
            'symbol': symbol,
            'error': None
        }
        
    except Exception as e:
        return {
            'symbol': symbol,
            'error': str(e)
        }

def send_email(subject, body):
    mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')
    
    data = {
        'Messages': [
            {
                "From": {
                    "Email": FROM_EMAIL,
                    "Name": "BIST Analiz Botu"
                },
                "To": [
                    {
                        "Email": TO_EMAIL,
                        "Name": "Alıcı"
                    }
                ],
                "Subject": subject,
                "TextPart": body
            }
        ]
    }
    
    try:
        result = mailjet.send.create(data=data)
        if result.status_code == 200:
            print("Email başarıyla gönderildi")
        else:
            print(f"Email gönderilirken hata oluştu: {result.status_code}")
    except Exception as e:
        print(f"Email gönderilirken hata oluştu: {str(e)}")

def main():
    # Tarihleri ayarla
    today = datetime.now()
    start_date = (today - pd.Timedelta(days=30)).strftime('%Y-%m-%d')  # Son 30 günlük veri
    end_date = today.strftime('%Y-%m-%d')
    
    # Hisse listesini oku
    try:
        with open('hisse_listesi.txt', 'r', encoding='utf-8') as f:
            symbols = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Hata: hisse_listesi.txt dosyası bulunamadı!")
        return
    
    print(f"\n=== Borsa İstanbul AL Sinyalleri ({end_date}) ===\n")
    print(f"Toplam {len(symbols)} hisse analiz ediliyor...\n")
    
    # Her hisse için analiz yap
    results = []
    for symbol in symbols:
        result = analyze_stock(symbol, start_date, end_date)
        if result['error'] is None and 'price' in result:  # AL sinyali varsa
            results.append(result)
    
    if results:  # Eğer AL sinyali veren hisse varsa
        # Email içeriğini hazırla
        email_body = f"=== Borsa İstanbul AL Sinyalleri ({end_date}) ===\n\n"
        
        # BOSC değerine göre sırala (en yüksekten düşüğe)
        results.sort(key=lambda x: x['bosc'], reverse=True)
        
        for result in results:
            line = f"{result['symbol']} - "
            line += f"Fiyat: {result['price']:.2f}, BOSC: {result['bosc']}\n"
            print(line)
            email_body += line
        
        # Email gönder
        send_email(
            subject=f"BIST AL Sinyalleri - {end_date}",
            body=email_body
        )
        
        print("\nAL sinyali veren hisseler için email gönderildi.")
    else:
        print("\nBugün AL sinyali veren hisse bulunamadı.")

if __name__ == "__main__":
    main()
