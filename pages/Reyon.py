import const
import streamlit_authenticator as stauth
import streamlit as st
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
import pandas as pd
import numpy as np
import cv2
import pickle
from pathlib import Path
import sqlite3 as sql

st.set_page_config(
    page_title="Yeni Bölge Tanımlama",
    page_icon="🛒",
    # layout="wide",
    )

"# Yeni Bölge Tanımlama"
st.sidebar.success("Lütfen bir sayfa seçiniz.")

#-------- User authentication-------
names = ["Ergun Altindag","Dolay Demirel"]
usernames = ["ergn","dly"]

#--- Load hashed passwords ---
file_path = Path("C:/Users/TULPAR/Desktop/Streamlit/hashed_pw.pkl")
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator =  stauth.Authenticate(names, usernames, hashed_passwords,"Main","abcdef", cookie_expiry_days=30)

name,authentication_status,username = authenticator.login("Login","main")

if authentication_status == False:
    st.error("Şifre veya kullanıcı adı hatalı")
    
if authentication_status:
    authenticator.logout("Çıkış","sidebar")
    st.sidebar.title(f"Hoşgeldiniz {name}") 

    option = st.selectbox('Kamera seçin', ('Kamera 1', 'Kamera 2') ,key='kamera_key') 
    if option == 'Kamera 1':
        video_path = 0
        sections_dict = const.sections_camera1
        reset_flags_dict = const.reset_flags_camera1
    if option == 'Kamera 2':
        video_path = 1
        sections_dict = const.sections_camera2
        reset_flags_dict = const.reset_flags_camera2

    section_number = st.selectbox("Select Section Number", range(1, 11), key="section_number")

    frame = 0

    cap = cv2.VideoCapture(video_path)

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame)

    success, first_frame = cap.read()

    pil_image = Image.fromarray(cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB))
    
    sections = {}
    reset_flags = {}

    if section_number not in const.sections_camera1 and option == 'Kamera 1':
        const.sections_camera1[section_number] = []
        const.reset_flags_camera1[section_number] = False

    if section_number not in const.sections_camera2 and option == 'Kamera 2':
        const.sections_camera2[section_number] = []
        const.reset_flags_camera2[section_number] = False
        "## Choose 4 points by clicking on the image"

    def get_ellipse_coords(point: tuple[int, int]) -> tuple[int, int, int, int]:
        center = point
        radius = 10
        return (
            center[0] - radius,
            center[1] - radius,
            center[0] + radius,
            center[1] + radius,
        )
        
    reyon_adi_text = st.empty()
    conn = sql.connect("Bitirme.db")
    cursor = conn.cursor()
    add_command = """SELECT reyon_adi from REYON WHERE kamera = ? and sec=? """
    data_db = (video_path,section_number)
    cursor.execute(add_command, data_db)
    reyon = cursor.fetchone() 
    if reyon:
        reyon_adi_text.markdown(f"Reyon adı = {reyon[0]}")
    conn.commit()
    conn.close()

    ok_pressed, reset_pressed = st.columns([50, 6])
    with pil_image as img:
        draw = ImageDraw.Draw(img)

        # Draw an ellipse at each coordinate in points
        sections_dict = const.sections_camera1 if option == 'Kamera 1' else const.sections_camera2
        reset_flags_dict = const.reset_flags_camera1 if option == 'Kamera 1' else const.reset_flags_camera2
        
        for point in sections_dict[section_number]:
            coords = get_ellipse_coords(point)
            draw.ellipse(coords, fill="red")
            
        if len(sections_dict[section_number]) < 4:
            value = streamlit_image_coordinates(img, key=f"pil_{section_number}")

            if value is not None:
                point = value["x"], value["y"]

                if point not in sections_dict[section_number]:
                    sections_dict[section_number].append(point)
                    st.experimental_rerun()
        else:
            # Draw an ellipse at each final coordinate
            for point in sections_dict[section_number]:
                coords = get_ellipse_coords(point)
                draw.ellipse(coords, fill="red")

            # Show the final image with selected points
            st.image(img, caption="Image with Selected Points", use_column_width=True)
            
            reyonadi = st.text_input('Reyon adını giriniz')
            
            if ok_pressed.button('Tamam'):
                # Sort points by y and then by x
                ordered_list = sorted(sections_dict[section_number], key=lambda coord: (coord[1], coord[0]))
                # Take the two coordinates with the lowest y value
                top_left, top_right = ordered_list[:2]
                # Order them by x in ascending order
                top_left, top_right = sorted([top_left, top_right], key=lambda coord: coord[0])

                # Take the remaining two coordinates
                bottom_left, bottom_right = ordered_list[2:]
                # Order them by x in ascending order
                bottom_left, bottom_right = sorted([bottom_left, bottom_right], key=lambda coord: coord[0])

                final_ordered_list = [top_left, top_right, bottom_left, bottom_right]

                # Debugging and testing by listing the selected coordinates
                # st.data_editor(
                #     final_ordered_list,
                #     column_config={
                #         "sales": st.column_config.ListColumn(
                #             "Final Ordered List:",
                #             width="medium",
                #         ),
                #     },
                #     hide_index=True,
                # )
                
                conn = sql.connect("Bitirme.db")
                cursor = conn.cursor()
                
                s = str(top_left)
                x1, x2 = s.split(",")
                s = str(top_right)
                x3, x4 = s.split(",")
                s = str(bottom_left)
                x5, x6 = s.split(",")
                s = str(bottom_right)
                x7, x8 = s.split(",")
                x1 = ''.join(filter(str.isdigit, x1))
                x2 = ''.join(filter(str.isdigit, x2))
                x3 = ''.join(filter(str.isdigit, x3))
                x4 = ''.join(filter(str.isdigit, x4))
                x5 = ''.join(filter(str.isdigit, x5))
                x6 = ''.join(filter(str.isdigit, x6))
                x7 = ''.join(filter(str.isdigit, x7))
                x8 = ''.join(filter(str.isdigit, x8))
                
                add_command = """SELECT sec FROM REYON WHERE kamera = ? and sec=? """
                data_db = (video_path,section_number)
                cursor.execute(add_command, data_db)
                
                if reyonadi:
                    if cursor.fetchone() is None:  
                        add_command ="INSERT INTO REYON (sec, bbox_tl_x, bbox_tl_y, bbox_tr_x, bbox_tr_y, bbox_bl_x, bbox_bl_y, bbox_br_x, bbox_br_y, pop, kullanici_sayisi,kamera,reyon_adi) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
                        data_db = (section_number,x1,x2,x3,x4,x5,x6,x7,x8,0.0,0,video_path,reyonadi)
                        cursor.execute(add_command,data_db)
                        st.warning("Yeni Section Eklendi!")
                        
                        add_command = """SELECT reyon_adi from REYON WHERE kamera = ? and sec=? """
                        data_db = (video_path,section_number)
                        cursor.execute(add_command, data_db)
                        reyon = cursor.fetchone() 
                        if reyon:
                            reyon_adi_text.markdown(f"Reyon adı = {reyon[0]}") 
                    else:
                        add_command = "UPDATE REYON SET bbox_tl_x=?, bbox_tl_y=?, bbox_tr_x=?, bbox_tr_y=?, bbox_bl_x=?, bbox_bl_y=?, bbox_br_x=?, bbox_br_y=?, reyon_adi=? WHERE sec=? AND kamera=?"
                        data_db = (x1, x2, x3, x4, x5, x6, x7, x8,reyonadi, section_number, video_path)
                        cursor.execute(add_command, data_db)
                        st.warning("Section Güncellendi!") 
                        
                        add_command = """SELECT reyon_adi from REYON WHERE kamera = ? and sec=? """
                        data_db = (video_path,section_number)
                        cursor.execute(add_command, data_db)
                        reyon = cursor.fetchone() 
                        if reyon:
                            reyon_adi_text.markdown(f"Reyon adı = {reyon[0]}")
                    
                    conn.commit()
                    conn.close()
                
                else:
                    st.warning("Reyon Adı giriniz!")
                
                const.points.extend(final_ordered_list)
                sections_dict[section_number] = final_ordered_list
                reset_flags[section_number] = False

                #st.markdown(sections_dict)
                
        conn = sql.connect("Bitirme.db")
        cursor = conn.cursor()  
        
        add_command = """SELECT sec FROM REYON WHERE kamera = ? and sec=? """
        data_db = (video_path,section_number)
        cursor.execute(add_command, data_db)
                
        if cursor.fetchone() is not None:  
            if reset_pressed.button('Sıfırla'):
                conn = sql.connect("Bitirme.db")
                cursor = conn.cursor()
                            
                add_command ="DELETE from REYON WHERE sec=? and kamera=?"
                data_db = (section_number,video_path)
                cursor.execute(add_command,data_db)
                    
                conn.commit()
                conn.close()
                        
                st.warning("Section Silindi!")    
                sections_dict[section_number] = []
                reset_flags[section_number] = True
                st.experimental_rerun()
                
        conn.commit()
        conn.close()
