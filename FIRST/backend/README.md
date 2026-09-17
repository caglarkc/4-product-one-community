# FIRST backend — uzak sunucuda Docker

Bu dizin Django/DRF backend'in en küçük çalıştırma iskeletidir. Yalnız `GET /health/` süreç sağlık kontrolü vardır; auth, veritabanı, kullanıcı modeli ve ürün API'leri henüz uygulanmadı.

Python bağımlılıkları image içinde kurulur. Geliştirici bilgisayarında `.venv`, pip kurulumu veya Docker kurulumu gerekmiyor. Aşağıdaki komutlar Docker Engine ve Compose bulunan **uzak sunucuda** çalıştırılacaktır. Henüz sunucuya gönderim veya deploy yapılmadı.

## Sunucuda hazırlık ve çalıştırma

Repo sunucuya alındıktan sonra:

```sh
cd FIRST/backend
cp .env.example .env
chmod 600 .env
openssl rand -hex 32
```

Üretilen rastgele değeri `.env` içindeki `DJANGO_SECRET_KEY` alanına yaz. `.env` dosyasını Git'e ekleme. `DJANGO_ALLOWED_HOSTS` alanına gerçek API domain'ini ekle; container sağlık kontrolü için `localhost,127.0.0.1` değerlerini koru.

```sh
docker compose config --quiet
docker compose build --pull
docker compose run --rm backend python manage.py check
docker compose up -d
docker compose ps
curl --fail http://127.0.0.1:8000/health/
docker compose logs --tail=100 backend
```

Beklenen cevap: `{"status": "ok"}`. Port sadece sunucunun loopback adresinde açılır; dış erişim için sunucudaki HTTPS reverse proxy gerçek API domain'ini bu porta yönlendirmelidir. Bu dosyalar proxy/TLS kurmaz. Proxy başka container'daysa ağ bağlantısı ayrıca ayarlanmalıdır; portu doğrudan herkese açma.

Container root olmayan kullanıcıyla, salt okunur dosya sistemiyle çalışır. Yazılabilir `/tmp` geçicidir. Veritabanı seçimi yapılmadığı için migration çalıştırılmaz ve kalıcı veri saklanmaz. Bağımlılık aralıkları kullanılır; üretim tesliminde doğrulanan sürümler kilitlenmelidir.

## Doğrulama sınırı

Yerelde Docker kurulmadı/çalıştırılmadı; image build ve container smoke kontrolü uzak sunucuda yukarıdaki komutlarla yapılacaktır. `/health/` yalnız sürecin cevap verdiğini gösterir; tamamlanmış uygulama veya auth kontrolü değildir.
