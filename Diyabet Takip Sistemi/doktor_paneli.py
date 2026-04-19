from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from datetime import datetime
import psycopg2
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import io


def veritabani_baglan():
    return psycopg2.connect(
        dbname="diyabet_sistemi",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )


def doktor_paneli_olustur(doktor_id, rol):
    from hasta_ekle import hasta_ekle_ekrani, oneriler_ekrani

    def orta_paneli_temizle():
        for w in orta.winfo_children():
            w.destroy()

    def hastalari_getir():
        try:
            with veritabani_baglan() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT hasta_id, isim FROM hasta WHERE doktor_id = %s",
                        (doktor_id,)
                    )
                    return cur.fetchall()
        except:
            return []

    def uyarilari_getir(hasta_id):
        try:
            with veritabani_baglan() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT tarih, seviye, mesaj FROM uyari "
                        "WHERE hasta_id = %s ORDER BY tarih DESC",
                        (hasta_id,)
                    )
                    return cur.fetchall()
        except:
            return []

    def guncelle_hasta_listesi():
        hasta_listesi.delete(0, END)
        for h in hastalari_getir():
            hasta_listesi.insert(END, f"{h[0]} - {h[1]}")

    def hasta_secildi(_):
        try:
            secim = hasta_listesi.get(hasta_listesi.curselection())
            h_id, h_ad = secim.split(" - ", 1)
            secilen_hasta.update(id=int(h_id), isim=h_ad)
            uyari_listele()
        except:
            pass

    def uyari_listele():
        for i in uyari_list.get_children():
            uyari_list.delete(i)
        for u in uyarilari_getir(secilen_hasta["id"]):
            uyari_list.insert("", END, values=u)

    def hasta_ekle():
        orta_paneli_temizle()
        hasta_ekle_ekrani(orta, doktor_id, guncelle_hasta_listesi)

    def oneriler_ekle():
        if not secilen_hasta["id"]:
            messagebox.showwarning("Uyarı", "Lütfen bir hasta seçin!")
            return
        orta_paneli_temizle()
        oneriler_ekrani(orta, secilen_hasta["id"], secilen_hasta["isim"])

    def onerileri_goster():
        orta_paneli_temizle()

        Label(
            orta, text="📋 Öneriler", font=("Segoe UI", 16, "bold"),
            bg="#1e1e1e", fg="#ba68c8"
        ).pack(pady=10)

        frame = Frame(orta, bg="#1e1e1e")
        frame.pack(padx=10, pady=10, fill=BOTH, expand=True)

        scroll = Scrollbar(frame)
        scroll.pack(side=RIGHT, fill=Y)

        tree = ttk.Treeview(frame, yscrollcommand=scroll.set, selectmode="browse")
        scroll.config(command=tree.yview)

        tree["columns"] = ("Tarih", "Hasta", "Seviye", "Diyet", "Egzersiz", "Neden")
        tree.column("#0", width=0, stretch=NO)
        for c in tree["columns"]:
            tree.heading(c, text=c)
            tree.column(c, anchor=W, width=120)
        tree.pack(fill=BOTH, expand=True)

        try:
            with veritabani_baglan() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT o.tarih, h.isim, o.seker_seviyesi,
                               o.diyet, o.egzersiz, o.neden
                        FROM   oneriler o
                        JOIN   hasta h ON h.hasta_id = o.hasta_id
                        WHERE  h.doktor_id = %s
                        ORDER  BY o.tarih DESC
                        """,
                        (doktor_id,)
                    )
                    for row in cur.fetchall():
                        tree.insert("", END, values=row)
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
                        """,
                        (hasta_id, tarih)
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
                      bg="#2c2c2c", fg="white").pack()
                return

            fig = plt.Figure(figsize=(5.5, 3), dpi=100)
            ax = fig.add_subplot(111)
            ax.plot(x, y, marker="o", linestyle="-", color="magenta")
            ax.axhline(70, color="red", ls="--")
            ax.axhline(200, color="red", ls="--")
            ax.set(title="Günlük Şeker", ylabel="mg/dL", xlabel="Zaman")
            canvas = FigureCanvasTkAgg(fig, master=grafik_frame)
            canvas.draw()
            canvas.get_tk_widget().pack()
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    pencere = Tk()
    pencere.title("Doktor Paneli")
    pencere.geometry("1300x800")
    pencere.configure(bg="#1e1e1e")

    cerceve = Frame(pencere, bg="#1e1e1e")
    cerceve.pack(fill=BOTH, expand=True)

    sol   = Frame(cerceve, bg="#292929", width=250)
    orta  = Frame(cerceve, bg="#1e1e1e")
    sag   = Frame(cerceve, bg="#2c2c2c", width=450)

    sol.pack(side=LEFT, fill=Y)
    orta.pack(side=LEFT, fill=BOTH, expand=True)
    sag.pack(side=RIGHT, fill=Y)

    try:
        with veritabani_baglan() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT isim, email, dogum_tarihi, profil_resim "
                    "FROM doktor WHERE doktor_id = %s",
                    (doktor_id,)
                )
                isim, email, dogum, resim = cur.fetchone()
        if resim:
            img = Image.open(io.BytesIO(resim)).resize((120, 120))
        else:
            img = Image.new("RGB", (120, 120), "gray")
    except:
        isim = email = dogum = "-"
        img = Image.new("RGB", (120, 120), "gray")

    img_tk = ImageTk.PhotoImage(img)
    Label(sol, image=img_tk, bg="#292929").pack(pady=10)
    Label(sol, text=isim,  font=("Segoe UI", 12, "bold"),
          bg="#292929", fg="white").pack()
    Label(sol, text=email, bg="#292929", fg="white").pack()
    Label(sol, text=f"Doğum: {dogum}", bg="#292929", fg="white").pack(pady=(0, 15))

    if rol == "doktor":
        Button(sol, text="➕ Hasta Ekle", command=hasta_ekle,
               bg="#ba68c8", fg="white").pack(pady=5, fill=X)
        Button(sol, text="📋 Hastaları Listele", command=guncelle_hasta_listesi,
               bg="#ba68c8", fg="white").pack(pady=5, fill=X)
        Button(sol, text="💡 Öneri Ekle", command=oneriler_ekle,
               bg="#8e24aa", fg="white").pack(pady=5, fill=X)
        Button(sol, text="📄 Önerileri Göster", command=onerileri_goster,
               bg="#ab47bc", fg="white").pack(pady=5, fill=X)

    hasta_listesi = Listbox(sol, bg="white")
    hasta_listesi.pack(fill=BOTH, expand=True, padx=10, pady=10)
    hasta_listesi.bind("<<ListboxSelect>>", hasta_secildi)

    Button(sol, text="📊 Grafik Göster",
           command=lambda: grafik_goster(secilen_hasta["id"])
           if secilen_hasta["id"] else messagebox.showwarning(
               "Uyarı", "Hasta seçin!"),
           bg="#0097a7", fg="white").pack(pady=5, fill=X)

    Label(sag, text="📢 Uyarılar", font=("Segoe UI", 16, "bold"),
          bg="#2c2c2c", fg="#ba68c8").pack(pady=10)

    uyari_frame = Frame(sag, bg="#2c2c2c")
    uyari_frame.pack(padx=10, pady=5, fill=BOTH, expand=False)

    uy_scroll_y = Scrollbar(uyari_frame, orient=VERTICAL)
    uy_scroll_x = Scrollbar(uyari_frame, orient=HORIZONTAL)

    uyari_list = ttk.Treeview(
        uyari_frame,
        columns=("Tarih", "Seviye", "Mesaj"),
        show="headings",
        yscrollcommand=uy_scroll_y.set,
        xscrollcommand=uy_scroll_x.set
    )
    uy_scroll_y.config(command=uyari_list.yview)
    uy_scroll_x.config(command=uyari_list.xview)

    uy_scroll_y.pack(side=RIGHT, fill=Y)
    uy_scroll_x.pack(side=BOTTOM, fill=X)

    for col, w in zip(("Tarih", "Seviye", "Mesaj"), (100, 100, 300)):
        uyari_list.heading(col, text=col)
        uyari_list.column(col, width=w)

    uyari_list.pack(fill=BOTH, expand=True)

    grafik_frame = Frame(sag, bg="#2c2c2c")
    grafik_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    secilen_hasta = {"id": None, "isim": None}
    guncelle_hasta_listesi()

    pencere.mainloop()
