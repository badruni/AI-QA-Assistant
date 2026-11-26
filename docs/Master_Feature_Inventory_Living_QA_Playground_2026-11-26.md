# Master Feature Inventory — Living QA Playground

**Tanggal audit:** 26 November 2026
**Sumber frontend:** `QA_Playground_Source_20261126_113647.zip` (17 entries)
**Sumber server:** `playground_server.py` (1,388 bytes)
**Jenis audit:** source inspection; bukan verifikasi runtime menyeluruh.

## Aturan membaca status

- **Implemented:** struktur/behavior yang diminta tampak jelas pada source.
- **Partial:** sebagian pola ada, tetapi belum memenuhi komponen secara lengkap atau hanya statis.
- **Not Implemented:** tidak ditemukan implementasi yang mendukung komponen pada source yang diperiksa.
- **Out of Scope:** hanya boleh dipakai setelah ada keputusan eksplisit dan alasan; tidak digunakan untuk mengurangi baseline 56.
- Status ini adalah hasil source inspection. Status Pass/Fail runtime belum ditetapkan.

## Ringkasan hasil

- Baseline wajib: **56 komponen**.
- Implemented: **21**.
- Partial: **19**.
- Not Implemented: **16**.
- Out of Scope: **0** (tidak ada yang dikeluarkan dari baseline).

> Angka di atas adalah klasifikasi source awal, bukan hasil pengujian browser. Beberapa status Implemented tetap memerlukan runtime verification.

## A. Master inventory — 56 baseline components

### Navigation & Layout

| No. | Komponen | Status source | Bukti source | Gap / catatan | Test relevan |
|---:|---|---|---|---|---|
| 1 | Header | **Implemented** | `index.html`: `.topbar`, `.main-nav`, `.top-actions`; CSS sticky header. | Desktop header and main navigation exist. QA Lab nav is not present. | Normal, Accessibility, Responsive |
| 2 | Logo | **Implemented** | `.brand`, `.brand-name`, `.hero-brand`; local `mdz-logo.svg` also exists in assets. | Logo/brand treatment exists in header, hero and footer; image asset presence should be verified for actual usage. | Normal, Accessibility, Responsive |
| 3 | Hamburger Menu | **Implemented** | `#menuOpen`, `#mobileDrawer`, `#menuClose`, `#drawerScrim`; JS open/close handlers. | Mobile drawer opens/closes and Escape handler calls close; focus management and inert background are not implemented. | Normal, Negative, Accessibility, Responsive |
| 4 | Expandable Sidebar | **Not Implemented** | No expandable sidebar structure or dedicated JS behavior found. | Mobile drawer is not an expandable sidebar; do not count it as this component. | Normal, Negative, Accessibility, Responsive |
| 5 | Overlay Navigation | **Partial** | Mobile drawer plus `.drawer-scrim` overlay on small screens. | Overlay exists for the mobile drawer only; no separate overlay navigation pattern or keyboard/focus treatment. | Normal, Negative, Accessibility, Responsive |
| 6 | Bottom Navigation | **Not Implemented** | No bottom navigation markup or styles found. | No persistent bottom navigation component. | Normal, Accessibility, Responsive |
| 7 | Footer | **Implemented** | `footer.site-footer`, `.footer-links`, `.social-links`. | Footer structure and links exist; links currently point to local placeholder anchors. | Normal, Accessibility, Responsive |
| 8 | Floating Go to Top | **Partial** | `#backTop`; JS calls `window.scrollTo`; CSS positions button inside footer, not fixed/floating. | Back-to-top action exists, but component is not floating/always available as its name implies. | Normal, Accessibility, Responsive |

### Homepage & Content

| No. | Komponen | Status source | Bukti source | Gap / catatan | Test relevan |
|---:|---|---|---|---|---|
| 9 | Hero Banner | **Implemented** | `section.hero`, `.hero-copy`, `.hero-visual`. | Hero section with copy, CTA and visual exists. | Normal, Accessibility, Responsive |
| 10 | Image Carousel / Slider | **Implemented** | `#heroCarousel`; JS `showHeroSlide`, previous/next, preload, pointer swipe. | Four-slide carousel with arrows, indicators, keyboard arrows and pointer swipe handlers. | Normal, Negative, Accessibility, Responsive |
| 11 | Carousel Indicator | **Implemented** | Four `.dot` buttons with `aria-current`; JS updates active state. | Indicators are interactive and active state is updated by JS. | Normal, Negative, Accessibility, Responsive |
| 12 | CTA Button | **Implemented** | `.btn-primary` anchor and `.btn-outline` trailer button. | Join Community navigates to section; trailer button currently displays placeholder toast. | Normal, Negative, Accessibility, Responsive |
| 13 | What's On Section | **Implemented** | `section.top-panels` contains `.whats-on`. | Section and event summary panel exist as static content. | Normal, Responsive |
| 14 | Event Card | **Partial** | `.event-feature` with date, title, location and image. | One static featured event card; no detail route or event interaction. | Normal, Negative, Responsive |
| 15 | Winner Table | **Implemented** | `.winner-panel`, `.table-wrap`, semantic table with thead/tbody. | Static three-row table exists; responsive handling is horizontal scroll wrapper. | Normal, Negative, Accessibility, Responsive |
| 16 | Horizontal Carousel | **Not Implemented** | No carousel track/controls for a horizontal content list found. | Hero carousel is a slide carousel, not a horizontal multi-card carousel. | Normal, Negative, Accessibility, Responsive |
| 17 | Highlights Section | **Implemented** | `section.highlights`, `.highlight-list`, five `.highlight-card` anchors. | Highlights content section and five image cards exist. | Normal, Negative, Accessibility, Responsive |
| 18 | Category Card | **Partial** | Highlight cards show category-like labels (Car Review, Modification, Motorsport, Lifestyle, Family Garage). | Cards visually represent categories but are not a distinct category-card component or category destination. | Normal, Negative, Accessibility, Responsive |
| 19 | Latest Discussions | **Implemented** | `.discussions`, `.discussion-list` with three discussion entries. | Discussion listing exists as static content. | Normal, Negative, Accessibility, Responsive |
| 20 | Discussion Card | **Partial** | Each `.discussion` row contains avatar, title, author, timestamp and stats. | A discussion row pattern exists, but it is static and has no detail/action behavior. | Normal, Negative, Accessibility, Responsive |
| 21 | Comment Input | **Not Implemented** | No comment form or input found. | No comment composer or submit interaction. | Normal, Negative, Accessibility, Responsive |
| 22 | Comment Thread | **Not Implemented** | No thread detail/reply structure found. | Discussion list is not a comment thread. | Normal, Negative, Accessibility, Responsive |
| 23 | Nested Comments | **Not Implemented** | No nested/reply comment markup found. | No nested discussion hierarchy. | Normal, Negative, Accessibility, Responsive |
| 24 | Like Button | **Not Implemented** | No like control or state handler found. | No like interaction. | Normal, Negative, Accessibility |
| 25 | Comment Counter | **Partial** | Discussion stats contain static comment-like numbers (e.g. 54, 37, 89). | Counters are visual text only; not tied to comments or changing state. | Normal, Negative, Accessibility |
| 26 | View Counter | **Partial** | Discussion stats contain static view-like values (e.g. 2.3K, 1.1K, 4.8K). | Values are static display text, not tracked view counts. | Normal, Negative |
| 27 | Reels Section | **Partial** | `.reels` section with one `.reel-image` preview. | A reels-like panel exists, but it contains a static image preview, not a reel/video feed. | Normal, Negative, Responsive |
| 28 | Video Card | **Partial** | `.reel-image` button contains image, play icon and duration label. | Video-card appearance exists, but it does not represent a playable video. | Normal, Negative, Accessibility, Responsive |
| 29 | Video Play Button | **Partial** | `.play-button` is a decorative span inside `.reel-image`. | Play icon is visual only; click opens image modal via `.media-open`, not video playback. | Normal, Negative, Accessibility |
| 30 | Gallery Section | **Implemented** | `section.gallery`, `.gallery-grid`, three image buttons. | Gallery section and three image entries exist. | Normal, Negative, Accessibility, Responsive |
| 31 | Masonry Grid | **Not Implemented** | Gallery uses regular CSS Grid; no masonry layout found. | A regular grid is not a masonry grid. | Normal, Responsive |
| 32 | Infinite Scroll | **Not Implemented** | No IntersectionObserver, scroll-triggered append, or paging data flow found. | No infinite loading behavior. | Normal, Negative, Responsive |

### Interactive Components

| No. | Komponen | Status source | Bukti source | Gap / catatan | Test relevan |
|---:|---|---|---|---|---|
| 33 | Hover Interaction | **Implemented** | CSS hover rules for nav, highlight cards, discussion table rows, reel/gallery images. | Hover states exist; keyboard-equivalent states need separate validation. | Normal, Accessibility, Responsive |
| 34 | Tooltip | **Not Implemented** | No tooltip markup/behavior or `title`-based tooltip component found. | No explicit tooltip component. | Normal, Accessibility, Responsive |
| 35 | Expand / Collapse | **Partial** | Mobile drawer expands/collapses through `.open`; no generic disclosure/accordion component. | One specialized drawer state exists, not a reusable expand/collapse pattern. | Normal, Negative, Accessibility, Responsive |
| 36 | Scrollable Container | **Partial** | `.table-wrap` uses `overflow-x:auto`. | One horizontally scrollable table wrapper exists; no general scroll-container component. | Normal, Negative, Accessibility, Responsive |
| 37 | Horizontal Scroll | **Partial** | `.table-wrap` and responsive content overflow handling. | Horizontal scroll is present for the table only; no standalone horizontal scroller component. | Normal, Negative, Accessibility, Responsive |
| 38 | Vertical Scroll | **Not Implemented** | Page uses normal document scrolling; no dedicated vertical scroll container found. | Normal page scroll is not a dedicated vertical scrollable component. | Normal, Accessibility, Responsive |
| 39 | Modal / Popup | **Implemented** | `#imageModal`, `#modalClose`, `#modalImage`; JS open/close, focus transfer/trap/restore, body scroll lock. | Image modal implemented with accessibility behavior; it is image-viewer-specific, not a general-purpose modal framework. | Normal, Negative, Accessibility, Responsive |
| 40 | Floating Button | **Partial** | `#backTop` is a button in footer; CSS not fixed except relative positioning on mobile footer. | Back-to-top action exists, but no general floating action button component. | Normal, Accessibility, Responsive |
| 41 | Loading Indicator | **Not Implemented** | No loading spinner/progress UI found. | Image preload is internal JS behavior; no user-visible loading indicator. | Normal, Negative, Accessibility |

### Content & Navigation Components

| No. | Komponen | Status source | Bukti source | Gap / catatan | Test relevan |
|---:|---|---|---|---|---|
| 42 | Category Label | **Partial** | Text labels inside `.highlight-card` and section headings. | Category-like labels exist as card captions, but no reusable category-label component. | Normal, Accessibility, Responsive |
| 43 | Article Card | **Partial** | Highlight cards resemble article/category tiles. | No article metadata, summary, author/date or article detail behavior. | Normal, Negative, Accessibility, Responsive |
| 44 | Content Thumbnail | **Implemented** | Images used in event, highlights, reels preview and gallery cards. | Thumbnail images exist with varied contexts; some highlight images have empty alt text. | Normal, Negative, Accessibility, Responsive |
| 45 | Content Grid | **Partial** | `.highlight-list` and `.gallery-grid` use CSS Grid. | Grid layouts exist for highlights/gallery, but no general content-grid component/data pattern. | Normal, Negative, Responsive |
| 46 | Pagination | **Not Implemented** | No pagination markup or JS found. | No page navigation for multi-page content. | Normal, Negative, Accessibility |
| 47 | Load More / More Threads | **Not Implemented** | No load-more button or append behavior found. | No incremental content loading. | Normal, Negative, Accessibility |
| 48 | Gallery Image Viewer | **Implemented** | `.media-open` buttons; `openModal(btn)` loads `data-image` into `#modalImage`. | Gallery viewer opens image modal; test all images and failure cases separately. | Normal, Negative, Accessibility, Responsive |

### Responsive Components

| No. | Komponen | Status source | Bukti source | Gap / catatan | Test relevan |
|---:|---|---|---|---|---|
| 49 | Responsive Header | **Implemented** | CSS breakpoint at 760px hides desktop nav and displays mobile menu; 1050px adjusts header. | Desktop/mobile header variants are implemented in CSS. | Normal, Negative, Accessibility, Responsive |
| 50 | Responsive Sidebar | **Not Implemented** | No sidebar component; mobile drawer is a navigation drawer. | No responsive sidebar with expandable/collapsible sidebar behavior. | Normal, Accessibility, Responsive |
| 51 | Responsive Bottom Navigation | **Not Implemented** | No bottom navigation markup or mobile-specific bottom bar found. | No bottom navigation component at any viewport. | Normal, Accessibility, Responsive |
| 52 | Responsive Grid | **Implemented** | `.top-panels`, `.bottom-panels`, `.highlight-list`, `.gallery-grid` change layout at 1050px/760px. | Several grids adapt at breakpoints; needs browser verification for overflow and content fit. | Normal, Negative, Responsive |
| 53 | Responsive Carousel | **Implemented** | Hero carousel remains active; hero and image height/layout change at 760px/390px. | Responsive carousel layout exists; touch/swipe behavior still requires runtime tests on target devices/viewports. | Normal, Negative, Accessibility, Responsive |
| 54 | Responsive Card | **Partial** | Event, highlight, discussion and gallery cards receive responsive sizing/layout changes. | Cards adapt through parent layouts, but no complete reusable card system or per-card responsive rules. | Normal, Negative, Responsive |
| 55 | Responsive Table | **Partial** | `.table-wrap{overflow-x:auto}` wraps winner table. | Horizontal overflow is supported; no alternate mobile table presentation or explicit keyboard/scroll affordance. | Normal, Negative, Accessibility, Responsive |
| 56 | Responsive Gallery | **Implemented** | `.gallery-grid` rows and layout change at 760px; images use object-fit cover. | Gallery grid adapts for mobile; verify actual image crop, tap targets and modal sizing at viewports. | Normal, Negative, Accessibility, Responsive |

## B. Recommended Extensions — 16 usulan

Extension berikut bukan bagian dari baseline 56 dan belum disetujui sebagai scope implementasi. Evaluasi overlap dilakukan agar tidak membuat komponen duplikat.

| ID | Extension | Kondisi / overlap dengan source dan baseline | Rekomendasi awal |
|---|---|---|---|
| EXT-001 | Form & Input Controls | Belum ada; Comment Input #21 juga belum ada. | Distinct extension; can host inputs needed by form and CMS scenarios. |
| EXT-002 | Form Validation States | Belum ada. | Distinct extension; pair with EXT-001, include required/invalid/success states. |
| EXT-003 | File Upload | Belum ada. | Distinct extension; local-only test fixtures, safe file type/size checks. |
| EXT-004 | Search & Filter | Search button exists but only toast; no search/filter behavior. | Distinct extension; implement local content search/filter. |
| EXT-005 | Sorting Controls | Belum ada. | Distinct extension; useful for table/list and CMS content. |
| EXT-006 | Tabs | Belum ada. | Distinct extension; separate from baseline navigation; test tablist semantics. |
| EXT-007 | Accordion | No accordion markup; baseline #35 Expand / Collapse is partial via drawer. | Potential overlap: treat accordion as a pattern/variant under #35 unless user approves separate catalog entry. |
| EXT-008 | Breadcrumbs | Belum ada. | Distinct extension; useful for nested CMS/page navigation. |
| EXT-009 | Toast & Alert | `#toast` exists and is used for placeholder messages. | Partial existing implementation; extend to reusable success/warning/error/info states. |
| EXT-010 | Skeleton Loading | Belum ada. | Distinct extension; complementary to #41 Loading Indicator. |
| EXT-011 | Empty State | Belum ada. | Distinct extension; useful when lists/search results contain no items. |
| EXT-012 | Error State | Toast exists, but no content-level error state. | Distinct extension; page/component-level failure display. |
| EXT-013 | Video Player | No player; current Reels control opens image modal. | Distinct extension; native HTML video can avoid new dependency. |
| EXT-014 | Lazy Loading | No loading=lazy or IntersectionObserver found in supplied source. | Distinct extension; consider native loading=lazy first. |
| EXT-015 | Sticky Elements | `.topbar` uses `position:sticky; top:0`. | Already present as CSS behavior; extension may be reframed as Sticky Element test coverage, not a new component. |
| EXT-016 | Cookie Consent | Belum ada. | Distinct extension; local preference persistence and accessible dialog/banner. |

### Ringkasan overlap

- EXT-007 Accordion: overlap konseptual dengan #35 Expand / Collapse. Usulan: jadikan pola/varian #35, bukan otomatis kategori baru.
- EXT-009 Toast & Alert: sudah ada toast dasar; status Partial dan perlu diperluas jika disetujui.
- EXT-013 Video Player: bukan duplikasi #27–29 karena Reels/Video Card/Play Button saat ini hanya preview gambar.
- EXT-014 Lazy Loading: belum ditemukan pada source; pertimbangkan native browser lazy loading sebelum menambah JS.
- EXT-015 Sticky Elements: sticky header sudah ada pada CSS. Rekomendasi: masukkan sebagai test/behavior pada #1/#49, bukan komponen baru.
- EXT-001–006, EXT-008, EXT-010–012, EXT-016: belum ditemukan implementasi yang setara pada source yang diperiksa.

## C. Server audit — Security Behavior prerequisites

Server menggunakan `ThreadingHTTPServer` dan `SimpleHTTPRequestHandler`, bind ke `127.0.0.1:8000`, root ke folder `playground`, membatasi `translate_path()` agar resolved path tetap berada di root, dan membatasi path yang dicatat di log.

Dari source server yang diberikan, belum ada custom route untuk HTTP 401, 403, 500, redirect, atau endpoint skenario khusus. Static file server secara alami dapat mengembalikan 404 untuk resource yang tidak ditemukan, tetapi route/behavior ini tetap perlu runtime verification.

Rencana Security Behavior Lab perlu endpoint lokal yang eksplisit dan hanya tersedia pada loopback. Jangan mengubah server sebelum desain endpoint, expected response, log safety, dan regression test disetujui.

## D. Requirements/Test Matrix — kerangka cakupan

| QA category | Requirement / coverage | Komponen yang relevan | Contoh acceptance criteria |
|---|---|---|---|
| Normal Scenarios | Uji fungsi normal dari komponen yang benar-benar interaktif dan konten statis yang diharapkan | 1–56 sesuai perilaku | Aksi yang tersedia menghasilkan hasil yang diharapkan; konten dan navigasi tampil benar |
| Negative Test Lab | Skenario gagal sengaja dengan penanda dan expected result | Gambar, link, form, media, komponen interaktif, endpoint lokal | Skenario gagal hanya aktif di lab; scanner melaporkan bukti yang sesuai dan tidak salah menganggap placeholder normal sebagai bug |
| Accessibility Lab | Keyboard, fokus, nama/label, semantic structure, ARIA, contrast | 1–56 sesuai interaksi dan semantik | Kontrol dapat dioperasikan dengan keyboard; fokus terlihat dan urutannya masuk akal; label/semantik sesuai |
| Responsive Lab | Viewport desktop/tablet/mobile, overflow, ukuran target dan susunan | 1–56; terutama 49–56 | Tidak ada overflow tak diinginkan; komponen tetap dapat dipakai pada viewport yang ditetapkan |
| Security Behavior Lab | Status HTTP, redirect, resource restriction, response headers | Endpoint lokal dan komponen yang memang memerlukan alur akses | Hasil sesuai endpoint lokal; tidak ada akses eksternal atau bypass; 403 threshold scanner tetap dihormati |

Catatan: tabel ini adalah kerangka requirement, bukan klaim bahwa semua komponen sudah mempunyai test case rinci atau telah lulus.

## E. Prioritas gap untuk Full Project Delivery

1. QA Lab navigation + landing page + dropdown desktop/mobile.
2. Component catalog UI/registry untuk menampilkan 56 baseline dan statusnya.
3. Komponen interaksi yang belum ada: expandable sidebar, overlay navigation pattern, bottom navigation, horizontal carousel, comment input/thread/nested replies, like, masonry, infinite scroll, tooltip, generic expand/collapse, dedicated scroll containers, loading indicator, pagination, load more.
4. Lengkapi komponen partial: event/discussion/article/category cards, counters, reels/video, back-to-top floating behavior, responsive table/card.
5. Evaluasi 16 extensions dan persetujuan scope.
6. Lima QA labs dan scenario metadata.
7. Endpoint Security Behavior lokal, evidence, regression, dokumentasi.

## F. Batasan audit dan hal yang belum diverifikasi

- Source ZIP berisi frontend dan aset; tidak berisi server source. Server diperiksa terpisah dari file `playground_server.py`.
- Belum dilakukan browser runtime audit untuk setiap komponen.
- Belum dilakukan keyboard/screen-reader audit menyeluruh.
- Belum dilakukan viewport sweep untuk semua breakpoint dan komponen.
- Belum dilakukan HTTP endpoint test untuk Security Behavior Lab.
- Belum dilakukan pengujian integrasi dengan AI QA Assistant scanner untuk seluruh 56 komponen.
- Status komponen dapat berubah setelah runtime verification; perubahan status harus disertai evidence.

## G. Keputusan yang diminta dari pengguna

1. Review status source untuk 56 komponen, terutama yang Partial.
2. Konfirmasi apakah Accordion menjadi varian #35 Expand / Collapse, bukan komponen ke-57.
3. Konfirmasi apakah Sticky Elements dicatat sebagai behavior/test coverage pada Header, bukan extension baru.
4. Tentukan apakah seluruh 16 extensions masuk scope delivery atau hanya yang disetujui setelah prioritas dan effort dibahas.
5. Setelah inventory disetujui, lanjutkan Requirements/Test Matrix rinci dan Final Technical Design. Belum ada source code yang diubah.

## H. Standar Operasional Pengembangan

Satu batch per tahap; perintah PowerShell siap salin; tunggu hasil sebelum melanjutkan; diagnosis error sebelum perubahan; backup sebelum perubahan signifikan; pertahankan fitur yang berfungsi; validasi setiap perubahan; dokumentasikan arsitektur/dependensi/cara menjalankan; jangan memindahkan virtualenv; jangan menyimpan secret; patuhi batas 403; jangan commit kecuali diminta; bedakan source inspection, browser observation, automated test, dan manual test.
