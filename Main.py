import streamlit as st
import pickle
from pathlib import Path
import streamlit_authenticator as stauth
from ultralytics import YOLO
from collections import defaultdict
from PIL import Image
from torchvision.transforms import functional as F
import sqlite3 as sql
from shapely.geometry import Point, Polygon
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import time
import cv2

st.set_page_config(
    page_title="Kamera",
    page_icon="📷",
)

st.title("Ana Sayfa")
st.sidebar.success("Lütfen bir sayfa seçiniz.")

def check_person_in_section(x, y, section_coordinates, person_ids_in_section, section_track_ids, track_id):
    # Order the coordinates for checking
    order_of_points = [0, 1, 3, 2]  # Adjust these indices for drawing order (for shapely)
    section_coordinates_ordered = [section_coordinates[i] for i in order_of_points]
    
    section_polygon = Polygon(section_coordinates_ordered)
    person_point = Point(x, y)

    if person_point.within(section_polygon):
        if track_id not in person_ids_in_section:
            person_ids_in_section[track_id] = {'entry_time': time.time(), 'counted': False}
            
        # Check if the person has been in the section for at least 2 seconds and not counted yet
        current_time = time.time()
        entry_time = person_ids_in_section[track_id]['entry_time']
        if current_time - entry_time > 2 and not person_ids_in_section[track_id]['counted']:
            person_ids_in_section[track_id]['counted'] = True
            section_track_ids.add(track_id)
            return True
    else:
        # Reset the counted flag if the person leaves the section
        if track_id in person_ids_in_section and track_id in section_track_ids:
            del person_ids_in_section[track_id]
            section_track_ids.remove(track_id)
            
    return False

def transform_list_to_dict(data_list):
    result_dict = {}

    for item in data_list:
        sect, tlx, tly, trx, try_, blx, bly, brx, bry = item
        coordinates = [(tlx, tly), (trx, try_), (blx, bly), (brx, bry)]
        
        # Check if the section already exists in the dictionary
        if sect in result_dict:
            result_dict[sect].extend(coordinates)
        else:
            result_dict[sect] = coordinates

    return result_dict

def draw_section_polygons(frame, section_coordinates, section_number):
    # Draw polygons for the section
    cv2.polylines(
        frame,
        [np.array(section_coordinates, np.int32)],
        isClosed=True,
        color=(0, 0, 255),
        thickness=1
    )
    
    # Write section number on top of the polygon
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thickness = 1
    font_color = (255, 255, 255)  # White text
    text_size = cv2.getTextSize(str(section_number), font, font_scale, font_thickness)[0]
    text_position = (int((section_coordinates[0][0] + section_coordinates[1][0]) / 2 - text_size[0] / 2),
                     int((section_coordinates[0][1] + section_coordinates[2][1]) / 2 + text_size[1] / 2))
    cv2.putText(frame, str(section_number), text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)
    
    return frame


#-------- User authentication-------
names = ["Ergun Altindag","Dolay Demirel"]
usernames = ["ergn","dly"]


#--- Load hashed passwords ---
file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator =  stauth.Authenticate(names, usernames, hashed_passwords,"Main","abcdef", cookie_expiry_days=30)

name,authentication_status,username = authenticator.login("Login","main")


if authentication_status == False:
    st.error("Şifre veya kullanıcı adı hatalı")
    
if authentication_status:
    authenticator.logout("Çıkış","sidebar")
    st.sidebar.title(f"Hoşgeldiniz {name}") 
    
    model = YOLO('yolov8m.pt')
    
    model_secimi = st.selectbox('Model seçin', ('M-Model', 'S-Model','N-Model') ,key='model_key') 
    if model_secimi == 'M-Model':
        model = YOLO('yolov8m.pt')
    if model_secimi == 'S-Model':
        model = YOLO('yolov8s.pt')
    if model_secimi == 'N-Model':
        model = YOLO('yolov8n.pt')
    vid_area = st.empty()
    
    # video_path = 0
    
    option = st.selectbox('Kamera seçin', ('Kamera 1', 'Kamera 2') ,key='kamera_key') 
    if option == 'Kamera 1':
        
        video_path = 0 
        
        conn = sql.connect("Bitirme.db")
        cursor = conn.cursor()
        
        add_command = """SELECT sec, bbox_tl_x, bbox_tl_y, bbox_tr_x, bbox_tr_y, bbox_bl_x, bbox_bl_y, bbox_br_x, bbox_br_y FROM REYON WHERE kamera = 0 """
        cursor.execute(add_command)
        kamera_0 = cursor.fetchall()
        
        add_command = """SELECT sec,kullanici_sayisi  FROM REYON WHERE kamera = 0 """
        cursor.execute(add_command)
        sec_degerleri_cam0 = cursor.fetchall()
        sec_degerleri_cam0 = dict(sec_degerleri_cam0)
       
        conn.commit()
        conn.close() 
        count_section = sec_degerleri_cam0
        
        #section_coordinates = const.sections_camera1

    if option == 'Kamera 2':
        
        video_path = 1
        
        conn = sql.connect("Bitirme.db")
        cursor = conn.cursor()
        
        add_command = """SELECT sec, bbox_tl_x, bbox_tl_y, bbox_tr_x, bbox_tr_y, bbox_bl_x, bbox_bl_y, bbox_br_x, bbox_br_y FROM REYON WHERE kamera = 1 """
        cursor.execute(add_command)
        kamera_1 = cursor.fetchall()
        
        add_command = """SELECT sec,kullanici_sayisi  FROM REYON WHERE kamera = 1 """
        cursor.execute(add_command)
        sec_degerleri_cam1 = cursor.fetchall()
        sec_degerleri_cam1 = dict(sec_degerleri_cam1)
        
        conn.commit()
        conn.close() 
        count_section = sec_degerleri_cam1
        
    # DEBUG
    # st.markdown(f"const.points: {const.points}")
    # st.markdown(f"section_coordinates: {section_coordinates}")
    #
    # Order the coordinates to draw
    # order_of_keys = ['top_left', 'top_right', 'bottom_right', 'bottom_left']
    # ordered_to_draw = {key: section_coordinates[key] for key in order_of_keys}
    #
    # Initialize counters for each section and each person
    # count_section = 0
    
    count_right_section = 0
    count_people = 0
    current_count = 0
    current_count_people = 0
    person_ids_in_section = {}

    # Time threshold for counting (2 seconds)
    # time_threshold = 2.0
    
    # test video path
    # video_path = 'C:/Users/user/Desktop/bitirme/pedestrian.mp4'

    cap = cv2.VideoCapture(video_path)

    # Get video properties (width, height, frames per second)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    track_history = defaultdict(lambda: [])

    # Initialize trail coordinates dictionary
    track_list = {}
    
    count_display = st.empty()
    count_display3 = st.empty()
    count_display2 = st.empty()
    
    if option == 'Kamera 1':
        sections = transform_list_to_dict(kamera_0)
       
    elif option == 'Kamera 2':
        sections = transform_list_to_dict(kamera_1)
        
    else:
        st.error("invalid camera") 
        # Test for Error handling
    
    person_ids_in_section = {section_number: {} for section_number in sections}
    section_track_ids = {section_number: set() for section_number in sections}

    all_center_points=[]
    while cap.isOpened():
        
        
        # Read a frame from the video
        success, frame = cap.read()
        
        gunluk_tarih = datetime.now().date()

                                
        count_display.markdown(f"Farklı müşteri: {count_people} ")  
        count_display3.markdown(f"Mevcut müşteri: {current_count}")     
        
        section_counts_str = ""

        conn = sql.connect("Bitirme.db")
        cursor = conn.cursor()

        add_command = """SELECT kullanici_sayisi FROM MAGAZA WHERE date = ?"""
        data_db = (gunluk_tarih.strftime('%Y%m%d'),)
        cursor.execute(add_command, data_db)

        add_command = """SELECT kullanici_sayisi FROM MAGAZA WHERE date = ?"""
        data_db = (gunluk_tarih.strftime('%Y%m%d'),)
        cursor.execute(add_command, data_db)
        
        if cursor.fetchone() is None:
            add_command = "INSERT INTO MAGAZA (kullanici_sayisi, date) VALUES (?, ?)"
            data_db = (int(count_people), (gunluk_tarih.strftime('%Y%m%d')))
            cursor.execute(add_command, data_db)
        else:
            add_command = "UPDATE MAGAZA SET kullanici_sayisi = ? WHERE date = ?"
            data_db = (int(count_people), (gunluk_tarih.strftime('%Y%m%d')))
            cursor.execute(add_command, data_db)
    
        add_command = "SELECT SUM(kullanici_sayisi) FROM REYON WHERE kamera=0;"
        cursor.execute(add_command)
        toplam_kullanici_sayisi_0 = cursor.fetchone()[0]

        add_command = "SELECT SUM(kullanici_sayisi) FROM REYON WHERE kamera=1;"
        cursor.execute(add_command)
        toplam_kullanici_sayisi_1 = cursor.fetchone()[0]
         
        cursor.execute("SELECT kullanici_sayisi, pop FROM REYON WHERE kamera = 0;")
        guncelleme_listesi = []
        for row in cursor.fetchall():
            kullanici_sayisi, pop_degeri = row
            yeni_pop_degeri = ((kullanici_sayisi / toplam_kullanici_sayisi_0))
            guncelleme_listesi.append((yeni_pop_degeri, kullanici_sayisi))       

        # Update processes
        for guncelleme in guncelleme_listesi:
            cursor.execute("UPDATE REYON SET pop = ? WHERE kullanici_sayisi = ?;", guncelleme)
                
        cursor.execute("SELECT kullanici_sayisi, pop FROM REYON WHERE kamera = 1;")
        guncelleme_listesi = []
        for row in cursor.fetchall():
            kullanici_sayisi, pop_degeri = row
            yeni_pop_degeri = ((kullanici_sayisi / toplam_kullanici_sayisi_1))
            guncelleme_listesi.append((yeni_pop_degeri, kullanici_sayisi))

        # Update processes
        for guncelleme in guncelleme_listesi:
            cursor.execute("UPDATE REYON SET pop = ? WHERE kullanici_sayisi = ?;", guncelleme)
                
        conn.commit()
        conn.close()
        
        if success:
            
            # Run YOLOv8 tracking on the frame, persisting tracks between frames
            results = model.track(frame, device=0, save=False, stream=True, conf=0.5, persist=True, classes=0)
            for result in results:
                if result.boxes is None or result.boxes.id is None:
                    continue
                else:
                    boxes = result.boxes.xywh.cpu()
                    track_ids = result.boxes.id.cpu().numpy().astype(int)

                    # Visualize the results on the frame
                    annotated_frame = result.plot()

                    # Process each person's bounding box
                    for box, track_id in zip(boxes, track_ids):
                        x, y, w, h = box

                        # Update trail coordinates for each person
                        if track_id not in track_list:
                            track_list[track_id] = []
                        track_list[track_id].append((x, y))

                        # Draw the tracking lines
                        track = track_history[track_id]
                        track.append((float(x), float(y)))  # x, y center point
                        for i in range(1, len(track)):
                            pt1 = tuple(map(int, track[i - 1]))
                            pt2 = tuple(map(int, track[i]))
                            cv2.line(annotated_frame, pt1, pt2, (0, 255, 0), 1)

                    current_count_people = max(result.boxes.id.cpu().numpy().astype(int))
                    count_people = max(count_people, current_count_people)
                    current_count = len(result.boxes)
                    all_center_points.append((int(x),int(y)))
                    
                    if "average" not in track_list:
                        track_list["average"] = []
                    
                    smoothing_factor = 0.2
                    
                    if all_center_points:
                        # Draw a smoothed line connecting all the average center points over time
                        for i in range(1, len(track_list["average"])):
                            pt1 = tuple(map(int, track_list["average"][i - 1]))
                            pt2 = tuple(map(int, track_list["average"][i]))
                            smoothed_point = (
                                int(smoothing_factor * pt1[0] + (1 - smoothing_factor) * pt2[0]),
                                int(smoothing_factor * pt1[1] + (1 - smoothing_factor) * pt2[1])
                            )
                            cv2.line(annotated_frame, pt1, smoothed_point, (0, 0, 255), 1)

                        average_center = tuple(np.mean(all_center_points, axis=0, dtype=int))
                        track_list["average"].append(average_center)  # Store the current average center point in the track list
                    
                    for section_number, section_coordinates in sections.items():
                        for box, track_id in zip(boxes, track_ids):
                            x, y, w, h = box
                            # Check if the person's center is in the section and has been there for 2 seconds
                            if check_person_in_section(x, y, section_coordinates, person_ids_in_section[section_number], section_track_ids[section_number], track_id):
                                count_section[section_number] += 1
            
                        order_of_points = [0, 1, 3, 2]  # Adjust these indices based on your specific order
                        ordered_to_draw = [section_coordinates[i] for i in order_of_points]
                        annotated_frame = draw_section_polygons(annotated_frame, ordered_to_draw, section_number)

                    # Local Annotation for debug with local scripts
                    # Display the counts
                    # font_size = 0.6
                    # font_thickness = 1
                    # font_color = (255, 255, 255)  # White text
                    # background_color = (0, 0, 0)  # Black background
                    #
                    # Section
                    # text = f"Left Section: {count_section}"
                    # text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_size, font_thickness)[0]
                    # background_rect = ((10, 10), (10 + text_size[0] + 10, 10 + text_size[1] + 10))
                    # cv2.rectangle(annotated_frame, background_rect[0], background_rect[1], background_color, -1)
                    # cv2.putText(annotated_frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, font_size, font_color, font_thickness, cv2.LINE_AA)
                    #
                    # People Count
                    # text = f"People Count: {count_people}"
                    # text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_size, font_thickness)[0]
                    # background_rect = ((width // 2 - text_size[0] // 2 - 10, 10), (width // 2 + text_size[0] // 2 + 10, 10 + text_size[1] + 10))
                    # cv2.rectangle(annotated_frame, background_rect[0], background_rect[1], background_color, -1)
                    # cv2.putText(annotated_frame, text, (width // 2 - text_size[0] // 2, 30), cv2.FONT_HERSHEY_SIMPLEX, font_size, font_color, font_thickness, cv2.LINE_AA)
                    #
                    # People Count 2
                    # text = f"Current People Count: {current_count}"
                    # text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_size, font_thickness)[0]
                    # background_rect = ((width // 2 - text_size[0] // 2 - 10, height - 50), (width // 2 + text_size[0] // 2 + 10, height - 50 + text_size[1] + 10))
                    # cv2.rectangle(annotated_frame, background_rect[0], background_rect[1], background_color, -1)
                    # cv2.putText(annotated_frame, text, (width // 2 - text_size[0] // 2, height - 50 + 20), cv2.FONT_HERSHEY_SIMPLEX, font_size, font_color, font_thickness, cv2.LINE_AA)
                    #
                    # annotated_frame = cv2.resize(annotated_frame, (0, 0), fx=0.5, fy=0.5)
                    #cv2.imshow('test', annotated_frame) 
                    
                    vid_area.image(annotated_frame,channels='BGR')         
                    cam = 0
                    conn = sql.connect("Bitirme.db")
                    cursor = conn.cursor()
                    
                    for section_number, section_count in count_section.items():
                        if option == 'Kamera 1':
                            cam = 0
                        else:
                            cam = 1   
                        
                        section_counts_str += f"{section_number}.bölgedeki müşteri sayısı: {section_count}  "
                                               
                        add_command = "UPDATE REYON SET kullanici_sayisi=? WHERE sec=? AND kamera=?"
                        data_db = (section_count,section_number,cam)
                        cursor.execute(add_command, data_db)
                        
                    conn.commit()
                    conn.close()
                    
                    # Fetch data
                    count_display2.markdown(section_counts_str)      
                    
            # Break the loop if 'q' is pressed. Better to have it on for debugging and testing
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            # Handles videos instead of cameras
            # Break the loop if the end of the video is reached
            break
    
    # Debug and testing for potential customer lines
    # Create a single image with every trail at once
    # trail_img = np.ones((height, width, 3), dtype=np.uint8) * 255  # White background
    # for _, trail in track_list.items():
    #     for x, y in trail:
    #         cv2.circle(trail_img, (int(x), int(y)), 2, (0, 0, 0), -1)  # Black points for the trail
    # cv2.imwrite('all_trails.png', trail_img)

    cap.release()
    cv2.destroyAllWindows()