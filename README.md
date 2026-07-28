# RIPPERDOC

**ripperdoc**, gömülü build zinciri için PySide6 tabanlı bir masaüstü GUI aracıdır. Key üretimi, firmware başlık güncelleme, imzalama/şifreleme ve firmware imajlarının birleştirilmesi gibi CLI tabanlı işlemleri, tek bir grafik arayüz üzerinden yönetilebilir hale getirir.

Uygulama Windows hedefli olarak geliştirilmiştir (yapılandırma  için `platformdirs` kullanır) ve firmware binary dosyalarının başlığını temsil eden `Image_Hdr_t` isimli C yapısı ile bayt seviyesinde doğrudan çalışır.

---

## İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Özellikler](#özellikler)
3. [Proje Yapısı](#proje-yapısı)
4. [Gereksinimler ve Kurulum](#gereksinimler-ve-kurulum)
5. [Uygulamayı Çalıştırma](#uygulamayı-çalıştırma)
6. [Derleme - PyInstaller](#derleme---pyinstaller)
7. [Firmware Imaj Başlığı](#firmware-imaj-başlığı)
8. [Sayfa Sayfa Kullanım Kılavuzu](#sayfa-sayfa-kullanım-kılavuzu)
   - [AES Key Üretimi (Keygen)](#1-aes-anahtar-üretimi-keygen)
   - [ECDSA Anahtar Üretimi](#2-ecdsa-anahtar-üretimi)
   - [İmzala ve Şifrele](#3-i̇mzala-ve-şifrele)
   - [Birleştir](#4-birleştir)
   - [Ayarlar](#5-ayarlar)
9. [Kaynakça](#kaynakça)

---

## Genel Bakış

ripperdoc, bir `bootloader` + `updater` + `application` katmanlı firmware mimarisinde kullanılan post-build (derleme sonrası) işlemlerini otomatikleştirir:

- **Anahtar üretimi**: AES-256 simetrik key/nonce üretimi ve ECDSA (P-256) asimetrik key çifti üretimi.
- **Başlık güncelleme**: Derlenmiş binary dosyanın başlığındaki versiyon ve güvenlik metaverisini günceller.
- **İmzalama ve şifreleme**: Binary verinin metnini AES-GCM ile şifreler, ECDSA-P256 ile imzalar.
- **Birleştirme**: Bootloader, updater ve application imajlarını, doğru flash ofsetlerinde tek bir birleşik binary dosyasında birleştirir.

Araç, **PySide6** ve **QFluentWidgets** kullanılarak Fluent Design arayüzüyle geliştirilmiştir.

---

## Özellikler

| Modül | Açıklama |
|---|---|
| **AES Key Üretimi** | 128/192/256 bit AES key ve nonce üretir, hex formatında görüntüler.
| **ECDSA Key Üretimi** | P-256 eğrisinde özel/genel key çifti üretir; PEM, `.bin` ve C header `.h` formatlarında dışa aktarım sağlar. |
| **İmzala ve Şifrele** | Güncellenmiş (`*_patched.bin`) bir binary'yi girdi olarak alır. Metni AES-256-GCM ile şifreler, SHA-256 özetini ECDSA-P256 ile imzalar ve sonucu başlığa yazar. |
| **Başlık Güncelleme** | Versiyon (major/minor/patch), güvenlik versiyonu ve vektör adresi gibi alanları başlığa yazar. |
| **Binary Birleştir** | Bootloader + Updater + Application imajlarını; her biri için bağımsız ofset/flash-taban-adresi ve bağımsız versiyon alanlarıyla tek bir çıktı dosyasında birleştirir. |

---

## Proje Yapısı

```
ripperdoc/
├── app.py                          # Uygulama giriş noktası
├── build.ps1                       # PyInstaller scripti
├── requirements.txt                # Python bağımlılıkları
├── scripts
│   └── generate_version.py         # git SHA'sını yazan script
└── tools_gui
    ├── core                        # İş mantığı (GUI'den bağımsız)
    │   ├── keygen.py               # AES ve ECDSA key üretimi
    │   ├── merge.py                # İmaj birleştirme
    │   ├── patch_header.py         # Başlık alanlarını güncelleme
    │   └── sign_encrypt.py         # İmzalama + AES-GCM şifreleme
    ├── i18n
    │   ├── en.json
    │   └── tr.json
    ├── services
    │   ├── build_info.py           # Git SHA / build bilgisi
    │   ├── i18n_service.py         # Dil dosyalarını yükler, çeviri sağlar
    │   ├── key_format_service.py   # Key kodlama ve kod çözme(hex, vb.)
    │   └── user_config.py          # platformdirs tabanlı config yönetimi
    └── ui
        ├── main_window.py          # Ana pencere, navigasyon, sayfa yönetimi
        ├── main_window.py            # Ana pencere, navigasyon, sayfa yönetimi
        └── pages/
            ├── keygen_page.py
            ├── ecdsa_keygen_page.py
            ├── sign_encrypt_page.py
            ├── merge_page.py
            └── settings_page.py
```

---

## Gereksinimler ve Kurulum

### Gereksinimler

`requirements.txt` içeriği:

```
PySide6
PySide6-Fluent-Widgets
platformdirs
pycryptodome
PySideSix-Frameless-Window
pyinstaller
```


### Kurulum Adımları

```powershell
# Sanal ortam oluştur
python -m venv .venv
.venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

---

## Uygulamayı Çalıştırma

```powershell
python app.py
```

---

## Derleme - PyInstaller

Windows için hazır bir PowerShell scripti mevcuttur:

```powershell
.\build.ps1
```

Bu script:

- `--onefile` ve `--windowed` bayraklarıyla tek dosyalık, konsolsuz bir `.exe` üretir.
- Çıktı adı: **RIPPERDOC**
- İkon olarak `favicon.ico` kullanılır.
- `tools_gui/i18n/en.json` ve `tr.json` dosyaları ile `favicon.ico`, `--add-data` ile pakete dahil edilir.

> **Not:** Derleme öncesi `scripts/generate_version.py` çalıştırılarak `tools_gui/version.py` içine güncel git SHA'sı gömülebilir; bu bilgi Ayarlar sayfasında "build: <sha>" olarak gösterilir.

```powershell
PS C:> python scripts/generate_version.py

PS C:> .\build.ps1
```

---

## Firmware Imaj Başlığı

Tüm işlemler, sabit boyutlu bir başlık üzerinde bayt seviyesinde çalışır. Aşağıdaki tablo, kod tabanında tanımlı gerçek ofsetleri yansıtır:

| Alan | Ofset | Boyut | Açıklama |
|---|---|---|---|
| `image_magic` | `0x00` | 4 bayt | `0xDEADC0DE` (APP) veya `0xC0FFEE00` (UPDATER) |
| `image_hdr_ver` | `0x04` | 2 bayt | Başlık formatı versiyonu (`0x0100`) |
| `image_type` | `0x06` | 1 bayt | `1` = UPDATER, `2` = APP |
| `flags` | `0x07` | 1 bayt | Şifreli/imzalı bayrağı |
| `version_major` | `0x08` | 1 bayt | |
| `version_minor` | `0x09` | 1 bayt | |
| `version_patch` | `0x0A` | 1 bayt | |
| `key_id` | `0x0B` | 1 bayt | |
| `security_version` | `0x0C` | 4 bayt | |
| `vector_addr` | `0x10` | 4 bayt | Binary dosyasının **Stack Pointer** adresi |
| `data_size` | `0x14` | 4 bayt | Başlık sonrası veri (**metin**) uzunluğu |
| `aes_gcm_nonce` | `0x18` | 12 bayt | Nonce (IV) |
| `gcm_tag` | `0x24` | 16 bayt | AES-GCM doğrulama tag'ı |
| `sha256` | `0x36` | 32 bayt | Metnin SHA-256 özeti |
| `ecdsa_signature` | `0x54` | 64 bayt | Ham ECDSA-P256 imzası |
| - | `0x94`..`0x1FF` | (kalan) | Rezerve / kullanılmayan alan (toplam başlık `0x200` bayta tamamlanır) |

> ***Önemli:*** **Başlık yapısında değişiklik yapmadan önce mutlaka orijinal C header/struct tanımını referans alın.**

---

## Sayfa Sayfa Kullanım Kılavuzu

### 1. AES Anahtar Üretimi (Keygen)

- **Algoritma:** AES
- **Key boyutu:** 128 / 192 / 256 bit seçilebilir
- **ÇALIŞTIR** butonu, kriptografik olarak güvenli rastgele bir key ve 12 baytlık nonce üretir.
- Üretilen key ve nonce hex formatında gösterilir.
- **Kopyala** butonu ile panoya kopyalama, **Dışa Aktar** butonu ile `.bin` dosyası olarak kaydetme yapılabilir.

### 2. ECDSA Anahtar Üretimi

- **ANAHTARLAR ÜRET** butonu, NIST P-256 eğrisinde bir özel/genel anahtar çifti üretir.
- **Genel anahtar:** Üç farklı formatta dışa aktarılabilir:
  - `.pem` (metin)
  - `.bin` (ham 65 baytlık nokta gösterimi: `0x04 || X(32) || Y(32)`)
  - `.h` (C header, `static const uint8_t gEcdsaPublicKey[65] = {...};` şeklinde)


### 3. İmzala ve Şifrele

Girdi olarak **güncellenmiş** bir ikili (`*_patched.bin`) beklenir.

**Adımlar:**
1. **Giriş binary** dosyasını seçin.
2. **ECDSA-P256 gizli anahtarı** (PEM) girin veya `.pem` dosyasından yükleyin.
3. **AES-256 anahtarı** (hex) girin veya `.bin/.key` dosyasından yükleyin.
4. **BAŞLAT** butonuna basın.

**İşlem mantığı:**
- İmaj başlığı doğrulanır. Tip `"UPDATER"` veya `"APP"` olmalıdır.
- Metin, SHA-256 ile özetlenir ve ECDSA-P256 ile imzalanır.
- Metin, AES-256-GCM ile şifrelenir. Nonce ve doğrulama tag'ı üretilir.
- `nonce`, `gcm_tag`, `sha256` ve `ecdsa_signature` alanları başlığa yazılır, ilgili bayraklar set edilir.
- Sonuç bir `.bin` dosyası olarak kaydedilir ve log konsolunda özet bilgiler (nonce, gcm_tag, sha256, signature, image_type, data_size) gösterilir.

### 4. Birleştir

Üç bağımsız slot:

- **Bootloader** — ham binary, başlık kontrolü **yapılmaz**.
- **Updater** — başlık kontrolü yapılır, `"UPDATER"` tipinden olmalıdır.
- **Application** — başlık kontrolü yapılır, `"APP"` tipinden olmalıdır.

Her binary seçildiğinde (bootloader hariç), başlık okunarak tespit edilen imaj tipi ve dosya boyutu ekranda gösterilir.

**Bellek yerleşimi alanları:**
| Alan | Varsayılan Değer |
|---|---|
| Updater ofseti | `0x00004000` |
| Application ofseti | `0x00040000` |
| Updater flash taban adresi | `0x08004000` |
| Application flash taban adresi | `0x08040000` |

**BİRLEŞTİR** butonuna basıldığında:
1. Updater ve Application imajları, girilen versiyon/güvenlik-versiyonu bilgileriyle önce **güncellenir**.
2. Bootloader + Updater + Application sırasıyla tek bir çıktıda birleştirilir.
3. Bootloader'ın Updater ofsetini, Updater'ın Application ofsetini aşması durumunda hata verilir (taşma kontrolü).
4. Sonuç `.bin` dosyası olarak kaydedilir.

### 5. Ayarlar

- **Dil:** İngilizce / Türkçe arasında anlık geçiş.
- **Tema:** Acrylic / Mica / Aero (Windows bulanıklık efektleri. `PySideSix-Frameless-Window` üzerinden uygulanır).

## Kaynakça

- [PySide6](https://pypi.org/project/PySide6)
- [PySide6-Fluent-Widgets](https://qfluentwidgets.com)
- [platformdirs](https://pypi.org/project/platformdirs/)
- [pyinstaller](https://pyinstaller.org/en/stable/)
- [Modern modes of operation for symmetric block ciphers](https://pycryptodome.readthedocs.io/en/v3.23.0/src/cipher/modern.html)
- [Crypto.Hash package](https://pycryptodome.readthedocs.io/en/v3.23.0/src/hash/hash.html)
- [Elliptic Curve Cryptography](https://pycryptodome.readthedocs.io/en/v3.23.0/src/public_key/ecc.html)
- [DSA and ECDSA](https://pycryptodome.readthedocs.io/en/v3.23.0/src/signature/dsa.html)