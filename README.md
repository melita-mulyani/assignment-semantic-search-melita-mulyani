## 1. Memahami Problem Statement

### Tujuan (Objective)

Tujuan proyek ini adalah membangun prototipe aplikasi *semantic search* yang terintegrasi dengan *Large Language Model* (LLM) untuk knowledge base FAQ e-commerce.

Sistem dirancang untuk mengambil entri FAQ yang relevan berdasarkan makna pertanyaan pengguna, bukan hanya berdasarkan kecocokan kata kunci secara persis. Informasi yang ditemukan kemudian diberikan kepada LLM sebagai konteks untuk menghasilkan jawaban yang relevan dan sesuai dengan pertanyaan pengguna.

Pendekatan ini bertujuan membantu pengguna menemukan jawaban atas pertanyaan yang sering diajukan secara lebih alami, termasuk ketika mereka menggunakan kata-kata atau susunan kalimat yang berbeda dari FAQ asli.

### Sumber dan Struktur Knowledge Base

Knowledge base yang digunakan berasal dari file CSV bernama `ecommerce_faq_knowledge_base.csv`, yang disimpan di dalam direktori `data/`.

Dataset ini berisi informasi FAQ e-commerce yang menjadi sumber pengetahuan bagi aplikasi semantic search dan LLM. Setiap entri FAQ digunakan sebagai satu unit informasi yang akan dicari, dengan menggabungkan pertanyaan dan jawabannya agar sistem dapat menemukan informasi yang relevan berdasarkan pertanyaan pengguna.

File CSV asli akan tetap dipertahankan dan tidak diubah selama proses pengolahan data. Entri FAQ akan diubah menjadi vektor embedding dan disimpan dalam indeks FAISS untuk mendukung pencarian berdasarkan kemiripan makna (*semantic similarity search*).

### Batasan dan Asumsi

Prototipe ini dikembangkan dengan batasan dan asumsi berikut:

- **Jawaban berdasarkan knowledge base:** LLM harus menghasilkan jawaban berdasarkan informasi FAQ yang ditemukan melalui proses retrieval.
- **Tidak memberikan informasi yang tidak didukung:** Jika konteks hasil retrieval tidak memuat informasi yang cukup untuk menjawab pertanyaan, sistem harus menyampaikan bahwa jawabannya tidak tersedia dalam FAQ yang diberikan, alih-alih mengarang informasi.
- **Pencarian semantik:** Sistem menggunakan embedding vektor dan FAISS untuk menemukan entri FAQ berdasarkan kemiripan makna. Kualitas hasil pencarian bergantung pada relevansi entri FAQ yang tersedia dan representasi embedding yang dihasilkan.
- **Sumber pengetahuan tetap:** Sistem menggunakan dataset FAQ yang diberikan sebagai sumber pengetahuan. Sistem tidak secara otomatis mengakses situs web eksternal, data e-commerce terkini, atau sumber pengetahuan lainnya.
- **Cakupan prototipe:** Aplikasi dikembangkan untuk keperluan assignment dan belum dianggap sebagai sistem layanan pelanggan yang siap digunakan dalam lingkungan produksi.


## 2. Pengecekan Struktur/Isi Data Awal

UKURAN DATA: (59, 4)

KOLOM: ['faq_id', 'category', 'question', 'answer']

CONTOH 5 BARIS:
 faq_id || category || question || answer
      1 || Pemesanan || Bagaimana cara melakukan pemesanan di platform ini? || Pilih produk yang diinginkan, klik 'Tambah ke Keranjang', lalu lanjutkan ke halaman checkout untuk mengisi alamat pengiriman dan metode pembayaran.
      2 || Pemesanan || Apakah saya bisa memesan tanpa membuat akun? || Saat ini pemesanan hanya bisa dilakukan setelah membuat akun, agar Anda dapat melacak status pesanan dengan mudah.
      3 || Pemesanan || Bagaimana cara membatalkan pesanan yang sudah dibuat? || Pesanan dapat dibatalkan melalui halaman 'Pesanan Saya' selama status masih 'Diproses'. Setelah status berubah menjadi 'Dikirim', pembatalan tidak dapat dilakukan.
      4 || Pemesanan || Berapa lama waktu yang dibutuhkan sebelum pesanan diproses penjual? || Penjual biasanya memproses pesanan dalam waktu 1x24 jam setelah pembayaran dikonfirmasi.
      5 || Pemesanan || Apakah saya bisa mengubah alamat pengiriman setelah pesanan dibuat? || Perubahan alamat hanya bisa dilakukan sebelum pesanan berstatus 'Dikirim'. Silakan hubungi customer service secepatnya jika ingin mengubah alamat.

DATA KOSONG:
faq_id      0
category    0
question    0
answer      0

JUMLAH FAQ PER KATEGORI:
category
Pemesanan           9
Pengiriman          9
Pembayaran          8
Pengembalian        8
Akun                7
Produk              7
Promo               6
Customer Service    5
Total               59

DAFTAR KATEGORI:
['Pemesanan', 'Pengiriman', 'Pembayaran', 'Pengembalian', 'Akun', 'Promo', 'Produk', 'Customer Service']

Hasil pemeriksaan awal menunjukkan bahwa tidak terdapat nilai kosong pada keempat kolom dataset.

Pada tahap pemrosesan, kolom question dan answer akan digabungkan menjadi satu unit teks yang digunakan dalam proses semantic search. Kolom faq_id digunakan untuk mengidentifikasi setiap entri, sedangkan category memberikan informasi mengenai kelompok topik FAQ.

## 3. System Workflow
Sistem menggunakan alur berikut:

Ingest → Embed → Store → Retrieve → Generate

3.1. Ingest

Dataset FAQ dibaca dari file CSV menggunakan Pandas. Setiap FAQ dipersiapkan menjadi satu unit teks yang menggabungkan pertanyaan dan jawaban.

Contoh format:

Q: Bagaimana cara melakukan pemesanan di platform ini? 
A: [jawaban dari FAQ]

Penggabungan pertanyaan dan jawaban membantu sistem mencocokkan query pengguna dengan informasi FAQ yang relevan.

3.2. Embed

Setiap unit teks dikonversi menjadi embedding menggunakan Gemini Embedding API. Embedding merupakan representasi numerik yang menggambarkan makna teks.

Hasil eksperimen menghasilkan matriks embedding dengan ukuran (59, 3072), yang berarti terdapat 59 vektor dengan masing-masing 3.072 dimensi.

3.3. Store

Embedding disimpan dalam indeks FAISS menggunakan IndexFlatL2.

FAISS digunakan untuk mencari vektor yang paling dekat dengan embedding query pengguna. Setelah proses penambahan data, indeks berisi 59 vektor.

Metode L2 distance digunakan untuk mengukur jarak ant vektor. Semakin kecil jarak, semakin dekat representasi vektor tersebut dalam ruang embedding.

Namun, jarak yang kecil tidak otomatis menjamin bahwa FAQ benar-benar menjawab kebutuhan pengguna.

3.4. Retrieve

Ketika pengguna memasukkan pertanyaan, sistem membuat embedding untuk query tersebut, kemudian mencari tiga FAQ terdekat menggunakan FAISS (top_k=3).

Hasil retrieval berupa daftar FAQ beserta informasi jaraknya. FAQ yang ditemukan kemudian diteruskan sebagai konteks untuk proses generasi jawaban.

3.5. Generate

FAQ hasil retrieval digunakan sebagai konteks bagi LLM melalui Gemini API.

Prompt dirancang agar model:

Menjawab berdasarkan konteks FAQ yang tersedia.

Tidak mengarang informasi yang tidak didukung oleh FAQ.

Menyampaikan bahwa informasi belum tersedia jika konteks tidak menjawab pertanyaan.

Menyarankan pengguna menghubungi customer service jika diperlukan.

Model yang berhasil digunakan dalam eksperimen adalah gemini-3.5-flash-lite.

## 4. Hasil Embeddings

Shape embeddings: (59, 3072)
Artinya:
- 59 = ada 59 FAQ yang berhasil diubah menjadi embedding.
- 3072 = setiap FAQ direpresentasikan sebagai vektor dengan 3.072 nilai numerik.
- Embeddings = representasi numerik yang menangkap makna teks sehingga kita bisa mencari FAQ berdasarkan kemiripan makna, bukan hanya kecocokan kata.

## 5. Analisis Hasil Semantic Search 

- Embedding: pertanyaan pengguna berhasil diubah menjadi vektor menggunakan Gemini Embeddings API.
- Vector search: FAISS berhasil menemukan tiga FAQ dengan jarak vektor terkecil.
- Semantic matching: sistem menemukan pertanyaan dengan makna yang serupa, walaupun kalimat pengguna, “kenapa paket saya belum sampai?”, tidak sama persis dengan FAQ yang tersimpan.

Nilai distance bukan persentase akurasi atau tingkat keyakinan. Nilai yang lebih kecil menunjukkan jarak yang lebih dekat berdasarkan metrik L2 yang digunakan.

## 6.a. Testing Results and Relevance Analysis
Pengujian dilakukan menggunakan lima query yang mewakili pertanyaan langsung, variasi istilah, pertanyaan tentang pengiriman, dan pertanyaan yang tidak tercakup secara spesifik dalam knowledge base.

No. 1

Query: Bagaimana cara melakukan pemesanan di platform ini?

FAQ yang Ditemukan: ID 1 — Cara melakukan pemesanan

Evaluasi: Baik. Query sesuai dengan FAQ yang ditemukan dan jawaban yang dihasilkan relevan.

No. 2

Query: Bisakah saya membatalkan order yang sudah saya buat?

FAQ yang Ditemukan: ID 3 — Pembatalan pesanan

Evaluasi: Baik. Sistem dapat mengenali variasi istilah “order” dan “pesanan”.

No. 3

Query: Kenapa paket saya belum sampai?

FAQ yang Ditemukan: ID 12 — Paket melewati estimasi; ID 14 — Status pengiriman tidak berubah; ID 52 — Nomor resi belum bisa dilacak

Evaluasi: Cukup baik. FAQ yang ditemukan relevan dengan masalah pengiriman. Pada pengujian awal, LLM belum memanfaatkan konteks secara tepat, tetapi jawaban membaik setelah prompt diperbaiki.

No. 4

Query: Apakah saya bisa membayar belanjaan secara angsuran?

FAQ yang Ditemukan: ID 20 — Pembayaran dengan cicilan

Evaluasi: Baik. Sistem mengenali bahwa “angsuran” memiliki makna yang serupa dengan “cicilan”.

No. 5

Query: Apakah toko menyediakan layanan pemasangan produk di rumah?

FAQ yang Ditemukan: ID 45 — Custom produk; ID 11 — Pengiriman same-day; ID 5 — Perubahan alamat pengiriman

Evaluasi: Kurang relevan. FAQ yang ditemukan tidak menjawab pertanyaan tentang pemasangan produk di rumah. LLM menyatakan informasi belum tersedia dan menyarankan menghubungi customer service.

Testing Conclusion

Dari lima query yang diuji:

Empat query memiliki FAQ yang relevan dalam hasil retrieval.

Satu query, yaitu pertanyaan tentang layanan pemasangan produk di rumah, belum mendapatkan FAQ yang relevan.

Sistem dapat menangani variasi kata seperti “order” dan “pesanan”, serta “angsuran” dan “cicilan”.

Perbaikan prompt membantu LLM memanfaatkan konteks retrieval secara lebih tepat.

Pada pertanyaan yang tidak didukung knowledge base, LLM dapat memberikan respons yang lebih aman dengan menyatakan keterbatasan informasi.

Hasil tersebut merupakan evaluasi manual terhadap lima query uji, bukan pengukuran akurasi keseluruhan sistem. Oleh karena itu, hasil ini belum cukup untuk menyimpulkan performa sistem pada seluruh kemungkinan pertanyaan pengguna.

## 6.b. Hal Penting dari Pengujian Relevansi Hasil Retrieval dan Response AI

Ada tiga hal penting dari pengujian ini.
- Semantic Search dapat memahami parafrasa. Contohnya, angsuran dapat mengarah ke FAQ tentang cicilan.
- LLM dapat menolak menjawab ketika informasi dianggap tidak tersedia. Ini terlihat pada query nomor 3 dan 5, meskipun kualitas penolakannya perlu diuji lebih lanjut.
- Semantic Search selalu mengembalikan hasil teratas jika diminta mencari top_k=3. Artinya, keberadaan hasil retrieval tidak otomatis berarti FAQ tersebut relevan. Karena itu, pertanyaan di luar cakupan FAQ perlu diuji lebih lanjut.

## 7. Kesimpulan Hasil Pengujian 

Kesimpulan perbaikan query pada aplikasi Semantic Search & LLM yang dikembangkan adalah bahwa perbaikan tidak hanya dilakukan pada query pengguna, tetapi juga pada cara sistem mengambil FAQ yang relevan dan cara LLM memanfaatkan konteks tersebut untuk menghasilkan jawaban.
Kesimpulan evaluasi perbaikan query
1. Semantic search mampu memahami variasi kata dan parafrasa. Contohnya, kata “order” dapat dipahami sebagai “pesanan”, dan “angsuran” memiliki makna yang berkaitan dengan “cicilan”. FAQ yang sesuai berhasil ditemukan pada peringkat pertama untuk kedua query tersebut.
2. Query yang terlalu umum masih dapat menemukan beberapa FAQ terkait. Pada query “Kenapa paket saya belum sampai?”, sistem menemukan FAQ mengenai keterlambatan paket, status pengiriman, dan nomor resi. Namun, jawaban yang tepat tetap bergantung pada kemampuan LLM memilih dan menggunakan informasi yang sesuai.
3. Perbaikan prompt meningkatkan relevansi jawaban LLM. Pada pengujian awal, LLM belum memanfaatkan konteks FAQ mengenai keterlambatan paket secara tepat. Setelah prompt diperbaiki, LLM dapat memberikan jawaban yang sesuai dengan FAQ, termasuk arahan menghubungi customer service jika keterlambatan melebihi tiga hari dari estimasi.
4. Sistem perlu menjaga batasan knowledge base. Untuk query mengenai layanan pemasangan produk di rumah, tidak tersedia FAQ yang secara khusus membahas layanan tersebut. LLM sudah merespons dengan menyatakan informasi belum tersedia dan menyarankan pengguna menghubungi customer service. Namun, hasil retrieval masih perlu ditingkatkan karena FAQ yang ditemukan kurang relevan.

Ringkasan hasil pengujian
Aspek Evaluasi || Kesimpulan
Pemahaman variasi query || Baik untuk variasi kata dan parafrasa yang diuji.
Relevansi hasil retrieval || 4 dari 5 query menemukan FAQ relevan pada peringkat pertama.
Kesesuaian jawaban LLM || Meningkat setelah prompt diperbaiki pada kasus paket belum sampai.
Pencegahan halusinasi || LLM dapat menyatakan informasi tidak tersedia ketika FAQ yang sesuai tidak ditemukan.
Area perbaikan || Meningkatkan relevansi retrieval untuk query di luar cakupan knowledge base.

Kesimpulan akhir: Perbaikan prompt membantu LLM menghasilkan jawaban yang lebih sesuai dengan konteks FAQ, sedangkan semantic search sudah cukup baik dalam mengenali variasi bahasa pada sebagian besar query yang diuji. Pengembangan selanjutnya dapat difokuskan pada peningkatan relevansi retrieval, misalnya dengan menguji variasi query, memperluas knowledge base, dan menetapkan ambang relevansi agar sistem tidak menggunakan FAQ yang tidak berkaitan.
Catatan: hasil 4 dari 5 query merupakan evaluasi manual pada sampel kecil, bukan ukuran akurasi keseluruhan sistem.

## 8. Limitations and Improvement Opportunities

8.1. Knowledge Base Coverage

Knowledge base hanya terdiri dari 59 FAQ. Pertanyaan tentang layanan yang belum tercakup, seperti pemasangan produk di rumah, tidak dapat dijawab secara spesifik berdasarkan data yang tersedia.

Improvement: Tambahkan FAQ yang mencakup kebutuhan pengguna yang belum tersedia, terutama pertanyaan yang sering diajukan kepada customer service.

8.2. Retrieval Relevance

FAISS mengambil FAQ berdasarkan kedekatan vektor. Hasil terdekat belum tentu relevan secara substantif dengan kebutuhan pengguna.

Pada query tentang pemasangan produk, tiga hasil teratas membahas topik lain.

Improvement: Evaluasi beberapa pilihan model embedding, tinjau kualitas teks yang di-embed, dan pertimbangkan threshold jarak atau mekanisme reranking. Threshold perlu ditentukan melalui eksperimen, bukan ditetapkan secara sembarang.

8.3. Prompt Sensitivity

Kualitas jawaban LLM dipengaruhi oleh cara konteks dan instruksi disampaikan. Pada query tentang paket yang belum sampai, prompt awal belum menghasilkan jawaban yang memanfaatkan konteks secara tepat.

Improvement: Perjelas instruksi agar model memeriksa seluruh konteks FAQ sebelum menyatakan informasi tidak tersedia.

8.4. Limited Evaluation Samples

Pengujian baru mencakup lima query. Hasil tersebut belum menggambarkan performa pada seluruh kategori FAQ atau berbagai variasi bahasa pengguna.

Improvement: Buat kumpulan query uji yang lebih besar, sertakan parafrasa dan pertanyaan di luar cakupan knowledge base, kemudian nilai relevansi retrieval dan kualitas jawaban secara terpisah.

8.5. Distance Is Not Confidence

L2 distance merupakan ukuran jarak vektor, bukan probabilitas bahwa jawaban benar. Nilai jarak tidak boleh langsung ditafsirkan sebagai persentase keyakinan model.

Improvement: Tentukan aturan penerimaan atau penolakan hasil retrieval berdasarkan pengujian empiris terhadap query yang relevan dan tidak relevan.

8.6. API Availability

Eksperimen mengalami kendala ketika mencoba beberapa model Gemini, termasuk respons 404 untuk model yang tidak tersedia dan 503 yang menunjukkan layanan sementara tidak tersedia. Model gemini-3.5-flash-lite berhasil digunakan pada eksperimen.

Improvement: Dokumentasikan model yang digunakan, tangani error API, dan pertimbangkan mekanisme retry yang terbatas untuk gangguan sementara.

## 9. Cara Menjalankan Notebook/Script
**9.a. Running Script**

Pada terminal VSCode, jalankan: 

python src\semantic_search.py
python src\semantic_search.py --test

**9.b. Cara Manual**

Prerequisites

Python dan virtual environment.

Library yang digunakan pada notebook, termasuk Pandas, NumPy, FAISS, dan library Gemini yang sesuai dengan kode.

Gemini API key yang valid.

Step 1 — Open the Project

Buka folder project di VS Code:

semantic-search-assignment

Pastikan struktur file mencakup:

semantic-search-assignment/
├── data/
│   └── ecommerce_faq_knowledge_base.csv
├── notebook/
│   └── starter_notebook_semantic_search.ipynb
└── .venv/

Step 2 — Activate the Virtual Environment

Pada terminal PowerShell di folder project, jalankan:

.\.venv\Scripts\Activate.ps1

Step 3 — Install Dependencies

Jika project menyediakan requirements.txt, jalankan:

python -m pip install -r requirements.txt

Jika belum ada, pastikan semua library yang diimpor pada notebook sudah terpasang. Gunakan nama paket dan versi yang sesuai dengan lingkungan eksperimen.

Step 4 — Configure the API Key

Atur API key Gemini pada terminal PowerShell:

$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

Ganti YOUR_GEMINI_API_KEY dengan API key milik sendiri. Jangan menyimpan API key langsung di notebook atau mengunggahnya ke GitHub.

Step 5 — Run the Notebook

Buka file:

notebook/starter_notebook_semantic_search.ipynb

Pilih kernel Python dari virtual environment .venv, lalu jalankan seluruh cell secara berurutan.

Jika notebook dijalankan dengan working directory berupa folder utama project, gunakan path dataset:

data_path = "data/ecommerce_faq_knowledge_base.csv"

Jika working directory berada di dalam folder notebook, gunakan:

data_path = "../data/ecommerce_faq_knowledge_base.csv"

Pastikan path yang digunakan sesuai dengan working directory aktual.

Step 6 — Test the Application

Masukkan query pengguna dan periksa:

FAQ yang ditemukan oleh semantic search.

Urutan hasil retrieval dan L2 distance.

Relevansi FAQ terhadap pertanyaan.

Jawaban akhir yang dihasilkan LLM.

Apakah model menyatakan keterbatasan informasi ketika tidak ada FAQ yang relevan.

6. Final Conclusion

Project ini menunjukkan implementasi dasar aplikasi tanya jawab berbasis Semantic Search dan LLM dengan menggunakan Gemini Embedding API, FAISS, dan Gemini LLM.

Eksperimen memperlihatkan bahwa semantic search dapat menemukan FAQ yang relevan meskipun pengguna memakai istilah yang berbeda dari pertanyaan pada knowledge base. Integrasi LLM kemudian membantu mengubah konteks FAQ menjadi jawaban yang lebih natural.

Namun, kualitas sistem tetap bergantung pada cakupan knowledge base, relevansi hasil retrieval, dan desain prompt. Evaluasi yang lebih luas serta penanganan query yang tidak relevan diperlukan sebelum sistem digunakan pada lingkungan produksi.
