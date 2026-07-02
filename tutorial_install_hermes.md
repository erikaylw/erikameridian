# Tutorial Install Hermes Agent di Laptop
### Panduan buat instalasi pertama — mudah, tinggal copy-paste

---

## 📋 Sebelum Mulai

**Yang dibutuhkan:**
- Laptop Windows/Mac/Linux
- Koneksi internet
- 10 menit waktu

---

## 🚀 Langkah 1: Buka Terminal

**Windows:**
- Tekan tombol `Windows` → ketik `CMD` → Enter
- Atau: tekan `Windows + R` → ketik `cmd` → Enter

**Mac:**
- Tekan `Command + Spasi` → ketik `Terminal` → Enter

**Linux:**
- Tekan `Ctrl + Alt + T`

---

## 🚀 Langkah 2: Install Hermes

Copy paste satu baris perintah ini ke terminal:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Tunggu beberapa saat sampai keluar tulisan "Installation complete" atau "Setup selesai".

---

## 🚀 Langkah 3: Set API Key

Setelah install selesai, daftar dulu ke OpenRouter (GRATIS):

1. Buka https://openrouter.ai/keys
2. Login pake Google/GitHub
3. Klik "Create Key"
4. Copy API Key-nya

Lalu di terminal, jalanin:

```bash
hermes auth add openrouter
```

Tempel API Key-nya, Enter.

---

## 🚀 Langkah 4: Cobain!

Jalanin perintah ini:

```bash
hermes
```

Nanti bakal muncul layar chat. Coba ketik:

```
Halo, siapa kamu?
```

Kalau dia jawab — BERHASIL! 🎉

Untuk keluar, tekan `Ctrl + C` atau ketik `/quit`.

---

## 🚀 Langkah 5: Coba Fitur Agent (yang beda dari ChatGPT)

Setelah chat terbuka, coba ketik perintah ini satu-satu:

```
Buat file teks nama saya, simpan di desktop
```

```
Coba baca file itu
```

```
Hitung 5+7*3 pakai python
```

Kalau semua jalan — selamat, lo lagi pake AGENT, bukan chatbot biasa! 🎯

---

## ❌ Kalau Error

| Error | Solusi |
|---|---|
| "command not found" | Restart terminal, atau buka terminal baru |
| "curl not found" | Windows: install Git Bash. Mac/Linux: built-in |
| "Permission denied" | Tambahin `sudo` di depan (mac/linux): `sudo curl -fsSL ...` |
| Lainnya | Screenshot errornya, tanya ke Erika |

---

## 📊 Perbandingan Cepat

| Fitur | ChatGPT (chatbot) | Hermes (agent) |
|---|---|---|
| Chat biasa | ✅ | ✅ |
| Buat file di laptop | ❌ | ✅ |
| Jalanin kode | ❌ | ✅ |
| Baca file PDF | ❌ | ✅ |
| Kirim ke Telegram | ❌ | ✅ |

---

## 💡 Tips

- Hermes bisa pake banyak model: DeepSeek (gratis/murah), Claude, GPT, Gemini
- Default pake deepseek — paling murah ($0.09/1M token)
- Mau pake model gratis? Ketik `/model` di chat, pilih yang ada tulisan "free"

---

**Selamat mencoba! 🚀**
