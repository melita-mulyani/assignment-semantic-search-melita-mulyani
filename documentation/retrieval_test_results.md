## Output Section 5 - Mengimplementasikan Semantic Search
{'rank': 1, 'question': 'Bagaimana jika paket saya belum sampai melebihi estimasi?', 'answer': 'Jika paket melebihi estimasi pengiriman lebih dari 3 hari, silakan hubungi customer service dengan menyertakan nomor resi untuk ditelusuri lebih lanjut.', 'category': 'Pengiriman', 'distance': np.float32(0.33353508)}
{'rank': 2, 'question': 'Kenapa status pengiriman saya tidak berubah selama beberapa hari?', 'answer': 'Status yang tidak berubah bisa disebabkan keterlambatan update sistem kurir. Disarankan menunggu 1x24 jam sebelum melaporkan ke customer service.', 'category': 'Pengiriman', 'distance': np.float32(0.4088098)}
{'rank': 3, 'question': 'Kenapa nomor resi saya belum bisa dilacak di website kurir?', 'answer': "Nomor resi baru dapat dilacak setelah paket diserahterimakan ke pihak kurir, biasanya butuh waktu beberapa jam setelah status 'Dikirim'.", 'category': 'Pengiriman', 'distance': np.float32(0.4320181)}

## Output Section 6 - Mendesain Prompt dan Context 

Persona:
Kamu adalah asisten customer service e-commerce
yang ramah, jelas, dan membantu.

Task:
Jawab pertanyaan pengguna hanya berdasarkan konteks FAQ.
Jangan menambahkan fakta atau kebijakan yang tidak tersedia
dalam konteks.

Aturan menjawab:
1. Jika ada FAQ yang relevan, gunakan informasi tersebut
   untuk menjawab pertanyaan.
2. Jika jawaban memiliki kondisi tertentu, jelaskan kondisi
   tersebut dengan jelas.
3. Jika konteks hanya menjawab sebagian pertanyaan,
   sampaikan informasi yang tersedia dan jelaskan batasannya.
4. Jangan langsung mengatakan informasi tidak tersedia
   hanya karena pertanyaan menggunakan kata-kata berbeda
   dari FAQ.
5. Jika tidak ada FAQ yang relevan, katakan bahwa informasi
   belum tersedia dan sarankan menghubungi customer service.

Context:
FAQ: Bagaimana jika paket saya belum sampai melebihi estimasi?
...
Format:
Berikan jawaban dalam bahasa Indonesia yang ringkas,
ramah, dan mudah dipahami.

Output is truncated. View as a scrollable element or open in a text editor. Adjust cell output settings...

## Output Section 7 - Mengintegrasikan LLM 
Model yang digunakan: gemini-3.5-flash-lite 

Jawaban LLM:
Halo! Tentu, Anda bisa membayar dengan cicilan. Fitur ini tersedia untuk transaksi dengan kartu kredit tertentu pada nominal minimal yang ditentukan oleh pihak bank ya. Ada hal lain yang bisa saya bantu?

Sumber FAQ yang digunakan:
- Apakah saya bisa membayar dengan cicilan?
- Apakah bisa membayar menggunakan lebih dari satu metode sekaligus?
- Metode pembayaran apa saja yang tersedia?

## Output Section 8 - Menguji Relevansi Hasil Retrieval dan Response AI 

# 1. Jawaban jelas tersedia di FAQ
Query: Bagaimana cara melakukan pemesanan di platform ini?
Jawaban: Halo! Tentu, saya akan bantu jelaskan ya. 

Untuk melakukan pemesanan, caranya sangat mudah:
1. Pilih produk yang Anda inginkan.
2. Klik tombol 'Tambah ke Keranjang'.
3. Lanjutkan ke halaman checkout untuk mengisi alamat pengiriman dan memilih metode pembayaran.

*Catatan: Saat ini pemesanan hanya dapat dilakukan setelah Anda membuat akun ya, agar Anda bisa melacak status pesanan dengan mudah.*

Ada lagi yang bisa saya bantu?
Sumber teratas: Bagaimana cara melakukan pemesanan di platform ini?

---

# 2. Jawaban jelas tersedia, tetapi kalimatnya berbeda
Query: Bisakah saya membatalkan order yang sudah saya buat?
Jawaban: Halo! Tentu, Anda bisa membatalkan pesanan yang sudah dibuat melalui halaman 'Pesanan Saya' selama statusnya masih 'Diproses'. Namun, perlu diingat bahwa pembatalan tidak dapat dilakukan jika status pesanan sudah berubah menjadi 'Dikirim'. 

Ada lagi yang bisa saya bantu?
Sumber teratas: Bagaimana cara membatalkan pesanan yang sudah dibuat?

---

# 3. Parafrasa: masalah keterlambatan pengiriman
Query: Kenapa paket saya belum sampai?
Jawaban: Halo! 😊 

Untuk pertanyaan mengapa paket belum sampai, dalam konteks kami terdapat informasi mengenai paket yang belum sampai melebihi estimasi, yaitu:

Jika paket Anda melebihi estimasi pengiriman lebih dari 3 hari, silakan hubungi customer service kami dengan menyertakan nomor resi agar dapat ditelusuri lebih lanjut ya. 
...

---

# 4. Parafrasa: masalah pembayaran cicilan
Query: Apakah saya bisa membayar belanjaan secara angsuran?
Jawaban LLM:
Halo! Tentu, Anda bisa membayar belanjaan secara angsuran (cicilan). 

Fitur cicilan ini tersedia untuk transaksi dengan kartu kredit tertentu, ya, dengan nominal minimal yang telah ditentukan oleh pihak bank. 

Ada lagi yang bisa saya bantu hari ini?

Sumber FAQ yang digunakan:
- Apakah saya bisa membayar dengan cicilan?
- Apakah bisa membayar menggunakan lebih dari satu metode sekaligus?
- Bagaimana cara melakukan pemesanan di platform ini?

---

# 5. Pertanyaan yang kemungkinan tidak tercakup dalam FAQ
Query: Apakah toko menyediakan layanan pemasangan produk di rumah?
Jawaban: Mohon maaf, saat ini informasi mengenai layanan pemasangan produk di rumah belum tersedia dalam sistem kami. Untuk info lebih lanjut, silakan menghubungi customer service kami ya. Ada hal lain yang bisa saya bantu?
Sumber teratas: Apakah saya bisa request custom produk kepada penjual?
---
Output is truncated. View as a scrollable element or open in a text editor. Adjust cell output settings...
