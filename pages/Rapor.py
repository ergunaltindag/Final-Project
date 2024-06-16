import streamlit_authenticator as stauth
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
import pickle
from pathlib import Path
import sqlite3 as sql
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.ticker import AutoLocator, AutoMinorLocator
import cv2
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Rapor",
    page_icon="📝",
    # layout="wide",
    )

"# Rapor Sayfası"
st.sidebar.success("Lütfen bir sayfa seçiniz.")

#-------- User authentication-------
names = ["Ergun Altindag","Dolay Demirel"]
usernames = ["ergn","dly"]

#--- Load hashed passwords ---
file_path = Path("C:/Users/TULPAR/Desktop/Streamlit/hashed_pw.pkl")
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

# Use authenticator for login
authenticator =  stauth.Authenticate(names, usernames, hashed_passwords,"Main","abcdef", cookie_expiry_days=30)

name,authentication_status,username = authenticator.login("Login","main")

# Wrong password
if authentication_status == False:
    st.error("Şifre veya kullanıcı adı hatalı")

# Correct password   
if authentication_status:
    authenticator.logout("Çıkış","sidebar")
    st.sidebar.title(f"Hoşgeldiniz {name}") 
    
    # Fetch today's data
    "Bu güne ait Rapor Sayfası"
    gunluk_tarih = datetime.today().date()
    conn = sql.connect("Bitirme.db")
    cursor = conn.cursor() 
    
    # Fetch data for any date  
    add_command = """SELECT kullanici_sayisi FROM MAGAZA WHERE date = ?"""
    data_db = (gunluk_tarih.strftime('%Y%m%d'),)
    cursor.execute(add_command, data_db)  
    bugünki_kullanici_sayisi = cursor.fetchone()[0]
    if bugünki_kullanici_sayisi is not None:
        st.write('Seçilen tarih kullanıcı sayısı:', bugünki_kullanici_sayisi)
    else:
        st.write('Belirtilen tarihte kayıt bulunamadı.')
    
    # Close DB after commits               
    conn.commit()
    conn.close()
    ""
    ""
    ""
    "Günlük Rapor Sayfası"
    
    # Today's data report
    tarih = st.date_input("Getirilmesini istediğiniz tarih seçin", datetime.today().date())
    st.write('Seçilen tarih:', tarih.strftime('%Y.%m.%d'))

    if tarih is not None:
        conn = sql.connect("Bitirme.db")
        cursor = conn.cursor()
        
        add_command = """SELECT kullanici_sayisi FROM MAGAZA WHERE date = ?"""
        data_db = (tarih.strftime('%Y%m%d'),)
        cursor.execute(add_command, data_db)

        kisi_sayisi = cursor.fetchone()

        if kisi_sayisi is not None:
            st.write('Seçilen tarih kullanıcı sayısı:', kisi_sayisi[0])
        else:
            st.write('Belirtilen tarihte kayıt bulunamadı.')
                    
    conn.commit()
    conn.close()
    " "      
    " "       
    " "        
    "Zaman-Aralığı Rapor Sayfası"   
    
    # Fetch data between two dates
    baslangic_tarih = st.date_input("Getirilmesini istediğiniz başlangıç tarihini seçin", datetime.today().date())
    bitis_tarih = st.date_input("Getirilmesini istediğiniz bitiş tarihini seçin", datetime.today().date())
    st.write('Seçilen tarih:', baslangic_tarih.strftime('%Y.%m.%d'),'-',bitis_tarih.strftime('%Y.%m.%d'))

    if baslangic_tarih is not None and bitis_tarih is not None:
        conn = sql.connect("Bitirme.db")
        cursor = conn.cursor()
        
        add_command = """SELECT kullanici_sayisi FROM MAGAZA WHERE date BETWEEN ? AND ? ORDER BY date ASC"""
        data_db = (baslangic_tarih.strftime('%Y%m%d'), bitis_tarih.strftime('%Y%m%d'))
        cursor.execute(add_command, data_db)
        kisi_sayisi = cursor.fetchall()
        
        add_command = """SELECT date FROM MAGAZA WHERE date BETWEEN ? AND ? ORDER BY date ASC"""
        data_db = (baslangic_tarih.strftime('%Y%m%d'), bitis_tarih.strftime('%Y%m%d'))
        cursor.execute(add_command, data_db)
        date = cursor.fetchall()
        
        conn.commit()
        conn.close() 
        
        if kisi_sayisi:
            kisi_sayisi = [item[0] for item in kisi_sayisi]
            date = [item[0] for item in date]
            
            date_labels = [f"{str(date)[:4]}.{str(date)[4:6]}.{str(date)[6:]}" for date in date]

            fig, ax = plt.subplots()
            ax.bar(date_labels, kisi_sayisi)
            
            # x ekseni etiketlerini daha iyi görüntülemek için döndür
            plt.xticks(rotation=45, ha='right')
            fig.subplots_adjust(bottom=0.2)
        
            canvas = fig.canvas
            canvas.draw()
            image_flat = np.frombuffer(canvas.tostring_rgb(), dtype='uint8')  # (H * W * 3,)
            image = image_flat.reshape(*reversed(canvas.get_width_height()), 3)  # (H, W, 3)

            # st.image kullanarak resmi görüntüle
            st.image(image, caption='Zaman Aralığı Grafiği', use_column_width=True)
                        
        else:
            st.write('Belirtilen tarihte kayıt bulunamadı.')
        
    " "      
    " "       
    " "     
    "Reyon Popilarite Sayfası"
        
    conn = sql.connect("Bitirme.db")
    cursor = conn.cursor()
    option = st.selectbox('Kamera seçin', ('Kamera 1', 'Kamera 2') ,key='kamera_key') 
    if option == 'Kamera 1':
        kamera=0
    if option == 'Kamera 2':
        kamera=1 
    
    add_command = """SELECT pop,reyon_adi FROM REYON WHERE kamera=? """
    data_db = (kamera,)
    cursor.execute(add_command, data_db)

    pop_orani = cursor.fetchall()
    
    if kisi_sayisi is not None:
        pop = [item[1] for item in pop_orani]
        reyon_adi = [item[0] for item in pop_orani]

        fig, ax = plt.subplots()
        ax.bar(pop, reyon_adi)

        # Customize the x-axis ticks and labels
        unique_pop_values = list(set(pop))  # Get unique values of 'pop'
        ax.set_xticks(unique_pop_values)  # Set the x-axis ticks
        ax.set_xticklabels(unique_pop_values)  # Set the x-axis tick labels

        # Use AutoLocator for y-axis ticks
        ax.yaxis.set_major_locator(AutoLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())

        canvas = fig.canvas
        canvas.draw()
        image_flat = np.frombuffer(canvas.tostring_rgb(), dtype='uint8')  # (H * W * 3,)
        image = image_flat.reshape(*reversed(canvas.get_width_height()), 3)  # (H, W, 3)

        # Display the image using st.image
        st.image(image, caption='Reyon Popilarite Figürü', use_column_width=True)
                
       
                    
    conn.commit()
    conn.close() 