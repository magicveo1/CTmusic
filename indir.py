import yt_dlp

def mp3_indir(url):
    ayarlar = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192', # Ses kalitesi (192, 256 və ya 320 edə bilərsən)
        }],
        'outtmpl': '%(title)s.%(ext)s', # İndirilən faylın adı videonun başlığı olacaq
        'ignoreerrors': True, # Silinmiş və ya gizli video çıxarsa xəta verib dayanmasın, sonrakinə keçsin
    }

    print("İndirmə əməliyyatı başladılır, bu əməliyyat videonun sayından asılı olaraq bir az vaxt ala bilər...")
    
    with yt_dlp.YoutubeDL(ayarlar) as ydl:
        ydl.download([url])
        
    print("Bütün proseslər tamamlandı! Mahnılar kodun olduğu qovluğa yığıldı, Sənan brat.")

# Tırnaqların arasına istədiyin YouTube kanalının (və ya /videos, /shorts bölməsinin) yaxud pleylistinin linkini yapışdır:
kanal_linki = "BURAYA_LINK_GELECEK"

# Funksiyanın işləməsi üçün bu sətr mütləq olmalıdır:
mp3_indir(kanal_linki)
