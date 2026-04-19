from tkinter import *
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk
import psycopg2
import hashlib
import smtplib
from email.mime.text import MIMEText
import os

def veritabani_baglan():
    return psycopg2.connect(
        dbname="diyabet_sistemi",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )

def hasta_bilgi_maili_gonder(email, tc, sifre):
    mesaj = MIMEText(f"""
    Sayın Kullanıcı,

    Doktorunuz sizi Diyabet Takip Sistemine kaydetti.
    Sisteme giriş bilgileriniz aşağıdadır:

    TC Kimlik No: {tc}
    Şifre: {sifre}

    Lütfen sisteme giriş yaptıktan sonra şifrenizi değiştiriniz.
    """)

    mesaj['Subject'] = 'Diyabet Takip Sistemi Giriş Bilgileri'
    mesaj['From'] = 'supergrls1111@gmail.com'
    mesaj['To'] = email

    try:
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.starttls()
        smtp.login('supergrls1111@gmail.com', 'fnsonvdcqrhjdegf')
        smtp.sendmail(mesaj['From'], mesaj['To'], mesaj.as_string())
        smtp.quit()
        print("Mail gönderildi.")
    except Exception as e:
        print("Mail gönderilemedi:", str(e))

def hasta_ekle_ekrani(orta, doktor_id, guncelle):
    for w in orta.winfo_children():
        w.destroy()

    Label(orta, text="🧾 Yeni Hasta Ekle", font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="#ba68c8").pack(pady=10)

    frame = Frame(orta, bg="#1e1e1e")
    frame.pack(pady=10)

    etiketler = ["İsim", "TC Kimlik No", "E-posta", "Şifre", "Doğum Tarihi (YYYY-AA-GG)", "Cinsiyet"]
    entryler = []

    for etiket in etiketler:
        Label(frame, text=etiket, bg="#1e1e1e", fg="white", font=("Segoe UI", 10)).pack(anchor=W, pady=(5, 0))
        ent = Entry(frame, width=40, font=("Segoe UI", 10), bg="#3e3e3e", fg="white", insertbackground="white", relief=FLAT)
        ent.pack(pady=2)
        entryler.append(ent)

    profil_resim_path = [None]
    foto_label = Label(frame, bg="#1e1e1e")
    foto_label.pack(pady=5)

    def foto_sec():
        yol = filedialog.askopenfilename(filetypes=[("Görsel", "*.jpg *.jpeg *.png")])
        if yol:
            img = Image.open(yol).resize((100, 100))
            foto = ImageTk.PhotoImage(img)
            foto_label.configure(image=foto)
            foto_label.image = foto
            profil_resim_path[0] = yol

    Button(frame, text="📂 Fotoğraf Seç", command=foto_sec, bg="#9c27b0", fg="white", font=("Segoe UI", 10), width=20).pack(pady=5)

    def kaydet():
        try:
            sifre = entryler[3].get()
            hashed_sifre = hashlib.sha256(sifre.encode()).hexdigest()

            conn = veritabani_baglan()
            cur = conn.cursor()

            with open(profil_resim_path[0], "rb") as f:
                resim = f.read()

            cur.execute("""
                INSERT INTO hasta (doktor_id, tc_kimlik_no, isim, email, sifre, dogum_tarihi, cinsiyet, profil_resim)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                doktor_id,
                entryler[1].get(),
                entryler[0].get(),
                entryler[2].get(),
                hashed_sifre,
                entryler[4].get(),
                entryler[5].get(),
                resim
            ))
            conn.commit()
            conn.close()

            hasta_bilgi_maili_gonder(entryler[2].get(), entryler[1].get(), entryler[3].get())

            messagebox.showinfo("Başarılı", "Yeni hasta başarıyla eklendi.")
            guncelle()
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    Button(orta, text="💾 Kaydet", command=kaydet, bg="#ba68c8", fg="white", width=20, font=("Segoe UI", 10, "bold"), relief=FLAT).pack(pady=10)

def oneriler_ekrani(orta, hasta_id, hasta_adi):
    for w in orta.winfo_children():
        w.destroy()

    Label(orta, text=f"💡 {hasta_adi} - Öneri Ekle", font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="#ba68c8").pack(pady=10)

    frame = Frame(orta, bg="#1e1e1e")
    frame.pack(pady=10)

    
    Label(frame, text="Egzersiz Önerisi", bg="#1e1e1e", fg="white", font=("Segoe UI", 10)).pack(anchor=W)
    egzersiz_combo = ttk.Combobox(frame, values=[
        "Yürüyüş", "Bisiklet", "Klinik Egzersiz"
    ])
    egzersiz_combo.pack(pady=2)

   
    Label(frame, text="Diyet Önerisi", bg="#1e1e1e", fg="white", font=("Segoe UI", 10)).pack(anchor=W)
    diyet_combo = ttk.Combobox(frame, values=[
        "Az Şekerli Diyet", "Şekersiz Diyet", "Dengeli Beslenme"
    ])
    diyet_combo.pack(pady=2)

 
    Label(frame, text="Beklenen Belirtiler", bg="#1e1e1e", fg="white", font=("Segoe UI", 10)).pack(anchor=W)
    belirtiler_listbox = Listbox(frame, selectmode=MULTIPLE, height=8, bg="#3e3e3e", fg="white", selectbackground="#ba68c8")
    belirti_secenekleri = [
        "Poliüri", "Polifaji", "Polidipsi", "Nöropati",
        "Kilo Kaybı", "Yorgunluk", "Yaraların Yavaş İyileşmesi", "Bulanık Görme"
    ]
    for b in belirti_secenekleri:
        belirtiler_listbox.insert(END, b)
    belirtiler_listbox.pack(pady=2)

    def kaydet():
        try:
            egzersiz = egzersiz_combo.get()
            diyet = diyet_combo.get()
            secilen_belirtiler = [belirtiler_listbox.get(i) for i in belirtiler_listbox.curselection()]

            if not egzersiz or not diyet or not secilen_belirtiler:
                messagebox.showwarning("Eksik Veri", "Lütfen tüm alanları doldurun.")
                return

            conn = veritabani_baglan()
            cur = conn.cursor()


            mesaj = f"Egzersiz: {egzersiz} | Diyet: {diyet}"
            cur.execute("""
                INSERT INTO uyari (hasta_id, tarih, seviye, mesaj)
                VALUES (%s, now(), %s, %s)
            """, (hasta_id, "Öneri", mesaj))

            for b in secilen_belirtiler:
                cur.execute("""
                    INSERT INTO hasta_belirti (hasta_id, belirti_id, tarih)
                    SELECT %s, belirti_id, now()
                    FROM belirti
                    WHERE LOWER(ad) = LOWER(%s)
                """, (hasta_id, b.strip()))

            conn.commit()
            conn.close()
            messagebox.showinfo("Başarılı", "Öneriler ve belirtiler kaydedildi.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    Button(orta, text="💾 Öneriyi Kaydet", command=kaydet, bg="#ba68c8", fg="white", width=20,
           font=("Segoe UI", 10, "bold"), relief=FLAT).pack(pady=10)
