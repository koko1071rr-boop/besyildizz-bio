# Link Yönlendirme Merkezi

Tek admin (siz) tarafından yönetilen, çoklu müşteri destekli link-in-bio ürünü:
FastAPI + SQLite backend, tek dosyalık admin paneli (`admin.html`) ve tek dosyalık
public bio sayfası (`index.html`). Her müşteri için bir "bio sayfası" kaydı
oluşturur, linkini/QR kodunu NFC çipine veya kartvizite yazarsınız.

> **Mimari not:** Sistemde çoklu kullanıcı girişi yoktur. Tek bir `ADMIN_TOKEN` ile
> siz giriş yapıp tüm müşterilerin bio sayfalarını tek panelden yönetirsiniz.
> Müşterilerin kendi hesabı veya girişi olmaz — sadece kendilerine ait public
> linki/QR'ı kullanırlar.

## Klasör yapısı

```
besyildizz.bio/
├── backend/               # FastAPI + SQLite API
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── requirements.txt
│   ├── Procfile           # Railway/Heroku başlangıç komutu
│   ├── .env.example
│   └── uploads/           # Yüklenen logo dosyaları (otomatik oluşturulur, /uploads altında servis edilir)
├── admin.html              # Admin paneli (tek dosya)
├── index.html               # Public bio sayfası (slug'a göre API'den veri çeker)
├── style.css                 # Public sayfanın stilleri
└── vercel.json                # Vercel'de temiz slug URL'leri için rewrite kuralı
```

## Özellikler

- **Bio sayfası yönetimi:** slug, işletme adı, slogan, logo, tema rengi, sınırsız link
- **Logo yükleme:** admin panelden dosya seçilir, backend'e yüklenir, otomatik URL üretilir
- **QR kod:** her bio sayfası için anında QR üretimi + PNG indirme
- **Linki kopyala:** tek tıkla public URL'i panoya kopyalama
- **Silme:** onay istemli, geri alınamaz silme
- **Public sayfa:** linkler düz `<a href target="_blank">` etiketleridir — Google
  Yorum, Instagram, `wa.me/...` gibi linkler mobilde otomatik ilgili uygulamayı
  açar, aradan geçen hiçbir JS yoktur

## 1) Backend'i çalıştırma (localhost:8000)

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

copy .env.example .env      # Windows
# cp .env.example .env      # macOS/Linux
```

`.env` dosyasını açıp değerleri düzenleyin:

```bash
# Admin panelinde giriş yaparken kullanacağınız gizli anahtar.
ADMIN_TOKEN=dev-secret-change-me

# index.html ve admin.html'in servis edileceği origin'ler (virgülle ayırın).
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

# Bio sayfalarının yayında yaşadığı adres (QR kod ve "Linki Kopyala" bunu kullanır).
PUBLIC_SITE_URL=http://localhost:5500
```

**`ADMIN_TOKEN`'ı nasıl değiştiririm?** `backend/.env` dosyasında `ADMIN_TOKEN=`
satırını istediğiniz güçlü bir değerle değiştirip backend'i yeniden başlatmanız
yeterli. Panelde önceden giriş yapılmışsa tarayıcıda "Çıkış" yapıp yeni token ile
tekrar giriş yapın (token, tarayıcının `localStorage`'ında tutulur).

Sunucuyu başlatın:

```bash
uvicorn main:app --reload --port 8000
```

API şu adreste ayakta olacak: `http://localhost:8000` — interaktif dokümantasyon
için `http://localhost:8000/docs` adresine gidebilirsiniz. Veriler `backend/biopages.db`
adlı SQLite dosyasında tutulur, ilk çalıştırmada otomatik oluşturulur.

### API uç noktaları

| Yöntem | Yol | Açıklama | Yetki |
|---|---|---|---|
| GET | `/api/bio/{slug}` | Tek bir bio sayfasını döner | Herkese açık |
| GET | `/api/admin/bio` | Tüm kayıtları listeler | `X-Admin-Token` header |
| POST | `/api/admin/bio` | Yeni bio sayfası oluşturur | `X-Admin-Token` header |
| PUT | `/api/admin/bio/{slug}` | Var olan kaydı günceller | `X-Admin-Token` header |
| DELETE | `/api/admin/bio/{slug}` | Kaydı siler | `X-Admin-Token` header |
| GET | `/api/admin/bio/{slug}/qr` | Bio sayfasının public URL'ini QR kod (PNG) olarak döner | `X-Admin-Token` header |
| POST | `/api/admin/upload` | Logo dosyası yükler (PNG/JPEG/WEBP, max 5MB), yüklenen dosyanın tam URL'ini döner | `X-Admin-Token` header |

Yüklenen logolar `backend/uploads/` klasörüne kaydedilir ve `/uploads/<dosya>`
altında statik olarak servis edilir (dönen URL, isteğin geldiği host/port'a göre
otomatik oluşturulur). QR kodlar `PUBLIC_SITE_URL` + `/slug` adresini kodlar.

## 2) Frontend'i çalıştırma

`index.html` ve `admin.html`, backend'e `fetch` ile bağlanır; bu yüzden `file://`
olarak doğrudan açmak yerine basit bir statik sunucuyla servis edin (CORS ve
`file://` kısıtlamaları nedeniyle):

```bash
# proje kök dizininde (backend/ değil)
python -m http.server 5500
```

Sonra tarayıcıda:

- Admin paneli: `http://localhost:5500/admin.html`
- Örnek bio sayfası: `http://localhost:5500/ornek-kafe` *(bkz. aşağıdaki not)*

> **Slug'lı URL'ler hakkında not:** `python -m http.server` gibi basit statik
> sunucular `/ornek-kafe` gibi yolları otomatik olarak `index.html`'e yönlendirmez.
> Yerelde test ederken bunun yerine `http://localhost:5500/index.html?slug=ornek-kafe`
> kullanabilirsiniz. Vercel'de (aşağıya bakın) `vercel.json` bu yönlendirmeyi
> otomatik yapar; böylece `besyildizz.bio/ornek-kafe` gibi temiz URL'ler çalışır.

`ALLOWED_ORIGINS` ve `PUBLIC_SITE_URL` değerlerini kullandığınız portla/domain'le
eşleştirmeyi unutmayın (`backend/.env` dosyasında).

## 3) İlk bio sayfasını oluşturma

1. `http://localhost:5500/admin.html` adresine gidin.
2. `.env` dosyasındaki `ADMIN_TOKEN` değerini girip giriş yapın.
3. "Yeni Ekle" ile slug, işletme adı, tema rengi, logo ve linkleri girip kaydedin.
4. Kayıt kartındaki 🔗 (linki kopyala) veya 📱 (QR göster/indir) butonlarını kullanın.
5. `http://localhost:5500/index.html?slug=<slug>` adresinden sonucu görüntüleyin.

## Deploy notları

### Backend → Railway

1. Railway'de yeni proje oluşturup bu repoyu bağlayın, **Root Directory**'yi
   `backend` olarak ayarlayın (Procfile zaten `backend/` içinde, Railway'i
   otomatik algılar).
2. Railway'in Variables sekmesinden `.env`'deki değerleri girin: `ADMIN_TOKEN`,
   `ALLOWED_ORIGINS` (Vercel domain'iniz, örn. `https://besyildizz.bio`),
   `PUBLIC_SITE_URL` (aynı domain).
3. **Kalıcı depolama önemli:** SQLite dosyası (`biopages.db`) ve yüklenen logolar
   (`uploads/`) container'ın diskinde tutulur; Railway'in dosya sistemi varsayılan
   olarak kalıcı değildir. Railway'de bir **Volume** oluşturup `backend/` dizinine
   (ya da `biopages.db` ve `uploads/`'ı içeren bir alt yola) mount edin, aksi halde
   her deploy'da veriler ve yüklenen logolar silinir.
4. Deploy sonrası verilen `https://xxxx.up.railway.app` (veya bağladığınız custom
   domain) adresini not edin — bir sonraki adımda frontend'e bu adresi vereceksiniz.

### Frontend → Vercel

1. Proje kökünü (backend hariç, `index.html`/`admin.html`/`style.css`/`vercel.json`
   içeren dizini) Vercel'e statik proje olarak bağlayın (Framework Preset: **Other**,
   build komutu yok).
2. Deploy etmeden önce `index.html` ve `admin.html` içindeki iki sabiti güncelleyin:
   - `API_BASE_URL` → Railway'de aldığınız backend adresi
   - `PUBLIC_SITE_URL` (yalnızca `admin.html`'de) → Vercel'de kullanacağınız domain
3. `vercel.json` içindeki rewrite kuralı, `/ornek-kafe` gibi tüm yolları
   `index.html`'e yönlendirir; `admin.html` ve `style.css` gibi var olan statik
   dosyalar olduğu gibi servis edilmeye devam eder.
4. Deploy sonrası Railway'deki `ALLOWED_ORIGINS` ve `PUBLIC_SITE_URL` değerlerini
   Vercel'in verdiği gerçek domain ile güncelleyip backend'i yeniden başlatın
   (env değişiklikleri restart gerektirir).

### Deploy sonrası kontrol listesi

- [ ] `https://<vercel-domain>/admin.html` açılıyor ve giriş yapılabiliyor
- [ ] Yeni kayıt oluşturulabiliyor (CORS hatası yoksa `ALLOWED_ORIGINS` doğrudur)
- [ ] Logo yüklenebiliyor, QR indirilebiliyor
- [ ] `https://<vercel-domain>/<slug>` public sayfayı gösteriyor (rewrite doğrudur)
- [ ] QR kod telefonla okutulduğunda doğru public URL'e gidiyor

## Sorun giderme

- **"Sunucuya bağlanılamadı" hatası:** backend çalışmıyor veya `API_BASE_URL` yanlış.
- **CORS hatası (konsolda):** `ALLOWED_ORIGINS`, frontend'in gerçekten servis
  edildiği origin ile birebir eşleşmeli (protokol + host + port).
- **Giriş yapamıyorum:** `ADMIN_TOKEN` `.env`'de tanımlı mı, backend bu `.env`
  ile mi başlatıldı, panelde doğru değeri mi giriyorsunuz kontrol edin.
- **QR/kopyalama çalışmıyor:** bu ikisi de admin token gerektirir; oturum süresi
  dolmuşsa panel otomatik olarak giriş ekranına döner.
