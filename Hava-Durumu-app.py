import customtkinter as ctk
import tkintermapview
import requests
from tkinter import messagebox
from PIL import Image, ImageTk
import time
import sys
import os
import ctypes

# --- AYARLAR ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# GITHUB UYARISI: Bu kodu GitHub'a yüklerken API Key'i silin.
API_KEY = "BURAYA_API_KEY_GELECEK"

# --- 1. ADIM: GÖREV ÇUBUĞU İKONU İÇİN KİMLİK AYARI ---
# Bu ayar pencere oluşturulmadan ÖNCE yapılmalıdır.
try:
    myappid = 'modern.havadurumu.app.v1.0' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

def resource_path(relative_path):
    """ .exe yapıldığında veya normal çalışırken dosya yolunu bulur """
    try:
        # PyInstaller geçici klasörü
        base_path = sys._MEIPASS
    except Exception:
        # Normal çalışma klasörü: Script dosyasının bulunduğu tam yol
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

class HavaDurumuApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Pencere Ayarları
        self.title("Modern Dünya Hava Durumu")
        self.geometry("1100x700")
        
        # --- 2. ADIM: PENCERE VE GÖREV ÇUBUĞU İKONU ---
        icon_path = resource_path("logo.png")
        print(f"İkon aranıyor: {icon_path}") # Konsola yolunu yazar, kontrol edin.

        try:
            # Pillow ile resmi aç
            img = Image.open(icon_path)
            # Tkinter formatına çevir
            self.icon_img = ImageTk.PhotoImage(img)
            
            # PENCERE İKONUNU AYARLA (Sol Üst ve Görev Çubuğu)
            # True: Tüm alt pencerelere de uygula
            self.wm_iconphoto(True, self.icon_img) 
            
            # Alternatif (Eğer yukarıdaki çalışmazsa .ico dosyası gerekebilir)
            # self.iconbitmap(resource_path("logo.ico")) 
        except Exception as e:
            print(f"⚠️ İKON HATASI: {e}")
            print("Lütfen 'logo.png' dosyasının script ile aynı klasörde olduğundan emin olun.")

        # Veri Saklama Listesi
        self.active_locations = []
        self.last_click_time = 0

        # Grid Sistemi
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SOL PANEL ---
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        # --- 3. ADIM: ARAYÜZ İÇİNDEKİ LOGO (Sol Paneldeki Resim) ---
        try:
            # Resmi yeniden boyutlandır (Daha net görünmesi için)
            img_data = Image.open(icon_path)
            self.logo_image = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(100, 100))
            
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="", image=self.logo_image)
            self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        except Exception as e:
            print(f"Logo yüklenemedi: {e}")
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Hava Takip", font=ctk.CTkFont(size=24, weight="bold"))
            self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Arama
        self.search_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Haritada Git (Örn: Paris)")
        self.search_entry.grid(row=1, column=0, padx=20, pady=10)
        
        self.search_btn = ctk.CTkButton(self.sidebar_frame, text="Haritayı Odakla", command=self.haritayi_odakla)
        self.search_btn.grid(row=2, column=0, padx=20, pady=10)

        # Bilgi Notu
        self.info_lbl = ctk.CTkLabel(self.sidebar_frame, text="Haritaya tıklayarak konum ekleyin.\n(Maksimum 3 Konum)", text_color="gray", font=("Arial", 12))
        self.info_lbl.grid(row=3, column=0, padx=10, pady=(10, 5))

        # Sonuç Alanı
        self.results_container = ctk.CTkScrollableFrame(self.sidebar_frame, label_text="Seçilen Konumlar", width=280)
        self.results_container.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        # --- HARİTA ---
        self.map_widget = tkintermapview.TkinterMapView(self, corner_radius=0)
        self.map_widget.grid(row=0, column=1, sticky="nsew")

        self.map_widget.set_position(39.92, 32.85) # Ankara
        self.map_widget.set_zoom(6)
        self.map_widget.add_left_click_map_command(self.haritaya_tiklandi)

    def haritayi_odakla(self):
        address = self.search_entry.get()
        if not address:
            return

        url = "https://nominatim.openstreetmap.org/search"
        headers = {'User-Agent': 'HavaDurumuApp/1.0', 'Referer': 'http://localhost'}
        params = {'q': address, 'format': 'json', 'limit': 1}
        
        try:
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200 and response.json():
                data = response.json()[0]
                self.map_widget.set_position(float(data["lat"]), float(data["lon"]))
                self.map_widget.set_zoom(10)
            else:
                messagebox.showerror("Hata", "Konum bulunamadı.")
        except Exception as e:
            print(f"Arama hatası: {e}")

    def haritaya_tiklandi(self, coords):
        current_time = time.time()
        if current_time - self.last_click_time < 2.5: 
            return
        self.last_click_time = current_time

        if len(self.active_locations) >= 3:
            messagebox.showwarning("Sınır Aşıldı", "En fazla 3 konum seçebilirsiniz.\nLütfen birini silin.")
            return

        self.hava_durumu_ekle(coords[0], coords[1])

    def il_ismini_bul(self, lat, lon):
        url = "https://nominatim.openstreetmap.org/reverse"
        headers = {'User-Agent': 'HavaDurumuApp/1.0', 'Referer': 'http://localhost'}
        params = {'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 10}
        
        try:
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                address = data.get("address", {})
                bulunan_yer = address.get("province") or address.get("city") or address.get("state")
                if bulunan_yer:
                    bulunan_yer = bulunan_yer.replace(" ili", "").replace(" Province", "").strip()
                return bulunan_yer
        except Exception as e:
            print(f"Ters kodlama hatası: {e}")
        return None

    def hava_durumu_ekle(self, lat, lon):
        il_ismi = self.il_ismini_bul(lat, lon)
        basarili = False
        
        if il_ismi:
            print(f"İsimle deneniyor: {il_ismi}") 
            url = f"http://api.openweathermap.org/data/2.5/weather?q={il_ismi}&appid={API_KEY}&units=metric&lang=tr"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    veri = response.json()
                    self.konum_karti_olustur(veri, lat, lon)
                    basarili = True
                else:
                    print(f"Kod: {response.status_code}")
            except Exception as e:
                print(f"Hata: {e}")

        if not basarili:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=tr"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    veri = response.json()
                    self.konum_karti_olustur(veri, lat, lon)
                else:
                    hata_mesaji = f"Veri Alınamadı. Kod: {response.status_code}"
                    if response.status_code == 401:
                        hata_mesaji += "\nSebep: API Anahtarı geçersiz."
                    messagebox.showerror("API Hatası", hata_mesaji)
            except Exception as e:
                messagebox.showerror("Hata", f"Bağlantı hatası: {e}")

    def konum_karti_olustur(self, veri, lat, lon):
        sehir = veri.get("name", "Bilinmeyen")
        
        for item in self.active_locations:
            if item.get("city_name") == sehir:
                messagebox.showwarning("Zaten Ekli", f"{sehir} zaten listenizde mevcut.")
                return

        ulke = veri["sys"].get("country", "")
        temp = int(veri["main"]["temp"])
        durum = veri["weather"][0]["description"].title()
        
        marker = self.map_widget.set_marker(lat, lon, text=f"{sehir}\n{temp}°C")

        card_frame = ctk.CTkFrame(self.results_container, fg_color="#2B2B2B", border_width=1, border_color="#333")
        card_frame.pack(fill="x", pady=5, padx=5)
        card_frame.grid_columnconfigure(0, weight=1)
        
        header_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5,0))
        
        lbl_name = ctk.CTkLabel(header_frame, text=f"{sehir}, {ulke}", font=("Arial", 14, "bold"), anchor="w")
        lbl_name.pack(side="left")

        lbl_live = ctk.CTkLabel(header_frame, text="✓ Canlı", font=("Arial", 10, "bold"), text_color="#2ecc71")
        lbl_live.pack(side="left", padx=5)

        btn_close = ctk.CTkButton(
            header_frame, text="✕", width=20, height=20, 
            fg_color="transparent", hover_color="#c0392b", text_color="gray",
            command=lambda m=marker: self.sil_konum(m)
        )
        btn_close.pack(side="right")

        lbl_temp = ctk.CTkLabel(card_frame, text=f"{temp}°C", font=("Arial", 26, "bold"), text_color="#3B8ED0")
        lbl_temp.grid(row=1, column=0, sticky="w", padx=10)

        lbl_desc = ctk.CTkLabel(card_frame, text=durum, font=("Arial", 12), text_color="silver")
        lbl_desc.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 10))

        self.active_locations.append({
            "marker": marker, 
            "frame": card_frame,
            "city_name": sehir
        })

    def sil_konum(self, marker_ref):
        found_item = None
        for item in self.active_locations:
            if item["marker"] == marker_ref:
                found_item = item
                break
        
        if found_item:
            found_item["marker"].delete()
            found_item["frame"].destroy()
            self.active_locations.remove(found_item)

if __name__ == "__main__":
    app = HavaDurumuApp()
    app.mainloop()