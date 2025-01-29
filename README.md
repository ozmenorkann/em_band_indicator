# Borsa İstanbul Teknik Analiz Botu

Bu proje, Borsa İstanbul'da işlem gören hisseleri teknik analiz yöntemiyle inceleyerek AL sinyali veren hisseleri tespit eder ve email ile bildirim gönderir.

## Özellikler

- BIST hisselerinin günlük analizi
- SMA (Simple Moving Average) hesaplaması
- ATR (Average True Range) hesaplaması
- BOSC (Band Oscillator) indikatörü
- Otomatik günlük analiz (GitHub Actions ile)
- Email bildirimleri (Mailjet API ile)

## Kurulum

1. Repository'yi klonlayın:
```bash
git clone https://github.com/ozmenorkann/em_band_indicator.git
cd em_band_indicator
```

2. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

## Kullanım

1. Analiz edilecek hisseleri `hisse_listesi.txt` dosyasına ekleyin
2. GitHub repository'nizin Settings > Secrets and variables > Actions kısmına şu secret'ları ekleyin:
   - `MAILJET_API_KEY`: Mailjet API Key
   - `MAILJET_API_SECRET`: Mailjet API Secret
   - `FROM_EMAIL`: Gönderen email adresi
   - `TO_EMAIL`: Alıcı email adresi

## Otomatik Çalışma

Bu proje GitHub Actions kullanarak her iş günü (Pazartesi-Cuma) sabah 09:00'da otomatik olarak çalışır. Eğer AL sinyali veren hisse(ler) varsa, belirlenen email adresine bildirim gönderir.

## Teknik Göstergeler

- SMA Periyodu: 10 gün
- ATR Periyodu: 10 gün
- Bant Çarpanları: 3.2, 6.4, 9.5

## AL Sinyali Kriterleri

Bir hisse senedi aşağıdaki durumda AL sinyali verir:
- BOSC değeri 1 veya daha yüksek olduğunda

## Lisans

MIT
