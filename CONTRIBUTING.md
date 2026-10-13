# Katkı Rehberi / Contributing

Katkıda bulunmak istediğiniz için teşekkürler! Bu proje, öğrencilerin gerçek projelerde deneyim kazanmasını hedefler; ilk katkınız küçük bir dokümantasyon düzeltmesi bile olabilir.

Thanks for contributing! This project exists so people can gain experience on real projects — even a small docs fix is a welcome first contribution.

## Nereden başlamalı? / Where to start

1. [README.md](README.md) ile vizyonu ve ürünleri okuyun.
2. Katkı yapacağınız ürünün belgelerine bakın: [FIRST](FIRST/README.md), [STEP](STEP/README.md), [INTO](INTO/README.md), [PATH](PATH/README.md).
3. Yeni bir özellik yerine önce açık bir issue ile tartışın; "good first issue" etiketli işler yeni başlayanlar içindir.

## Geliştirme akışı / Workflow

1. Depoyu fork'layın ve konu bazlı bir dal açın: `feat/...`, `fix/...`, `docs/...`
2. Değişikliğinizi yapın; mevcut kod stiline ve ürünün `kararlar.md` / `teknik-kararlar.md` belgelerine uyun.
3. İlgili testleri ve kontrolleri çalıştırın:
   - FIRST backend: `python manage.py test accounts --settings=config.test_settings`
   - FIRST frontend: `npm run lint && npm run typecheck && npm test`
   - Kök: `node .orchestrator/bin/orchestrator.mjs verify-system`
4. Anlamlı bir commit mesajı yazın (ör. `fix(first): ...`, `docs: ...`) ve pull request açın.
5. PR açıklamasında **ne** değiştiğini, **neden** değiştiğini ve **nasıl doğrulandığını** belirtin.

## Kurallar / Ground rules

- **Sır eklemeyin:** `.env`, anahtar, token veya kişisel veri commit etmeyin. Bkz. [SECURITY.md](SECURITY.md).
- **Karar ile uygulamayı ayırın:** Belgelerde "kararlaştırıldı", "uygulandı" ve "doğrulandı" farklı şeylerdir; doğrulanmamış bir şeyi doğrulanmış gibi yazmayın.
- **Güvenlik önce:** Kimlik doğrulama, ödeme ve yetkilendirme değişiklikleri için özellikle ayrıntılı açıklama ve test gerekir.
- **Davranış kuralları:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) herkes için geçerlidir.

## Lisans / License

Katkı yaparak değişikliklerinizin [Apache License 2.0](LICENSE) altında lisanslanmasını kabul etmiş olursunuz.
By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE).
