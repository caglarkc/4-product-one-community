# Güvenlik Politikası / Security Policy

## Güvenlik açığı bildirme / Reporting a vulnerability

Bir güvenlik açığı bulduysanız **herkese açık issue açmayın.** Bunun yerine GitHub'ın özel bildirim özelliğini kullanın:

**Security → Report a vulnerability** (<https://github.com/caglarkc/4-product-one-community/security/advisories/new>)

If you find a vulnerability, **please do not open a public issue.** Use GitHub's private vulnerability reporting via the link above.

Bildirimde şunları belirtin / Please include:

- Etkilenen ürün ve bileşen (FIRST / STEP, backend / frontend / desktop) — affected product and component
- Yeniden üretme adımları — reproduction steps
- Olası etki — potential impact

## Kapsam / Scope

- Kimlik doğrulama, oturum ve yetkilendirme
- Ödeme, kredi ve ledger tutarlılığı (STEP)
- Özel dosya/medya erişimi ve özel repo vitrini (FIRST)
- Girdi doğrulama, CSRF/CORS, bilgi sızıntısı

## Sır yönetimi / Secrets

Gerçek anahtar, parola veya token'lar depoya **asla** eklenmemelidir. Yalnızca `.env.example` şablonları paylaşılır. Yanlışlıkla bir sır gördüyseniz yukarıdaki kanaldan bildirin.

Real keys, passwords and tokens must never be committed. Only `.env.example` templates are shared.

## Destek verilen sürümler / Supported versions

Proje aktif geliştirme altındadır; yalnızca `main` dalı desteklenir.
The project is under active development; only the `main` branch is supported.
