import psycopg2
from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime, date
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from PIL import Image, ImageTk

def veritabani_baglan():
    return psycopg2.connect(
        dbname="diyabet_sistemi",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )

def diyet_egzersiz_onerisi(seviye, belirtiler):
    """
    Parametreler
    ------------
    seviye      : int veya float | mg/dL kan şekeri
    belirtiler  : iterable[str] | Ör. ["Polifaji", "Yorgunluk"]

    Dönen
    -----
    (diyet, egzersiz) ikilisi – PDF tablosuna göre
    """
    s = float(seviye)
    bel = [b.lower() for b in belirtiler]        

    if s < 70 and any(b in bel for b in ["nöropati", "polifaji", "yorgunluk"]):
        return "Dengeli Beslenme", "Yok"

    if 70 <= s <= 110:
        if any(b in bel for b in ["yorgunluk", "kilo kaybı"]):
            return "Az Şekerli Diyet", "Yürüyüş"
        if any(b in bel for b in ["polifaji", "polidipsi"]):
            return "Dengeli Beslenme", "Yürüyüş"

    if 110 < s <= 180:
        if any(b in bel for b in ["bulanık görme", "nöropati"]):
            return "Az Şekerli Diyet", "Klinik Egzersiz"
        if any(b in bel for b in ["poliüri", "polidipsi"]):
            return "Şekersiz Diyet", "Klinik Egzersiz"
        if any(b in bel for b in ["yorgunluk", "nöropati", "bulanık görme"]):
            return "Az Şekerli Diyet", "Yürüyüş"

    if s >= 180:
        if any(b in bel for b in ["yaraların yavaş iyileşmesi",
                                  "polifaji", "polidipsi"]):
            return "Şekersiz Diyet", "Klinik Egzersiz"
        if any(b in bel for b in ["yaraların yavaş iyileşmesi", "kilo kaybı"]):
            return "Şekersiz Diyet", "Yürüyüş"

    return "Diyet Belirsiz", "Egzersiz Belirsiz"

def hasta_paneli_olustur(hasta_id):
    global sonuc_text, grafik_frame

    def olcum_ekle():
        try:
            seviye = int(entry_seviye.get())                
            zaman  = entry_zaman.get()                       
            tur    = combo_tur.get()                          

            with veritabani_baglan() as conn:
                with conn.cursor() as cur:

                    cur.execute("""
                        INSERT INTO olcum (hasta_id, olcum_zamani, seviye, olcum_turu)
                        VALUES (%s, %s, %s, %s)
                    """, (hasta_id, zaman, seviye, tur))

                    cur.execute("SELECT seker_uyari_kontrol(%s, %s)",
                                (hasta_id, date.today()))
                    sistem_uyari = cur.fetchone()[0]

                    cur.execute("""
                        SELECT b.ad
                        FROM   hasta_belirti hb
                        JOIN   belirti b ON b.belirti_id = hb.belirti_id
                        WHERE  hb.hasta_id = %s
                          AND  DATE(hb.tarih) = %s
                    """, (hasta_id, date.today()))
                    belirtiler = [r[0] for r in cur.fetchall()]

                    diyet, egzersiz = diyet_egzersiz_onerisi(seviye, belirtiler)
                    cur.execute("""
                        INSERT INTO uyari (hasta_id, tarih, seviye, mesaj)
                        VALUES (%s, NOW(), %s, %s)
                    """, (hasta_id, 'Otomatik',
                          f"📌 Diyet: {diyet}, Egzersiz: {egzersiz}"))

                    cur.execute("SELECT onerileri_uret(%s, %s)", (hasta_id, date.today()))  
                    cur.execute("SELECT insulin_oner(%s, %s)",
                                (hasta_id, date.today()))
                    insulin_mesaj = cur.fetchone()[0]

            messagebox.showinfo("Sistem Uyarısı",  sistem_uyari)
            messagebox.showinfo("İnsülin Önerisi", insulin_mesaj)
            messagebox.showinfo("Başarılı",       "Ölçüm ve öneriler kaydedildi.")

        except Exception as e:
            messagebox.showerror("Hata", str(e))




    def egzersiz_bildir():
        try:
            with veritabani_baglan() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO hasta_egzersiz (hasta_id, tarih, yapildi) "
                        "VALUES (%s, %s, TRUE)",
                        (hasta_id, date.today())
                    )
            messagebox.showinfo("Bildirim", "Egzersiz bildirildi.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def diyet_bildir():
        try:
            with veritabani_baglan() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO hasta_diyet (hasta_id, tarih, uygulandi) "
                        "VALUES (%s, %s, TRUE)",
                        (hasta_id, date.today())
                    )
            messagebox.showinfo("Bildirim", "Diyet bildirildi.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def durumu_goster():
        try:
            bugun = datetime.now().strftime("%Y-%m-%d")

            with veritabani_baglan() as conn:
                with conn.cursor() as cur:
                    
                    cur.execute("SELECT ortalama_seker(%s, %s)",
                                (hasta_id, bugun))
                    ort = cur.fetchone()[0]

                    cur.execute("""
                        SELECT COUNT(*) FROM olcum
                        WHERE  hasta_id = %s
                          AND  DATE(olcum_zamani) = %s
                          AND  olcum_turu IN ('sabah','oglen','ikindi','aksam','gece')
                    """, (hasta_id, bugun))
                    gecerli = cur.fetchone()[0]

        
                    cur.execute("""
                        SELECT COUNT(*) FROM olcum
                        WHERE  hasta_id = %s
                          AND  DATE(olcum_zamani) = %s
                          AND  olcum_turu NOT IN ('sabah','oglen','ikindi','aksam','gece')
                    """, (hasta_id, bugun))
                    disi = cur.fetchone()[0]

            
                    cur.execute("""
                        SELECT tarih, seviye, mesaj
                        FROM   uyari
                        WHERE  hasta_id = %s
                          AND  DATE(tarih) = %s
                        ORDER  BY tarih
                    """, (hasta_id, bugun))
                    gunluk_uyarilar = cur.fetchall()

    
                    cur.execute("""
                        SELECT mesaj
                        FROM   insulin_log
                        WHERE  hasta_id = %s AND tarih = %s
                        ORDER  BY id DESC LIMIT 1
                    """, (hasta_id, bugun))
                    ins_msg = cur.fetchone()

            sonuc_text.delete(1.0, END)
            sonuc_text.insert(END, f"🩸 Ortalama Şeker: {ort} mg/dL\n")

            if disi:
                sonuc_text.insert(END, f"⚠️ {disi} ölçüm saat dışı! "
                                        "Ortalamaya dahil edilmedi.\n")
            if gecerli <= 3:
                sonuc_text.insert(END, "⚠️ Yetersiz veri! "
                                        "Ortalama güvenilir değildir.\n")
            elif gecerli < 5:
                sonuc_text.insert(END, "⚠️ Ölçüm eksik! "
                                        "Eksik değerler ortalamaya katılmadı.\n")

  
            sonuc_text.insert(END, "\n🔔 Uyarılar:\n")
            if gunluk_uyarilar:
                for u in gunluk_uyarilar:
                    sonuc_text.insert(END, f"📅 {u[0]} | {u[1]} | {u[2]}\n")
            else:
                sonuc_text.insert(END, "• Bugün için uyarı yok.\n")

  
            sonuc_text.insert(END, "\n💉 İnsülin Önerisi:\n")
            if ins_msg:
                sonuc_text.insert(END, ins_msg[0] + "\n")
            else:
                sonuc_text.insert(END, "• Henüz insülin önerisi üretilmedi.\n")

        except Exception as e:
            messagebox.showerror("Hata", str(e))


    def grafik_goster(hasta_id):
        try:
            tarih = datetime.now().strftime("%Y-%m-%d")
            with veritabani_baglan() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT olcum_turu, seviye
                        FROM   olcum
                        WHERE  hasta_id = %s AND DATE(olcum_zamani) = %s
                        """, (hasta_id, tarih)
                    )
                    veriler = cur.fetchall()

            tur_sira = {"sabah": 0, "oglen": 1, "ikindi": 2, "aksam": 3, "gece": 4}
            veriler.sort(key=lambda x: tur_sira.get(x[0], 5))

            x = [v[0].capitalize() for v in veriler]
            y = [v[1] for v in veriler]

            for w in grafik_frame.winfo_children():
                w.destroy()

            if not x:
                Label(grafik_frame, text="Bugün için ölçüm yok.",
                      bg="white").pack()
                return

            fig = plt.Figure(figsize=(6, 4), dpi=100)
            ax = fig.add_subplot(111)
            ax.plot(x, y, marker="o", color="purple")
            ax.axhline(70, color="red", ls="--")
            ax.axhline(200, color="red", ls="--")
            ax.set(title="Günlük Kan Şekeri", ylabel="mg/dL")
            FigureCanvasTkAgg(fig, grafik_frame).get_tk_widget().pack()
        except Exception as e:
            messagebox.showerror("Hata", str(e))


    pencere = Tk()
    pencere.title("Hasta Paneli")
    try:
        with veritabani_baglan() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT isim, email, dogum_tarihi, profil_resim FROM hasta WHERE hasta_id = %s", (hasta_id,))
                isim, email, dogum, resim = cur.fetchone()
        if resim:
            with open("hasta_temp.jpg", "wb") as f:
                f.write(resim)
            img = Image.open("hasta_temp.jpg").resize((120, 120))
        else:
            img = Image.new("RGB", (120, 120), "gray")
    except:
        isim = email = dogum = "-"
        img = Image.new("RGB", (120, 120), "gray")

    img_tk = ImageTk.PhotoImage(img)
    profil_frame = Frame(pencere, bg="#f5f5f5")
    profil_frame.pack(pady=5)
    
    Label(profil_frame, image=img_tk, bg="#f5f5f5").pack()
    Label(profil_frame, text=isim, font=("Segoe UI", 12, "bold"),
          bg="#f5f5f5").pack()
    Label(profil_frame, text=email, bg="#f5f5f5").pack()
    Label(profil_frame, text=f"Doğum: {dogum}", bg="#f5f5f5").pack()

    pencere.geometry("1000x800")
    pencere.configure(bg="#f5f5f5")

    Label(pencere, text="👤 Hasta Paneli",
          font=("Segoe UI", 18, "bold"), bg="#f5f5f5").pack(pady=10)

    frame = Frame(pencere, bg="white", bd=2, relief=GROOVE)
    frame.pack(pady=10, padx=20, fill=X)

    Label(frame, text="Ölçüm Zamanı (YYYY-AA-GG SS:DD:SS):",
          bg="white").grid(row=0, column=0, sticky=W, padx=5, pady=5)
    entry_zaman = Entry(frame, width=30)
    entry_zaman.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    entry_zaman.grid(row=0, column=1)

    Label(frame, text="Şeker Seviyesi (mg/dL):",
          bg="white").grid(row=1, column=0, sticky=W, padx=5, pady=5)
    entry_seviye = Entry(frame)
    entry_seviye.grid(row=1, column=1)

    Label(frame, text="Ölçüm Türü:", bg="white").grid(row=2, column=0,
                                                       sticky=W, padx=5, pady=5)
    combo_tur = ttk.Combobox(frame, values=["sabah", "oglen", "ikindi", "aksam", "gece"])
    combo_tur.grid(row=2, column=1)

    Button(frame, text="📥 Ölçüm Ekle", command=olcum_ekle,
           bg="#4CAF50", fg="white").grid(row=3, columnspan=2, pady=10)

   
    Label(pencere, text="🧘 Günlük Egzersiz & Diyet Bildirimi",
          font=("Segoe UI", 14, "bold"), bg="#f5f5f5").pack()
    bildir_frame = Frame(pencere, bg="white", bd=2, relief=GROOVE)
    bildir_frame.pack(pady=10, padx=20, fill=X)

    Button(bildir_frame, text="✅ Egzersiz Yapıldı", command=egzersiz_bildir,
           bg="#1e88e5", fg="white").pack(pady=5)
    Button(bildir_frame, text="🥗 Diyet Uygulandı", command=diyet_bildir,
           bg="#43a047", fg="white").pack(pady=5)

   
    Label(pencere, text="📊 Günlük Özet",
          font=("Segoe UI", 14, "bold"), bg="#f5f5f5").pack()
    sonuc_text = Text(pencere, height=10, width=90)
    sonuc_text.pack(pady=10)

    Button(pencere, text="📈 Durumu Göster", command=durumu_goster,
           bg="#fb8c00", fg="white").pack(pady=10)

    
    Label(pencere, text="📉 Grafiksel Görünüm",
          font=("Segoe UI", 14, "bold"), bg="#f5f5f5").pack(pady=(10, 0))
    Button(pencere, text="📊 Grafik Göster",
           command=lambda: grafik_goster(hasta_id),
           bg="#673ab7", fg="white").pack(pady=5)

    grafik_frame = Frame(pencere, bg="white", bd=2, relief=GROOVE)
    grafik_frame.pack(padx=20, pady=10, fill=BOTH, expand=True)

    pencere.mainloop()
