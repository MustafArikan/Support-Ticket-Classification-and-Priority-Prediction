# Data Schema — Support Ticket Classification & Priority Prediction

**Proje:** Çok dilli (EN/DE/TR) destek bileti sınıflandırma ve öncelik tahmin sistemi
**Faz:** 1 (Problem Definition & Data Collection) — Label Schema Finalization
**Tarih:** 2026-07-07

---

## 1. Kaynak Veri Setleri

| Kaynak | Ham Satır | Filtre Sonrası | Dil | Durum |
|---|---|---|---|---|
| Tobi-Bueck/customer-support-tickets | 28,587 | 28,529 | EN (16,308), DE (12,221) | Temizlendi, birleştirildi |
| TR Sentetik Üretim (Qwen3.5:9b, Kaggle) | 4,227 | 4,225 | TR | Temiz, doğrulanmış (bkz. §5) |
| **Birleşik (nihai)** | — | **32,754** | EN+DE+TR | `tickets_combined.jsonl` — şema doğrulamasından geçti ✅ |

Birleştirme script'i: `combine_datasets.py` — kullanım:
```bash
python combine_datasets.py --tr tickets_tr_full.jsonl --en_de en_de_mix_dataset.csv --output data/raw/tickets_combined.jsonl
```

---

## 2. Kolon Şeması

| Kolon | Tip | Zorunlu | Açıklama | Beklenen Değer Aralığı |
|---|---|---|---|---|
| `id` | string | Evet | Benzersiz kayıt kimliği | `{lang}_{source}_{6haneli_sayı}` örn. `tr_synth_000001` |
| `language` | category | Evet | Bilet dili | `en`, `de`, `tr` |
| `subject` | string | Hayır | Bilet konu başlığı | 1–700 karakter, **NaN olabilir** (EN/DE'de %13.4 satırda boş — gerçek veri karakteristiği); 25 satırda (%0.08) body benzeri uzun metin var, bilinen kaynak veri anomalisi |
| `body` | string | Evet | Bilet gövde metni | 20–5000 karakter, boş olamaz (20 karakterden kısa 58 satır EN/DE'de filtrelendi — kesilmiş/eksik ticket) |
| `answer` | string | Hayır | Destek ekibinin yanıtı (varsa) | 0–5000 karakter, NaN/boş olabilir |
| `type` | category | Evet | Bilet türü (ITIL benzeri) | `Request`, `Incident`, `Problem`, `Change` |
| `queue` | category | Evet | Ham yönlendirme kuyruğu (orijinal, 10 sınıf) | bkz. §3, referans/audit amaçlı saklanır |
| `category` | category | **Evet (hedef etiket 1)** | Eşlenmiş 5 sınıflı kategori | `Technical Issue`, `Billing`, `Refund`, `Account Management`, `General Inquiry` |
| `priority` | category | **Evet (hedef etiket 2)** | Öncelik seviyesi | `low`, `medium`, `high`, `critical` — **`critical` sadece TR verisinde var, EN/DE'de hiç yok** (bkz. §4) |
| `tag_1`...`tag_8` | string | Hayır | Serbest metin anahtar kelime etiketleri | EN/DE'de 8'e kadar, TR'de 5'e kadar; `tag_6`+ çoğunlukla boş (%2–21 dolu) |

---

## 3. Kategori Eşleme Tablosu (queue → category)

Ham veri setindeki 10 kuyruk (`queue`), roadmap'in önerdiği 5 sınıfa aşağıdaki gibi eşlenir. Bu eşleme `category` kolonunu üretir; `queue` kolonu audit/geri izlenebilirlik için ham haliyle korunur.

| Ham `queue` | Eşlenen `category` |
|---|---|
| Technical Support | Technical Issue |
| IT Support | Technical Issue |
| Product Support | Technical Issue |
| Service Outages and Maintenance | Technical Issue |
| Billing and Payments | Billing |
| Returns and Exchanges | Refund |
| Human Resources | Account Management |
| Customer Service | Account Management |
| General Inquiry | General Inquiry |
| Sales and Pre-Sales | General Inquiry |

**Not:** Bu eşleme Faz 2 EDA sırasında her queue'nun örnek içeriği incelenerek doğrulanmalı/gerekirse revize edilmelidir — özellikle "Human Resources" ve "Sales and Pre-Sales" sınır durumları için.

---

## 4. Priority Seviyeleri

| Seviye | Tanım | EN (n=16,308) | DE (n=12,221) | TR (n=4,225) |
|---|---|---|---|---|
| `low` | Acil olmayan, bilgi amaçlı talepler | 3,365 | 2,513 | 257 |
| `medium` | Standart operasyonel sorunlar | 6,603 | 4,884 | 336 |
| `high` | İş akışını etkileyen, hızlı müdahale gereken sorunlar | 6,340 | 4,824 | 632 |
| `critical` | Sistem kesintisi / acil iş etkisi olan sorunlar | **0** | **0** | 3,000 |

**⚠️ Kritik bulgu:** EN/DE ham veri setinde `critical` sınıfı **hiç yok** (0 satır) — bu sınıf yalnızca TR sentetik veride mevcut. Bu, TR sentetik verinin neden özellikle bu sınıfı hedeflediğini doğruluyor, ancak modelleme açısından ciddi bir risk taşıyor: model `critical` etiketini öğrenirken dil sinyaline (metnin TR olup olmadığına) aşırı bağımlı kalabilir, bu da gerçek dünyada (EN/DE'de gerçek bir critical ticket geldiğinde) genelleme başarısızlığına yol açabilir. Faz 2 EDA'da bu durum ayrıca incelenmeli; olası çözümler: (a) stratified split'te dil dengesine dikkat etmek, (b) modelin dil-bağımsız öğrendiğini doğrulamak için TR olmayan critical örnekleri de (varsa manuel/az sayıda) sisteme eklemek, (c) değerlendirmede dil kırılımlı confusion matrix incelemek.

---

## 5. Bilinen Veri Kalitesi Notları (TR seti için doğrulandı)

- Toplam satır: 4,227 ham → **4,225 net geçerli** (2 satır başarısız LLM üretim denemesinin "hayalet" kaydı, `error` alanı dolu; filtrelenmeli)
- JSON parse hatası: 0
- Gerçek HTML formatlama kalıntısı (`<br>`, `<i>` vb.): 40 satır (%0.95)
- Placeholder etiketleri (`<isim>`, `<product>`, `<error_code>` vb.): kasıtlı, anonimleştirme amaçlı — hata değil, olduğu gibi korunmalı
- Dil: %100 `tr`
- Boş `body`/`answer`/`subject`: yalnızca yukarıdaki 2 hayalet satırda

---

## 5b. Birleşik Veri Seti Özeti (32,754 satır)

| Kategori | Satır | Oran |
|---|---|---|
| Technical Issue | 19,624 | %59.9 |
| Account Management | 5,759 | %17.6 |
| Billing | 3,085 | %9.4 |
| General Inquiry | 2,552 | %7.8 |
| Refund | 1,734 | %5.3 |

`id` üretim şeması: TR verisinde zaten mevcut (`tr_synth_XXXXXX`); EN/DE için birleştirme sırasında üretildi: `{lang}_source_{6haneli sıra no}` (örn. `en_source_000001`).

## 6. Beklenen Zorunlu Kurallar (validasyon için)

1. `id` benzersiz olmalı (dataset geneli, EN+DE+TR birleşik)
2. `error` alanı dolu olan satırlar birleştirme öncesi filtrelenmeli
3. `category` ∈ {5 sınıf}, `priority` ∈ {4 seviye} — bunların dışında değer olamaz
4. `body` boş olamaz, minimum 20 karakter
5. `language` ∈ {en, de, tr}
6. Aynı müşteriye ait biletler (eğer `customer_id` gibi bir alan varsa) train/val/test split'e dağılırken data leakage kontrolüne tabi tutulmalı (Faz 2)
