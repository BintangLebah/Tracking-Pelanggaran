# Uraian Pekerjaan

Bagian ini merangkum tujuan utama pekerjaan: menata ulang form tambah dan edit siswa agar input penting (jenis kelamin, tanggal lahir, foto, dan pemilihan kelas) terkirim dengan benar ke server. Perubahan meliputi pemindahan elemen input ke dalam tag form yang sesuai, penambahan select kelas yang mengambil opsi dari `kelas_options`, serta penempatan input file foto agar dapat diproses saat submit.

Langkah berikutnya adalah memastikan logika server-side menangani validasi dan penyimpanan data tersebut dengan aman. Ini mencakup validasi bahwa field `kelas` wajib diisi, validasi format tanggal, serta penanganan file foto (penyimpanan path dan mekanisme penggantian foto lama). Handler edit juga disesuaikan agar memperbarui atribut siswa dengan benar.

Selain itu, perlu memastikan alur UI tetap intuitif: setelah menyimpan perubahan pada siswa yang terkait kelas tertentu, pengguna diarahkan kembali ke halaman daftar/halaman detail kelas tersebut. Juga akan ditambahkan umpan balik berupa pesan sukses atau penjelasan error agar pengguna mengetahui hasil aksi mereka.

Terakhir, dokumentasi singkat dan langkah pengujian disediakan agar tim QA dan pengembang lain dapat memverifikasi perubahan dengan cepat. Ini termasuk skenario edit, tambah, dan validasi error yang umum terjadi.

# Progress

Perubahan form telah diterapkan: elemen radio untuk jenis kelamin dan input file foto sudah dipindahkan ke dalam form, dan select untuk memilih kelas telah ditambahkan tepat di bawah field tanggal lahir. Template sekarang menerima `kelas_options` sehingga opsi kelas ditampilkan dinamis berdasarkan data dari database.

Di sisi server, handler tambah dan edit siswa telah diperbarui untuk menyimpan jenis kelamin, tanggal lahir, organisasi, dan foto. Validasi server-side ditambahkan untuk memastikan `kelas` wajib diisi; jika validasi gagal, template kembali menampilkan pesan error yang relevan.

UX flow diperbaiki: setelah menyimpan data siswa yang terkait dengan sebuah kelas, sistem mengarahkan pengguna kembali ke halaman daftar siswa yang memfilter berdasarkan kelas tersebut (atau ke halaman detail kelas bila diperlukan). Ini memudahkan verifikasi perubahan pada konteks yang benar.

Pengujian awal dilakukan secara manual dengan beberapa skenario dasar (edit siswa—ubah gender, upload foto, ubah tanggal lahir; tambah siswa tanpa kelas). Hasil menunjukkan form mengirimkan data yang benar dan handler merespon sesuai harapan; catatan kecil pada edge-case akan didokumentasikan dan diperbaiki jika diperlukan.
