from tkinter import *
from tkinter import ttk, messagebox
from hasta_paneli import hasta_paneli_olustur
from doktor_paneli import doktor_paneli_olustur
import psycopg2
import hashlib

aktif_kullanici_rolu = None

def veritabani_baglan():
    return psycopg2.connect(
        dbname="diyabet_sistemi",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )

def giris_ekrani():
    pencere = Tk()
    pencere.title("Diyabet Takip Girişi")
    pencere.geometry("600x400")
    pencere.configure(bg="#1e1e1e")

    cerceve = Frame(pencere, bg="#2c2c2c", bd=2, relief=SOLID)
    cerceve.place(relx=0.5, rely=0.5, anchor=CENTER)

    Label(cerceve, text="Diyabet Takip Girişi", font=("Segoe UI", 16, "bold"), bg="#2c2c2c", fg="#ba68c8").pack(pady=20)

    Label(cerceve, text="TC Kimlik No:", bg="#2c2c2c", fg="white").pack()
    entry_tc = Entry(cerceve, bg="#3e3e3e", fg="white", insertbackground="white")
    entry_tc.pack(pady=5)

    Label(cerceve, text="Şifre:", bg="#2c2c2c", fg="white").pack()
    entry_sifre = Entry(cerceve, show="*", bg="#3e3e3e", fg="white", insertbackground="white")
    entry_sifre.pack(pady=5)

    Label(cerceve, text="Rol:", bg="#2c2c2c", fg="white").pack()
    rol_var = StringVar()
    rol_secim = OptionMenu(cerceve, rol_var, "doktor", "hasta")
    rol_secim.config(bg="#3e3e3e", fg="white", highlightthickness=0)
    rol_secim.pack(pady=5)
    rol_var.set("doktor")

    def giris_yap():
        global aktif_kullanici_rolu
        tc = entry_tc.get()
        sifre = entry_sifre.get()
        rol = rol_var.get()
        hashed_sifre = hashlib.sha256(sifre.encode()).hexdigest()

        try:
            conn = veritabani_baglan()
            cur = conn.cursor()

            if rol == "doktor":
                cur.execute("SELECT doktor_id FROM doktor WHERE tc_kimlik_no = %s AND sifre = %s", (tc, hashed_sifre))
                sonuc = cur.fetchone()
                if sonuc:
                    aktif_kullanici_rolu = "doktor"
                    pencere.destroy()
                    doktor_paneli_olustur(sonuc[0], aktif_kullanici_rolu)
                else:
                    messagebox.showerror("Hata", "Doktor bulunamadı veya şifre yanlış.")

            elif rol == "hasta":
                cur.execute("SELECT hasta_id FROM hasta WHERE tc_kimlik_no = %s AND sifre = %s", (tc, hashed_sifre))
                sonuc = cur.fetchone()
                if sonuc:
                    aktif_kullanici_rolu = "hasta"
                    pencere.destroy()
                    hasta_paneli_olustur(sonuc[0])
                else:
                    messagebox.showerror("Hata", "Hasta bulunamadı veya şifre yanlış.")

            conn.close()
        except Exception as e:
            messagebox.showerror("Bağlantı Hatası", str(e))

    Button(cerceve, text="Giriş Yap", command=giris_yap, bg="#4CAF50", fg="white", font=("Segoe UI", 11, "bold"), width=20).pack(pady=20)

    pencere.mainloop()

giris_ekrani()