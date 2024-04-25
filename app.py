import streamlit as st
import threading
import pandas as pd
import numpy as np
import openpyxl
from datetime import datetime
import time
from streamlit_folium import folium_static
import folium
import ast
import json
import folium
import statistics
from datetime import datetime
from openai import OpenAI
import streamlit_ext as ste
from folium import plugins

df = pd.read_excel('Bruksela_miejsca_odnosniki.xlsx')


def create_map(df_rec, choose_rec):

    places_all = []
    places = []
    places_2 = []
    special_place = [{"name": df_rec.iloc[choose_rec,2] , "location": (df_rec.iloc[choose_rec,4], df_rec.iloc[choose_rec,5])}]
    df_rec_atr = df_rec[df_rec['jedzenie']==0]

    for i in range(len(df_rec)):
        places_all.append({"name": df_rec.iloc[i,2] , "location": (df_rec.iloc[i,4], df_rec.iloc[i,5])})

    for i in range(len(df_rec_atr)):
        if df_rec_atr.iloc[i,2] !=df_rec.iloc[choose_rec, 2]:
            places.append({"name": df_rec_atr.iloc[i,2] , "location": (df_rec_atr.iloc[i,4], df_rec_atr.iloc[i,5])})

    df_rec_food = df_rec[df_rec['jedzenie']==1]

    for i in range(len(df_rec_food)):
        if df_rec_food.iloc[i,2] !=df_rec.iloc[choose_rec, 2]:
            places_2.append({"name": df_rec_food.iloc[i,2] , "location": (df_rec_food.iloc[i,4], df_rec_food.iloc[i,5])})
    
    latitudes = [place["location"][0] for place in places + places_2 + special_place]
    longitudes = [place["location"][1] for place in places + places_2 + special_place]
    avg_lat =  special_place[0]["location"][0]
    avg_lng =  special_place[0]["location"][1]
    
    map = folium.Map(location=[avg_lat, avg_lng], zoom_start=15)
    
    i = 1

    for place in places_all:
        if place in places:
            folium.Marker(
            location=place["location"], 
            popup=place["name"],
             icon=plugins.BeautifyIcon(
                         icon="arrow-down", icon_shape="marker",
                         number=i,
                         border_color= "Grey",
                         background_color="Orange")).add_to(map)
            
        elif place in places_2:
            folium.Marker(
            location=place["location"], 
            popup=place["name"],
            icon=plugins.BeautifyIcon(
                         icon="arrow-down", icon_shape="marker",
                         number=i,
                         border_color= "Grey",
                         background_color="Purple")).add_to(map)

        else:
            folium.Marker(
            location=special_place[0]["location"], 
            popup=special_place[0]["name"],
            icon=plugins.BeautifyIcon(
                         icon="arrow-down", icon_shape="marker",
                         number=i,
                         border_color= "Grey",
                         background_color="Green")).add_to(map)
        i+=1
        
    return map
         

    

primary_color = "#00AADB"

st.set_page_config(
    page_title="Dokąd tym razem? 💺",
    page_icon=":bar_chart:",
    layout="wide",
)

pd.set_option('display.float_format', '{:.0f}'.format)

st.markdown("<h1 style='margin-top: -70px; text-align: center;'>Dokąd tym razem? 💺</h1>", unsafe_allow_html=True)

nazwy = pd.read_excel('miasta.xlsx')




st.markdown(
    """
    <style>
    .sidebar .sidebar-content {
        width: 30%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

colA, colB = st.sidebar.columns([1.5,1.5])


with colA:
    panstwa =  sorted(list(set(nazwy['Państwa'].to_list())))
    panstwo = st.selectbox('Wybierz państwo (nieobowiązkowe)', panstwa)

with colB:
    if panstwo==' ':
        miasta =  sorted(list(set(nazwy['Miasta'].to_list())))
    else:
        miasta = sorted(list(set(nazwy.loc[nazwy['Państwa']==panstwo, 'Miasta'].to_list())))
    miasto = st.selectbox("### **Wybierz / wpisz nazwę miasta:**", miasta, index=miasta.index('Bruksela'))

with colA:
    zakres_ocen = st.radio("Wybierz zakres ocen rekomendowanych miejsc (średnia na Google Maps)", ['3,5 i wyżej', '4 i wyżej', '4,5 i wyżej'], horizontal=True, index =0)
if zakres_ocen == '3,5 i wyżej':
    df_rec = df.copy()
if zakres_ocen == '4 i wyżej':
    df_rec = df[df['rating']>=4]
if zakres_ocen == '4,5 i wyżej':
    df_rec = df[df['rating']>=4.5]

with colB:
    l_rekomendacji = st.slider('Wybierz liczbę rekomendacji (rekomendacje są wyświetlane w kolejności od najpopularniejszych wg. liczby opinii na Google Maps)', min_value=min(10, len(df_rec)/2), max_value=len(df_rec), value=len(df_rec), step=5)
df_best = df_rec.iloc[0:l_rekomendacji,:]
df_best_atr = df_rec[df_rec['jedzenie']==0].reset_index(drop=True).iloc[0:l_rekomendacji,:]
df_best_food = df_rec[df_rec['jedzenie']==1].reset_index(drop=True).iloc[0:l_rekomendacji,:]

if len(df_best[df_best['jedzenie']==0])>=5 & len(df_best[df_best['jedzenie']==1])>=3:
    df_rec = df_best.reset_index(drop=True).copy()
elif len(df_best[df_best['jedzenie']==0])<5:
    df_rec = pd.concat([df_best_atr.iloc[:5], df_best_food.iloc[:l_rekomendacji - len(df_best_atr.iloc[:5]), ]]).reset_index(drop=True)
elif len(df_best[df_best['jedzenie']==1])<3:
    df_rec = pd.concat([df_best_food.iloc[:3], df_best_atr.iloc[:l_rekomendacji - len(df_best_atr.iloc[:3]), ]]).reset_index(drop=True)


df_rec = df_rec.sort_values('ratingCount', ascending = False)

choose__phrase = st.sidebar.text_input("Wyszukaj konkretną atrakcję (np. popularny bar / miejsce do przejażdżek rowerowych)",  "", key="placeholder")

if 'previous_choose_phrase' not in st.session_state:
    st.session_state.previous_choose_phrase= ''
    st.session_state.previous_miasto = ''
    st.session_state.previous_zakres_ocen = ''
    st.session_state.previous_l_rekomendacji = ''

tekst = f'''
             Po wybraniu miasta generowana jest lista miejsc (atrakcji oraz 
             miejsc z jedzeniem) wraz z mapką i odnośnikami do videoblogów, w których mowa 
             o tych miejsach. Dodatkowo, po prawej stronie wyświetlane są informacje o atrakcji najbardziej dopasowanej do podanych oczekiwań📈'''

st.markdown(f"<h6 style='margin-top: -23px; text-align: left;'>{tekst}</h6>", unsafe_allow_html=True)


if "choose_rec" not in st.session_state:
    st.session_state.choose_rec = 0

if choose__phrase != st.session_state.previous_choose_phrase or miasto != st.session_state.previous_miasto or zakres_ocen != st.session_state.previous_zakres_ocen or l_rekomendacji != st.session_state.previous_l_rekomendacji:
    if choose__phrase!= '':
        with st.sidebar:
            st.write(f'✅ Szukam miejsca odpowiadającego Twoim oczekiwaniom')
        st.session_state.choose_rec = 8
    else:
        st.session_state.choose_rec = 0
    st.session_state.previous_choose_phrase = choose__phrase
    st.session_state.previous_miasto = miasto
    st.session_state.previous_zakres_ocen = zakres_ocen
    st.session_state.previous_l_rekomendacji = l_rekomendacji

if miasto != ' ':

        col1, col2, col3 = st.columns([5,0.05,2])



      #  with col3:                
      #      docx_file_path = f"{miasto}_rec.docx"    
#
 #           ste.download_button(
  #                  label="Pobierz raport",
   #                 data=open(docx_file_path, 'rb').read(),
    #                file_name=docx_file_path,
    #                mime="application/vnd.ms-docx"
    #            )


        with col3:
            col3a, col3b, col3c, col3d = st.columns([0.5,1,1,0.5])
            with col3b:
                if st.button("⬅️"):
                    if st.session_state.choose_rec > 0:
                        st.session_state.choose_rec -= 1
            with col3c:
                if st.button("➡️"):
                    if st.session_state.choose_rec < len(df_rec) - 1:
                        st.session_state.choose_rec += 1
            
            st.markdown(f'<p style="font-weight:bold">{st.session_state.choose_rec+1}. {df_rec.iloc[st.session_state.choose_rec,2]}</p>', unsafe_allow_html=True)
            st.write(f'{df_rec.iloc[st.session_state.choose_rec,12]}')



            numbers_and_links_string = 'Zobacz więcej: '
            for i, link in enumerate(eval(df_rec.iloc[st.session_state.choose_rec,1]), start=1):
                numbers_and_links_string += f"<a href='{link}' target='_blank'>{i}</a> "
            st.markdown(numbers_and_links_string, unsafe_allow_html=True)



        with col1:
            map = create_map(df_rec, st.session_state.choose_rec)
            folium_static(map)
        

   



    