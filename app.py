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
from typing import List, Iterator
from openai import OpenAI
client = OpenAI(api_key=AI_API_KEY)
import os
import wget
from ast import literal_eval
import qdrant_client
import warnings
from qdrant_client.http import models as rest

primary_color = "#00AADB"

st.set_page_config(
    page_title="Dokąd tym razem? 💺",
    page_icon=":bar_chart:",
    layout="wide",
)

pd.set_option('display.float_format', '{:.0f}'.format)

st.markdown("<h1 style='margin-top: -70px; text-align: center;'>Dokąd tym razem? 💺</h1>", unsafe_allow_html=True)

def query_qdrant(query, collection_name, vector_name='content', top_k=3):

    # Creates embedding vector from user query
    embedded_query = client.embeddings.create(
        input=query,
        model="text-embedding-ada-002",
    ).data[0].embedding
    
    
    query_results = st.session_qdrant.search(
        collection_name=collection_name,
        query_vector=(
            vector_name, embedded_query
        ),
        limit=top_k,
    )
    
    return query_results

def translate(i):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Przetłumacz na język polski"},
            {"role": "user", "content":i}
        ],
    )
    try:
        results = response.choices[0].message.content
    except:
        results = ''
    return results



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
    try:
        miasto = st.selectbox("### **Wybierz / wpisz nazwę miasta:**", miasta, index=miasta.index('Bruksela'))
    except:
        miasto = st.selectbox("### **Wybierz / wpisz nazwę miasta:**", miasta)

if 'previous_choose_phrase' not in st.session_state:
    st.session_state.previous_choose_phrase= ''
    st.session_state.previous_miasto = ''
    st.session_state.previous_zakres_ocen = ''
    st.session_state.previous_l_rekomendacji = ''
    st.session_state.choose_rec = 0
    st.session_df = pd.DataFrame()
    st.session_qdrant = qdrant_client.QdrantClient(url="http://localhost:6334", prefer_grpc=True)

if miasto != st.session_state.previous_miasto:
    if miasto == 'Barcelona':
        st.session_df = pd.read_feather('Barcelona_miejsca_odnosniki_INFO.ftr')
    else:
        st.session_df = pd.read_feather('Bruksela_miejsca_odnosniki_INFO.ftr')
    st.session_df['description_vec'] = st.session_df['description_vec'].apply(lambda x: list(x))
    st.session_df['title_vec'] = st.session_df['title_vec'].apply(lambda x: list(x))
    vector_size = len(st.session_df['description_vec'][0])
    st.session_qdrant = qdrant_client.QdrantClient(url="http://localhost:6333", prefer_grpc=True)
    st.session_qdrant.get_collections()

    st.session_qdrant.recreate_collection(
        collection_name='art',
        vectors_config={
            'title': rest.VectorParams(
                distance=rest.Distance.COSINE,
                size=vector_size,
            ),
            'content': rest.VectorParams(
                distance=rest.Distance.COSINE,
             size=vector_size,
            ),
        }
    )


    st.session_qdrant.upsert(
        collection_name='art',
        points=[
            rest.PointStruct(
                id=k,
                vector={
                    'title': v['title_vec'],
                    'content': v['description_vec'],
                },
                payload=v.to_dict(),
            )
            for k, v in st.session_df.iterrows()
        ],
    )


with colA:
    zakres_ocen = st.radio("Wybierz zakres ocen rekomendowanych miejsc (średnia na Google Maps)", ['3,5 i wyżej', '4 i wyżej', '4,5 i wyżej'], horizontal=True, index =0)
if zakres_ocen == '3,5 i wyżej':
    df_rec = st.session_df.copy()
if zakres_ocen == '4 i wyżej':
    df_rec = st.session_df[st.session_df['rating']>=4]
if zakres_ocen == '4,5 i wyżej':
    df_rec = st.session_df[st.session_df['rating']>=4.5]

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

choose__phrase = st.sidebar.text_input("Wyszukaj konkretną atrakcję (np. popularny bar / sztuka współczesna)",  "", key="placeholder")


tekst = f'''
             Po wybraniu miasta (TOP 60 miast Europy pod względem liczby ludności) generowana jest lista miejsc (atrakcji oraz 
             miejsc z jedzeniem) wraz z mapką i odnośnikami do videoblogów, w których mowa 
             o tych miejsach. Dodatkowo, po prawej stronie wyświetlane są informacje o atrakcji najbardziej dopasowanej do podanych oczekiwań📈'''

st.markdown(f"<h6 style='margin-top: -23px; text-align: left;'>{tekst}</h6>", unsafe_allow_html=True)


def zgodnosc(baza, i, choose__phrase_tr):
    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
        {"role": "system", "content": f'''
        The user provides expectations regarding the place he wants to visit. 
        The recommendation system recommends a place. Decide whether the recommendation is as expected. 
        If so return 1, if not, 0 (and nothing else)
        '''},
        {"role": "user", "content": f'''Expectation: {choose__phrase_tr},
    Description of recommended place: {baza.iloc[i, 9]}'''}
      ]
    )
    return response.choices[0].message.content 


if choose__phrase != st.session_state.previous_choose_phrase or miasto != st.session_state.previous_miasto or zakres_ocen != st.session_state.previous_zakres_ocen or>
    if choose__phrase!= '':
        with st.sidebar:
            st.write(f'✅ Szukam miejsca odpowiadającego Twoim oczekiwaniom')
        choose__phrase_tr = translate(choose__phrase)
        query_results = query_qdrant(choose__phrase_tr, 'art')
        try:
            st.session_state.choose_rec = df_rec.index[df_rec['title'] == query_results[0].payload["title"]].tolist()[0]
            if zgodnosc(df_rec, st.session_state.choose_rec, choose__phrase_tr) != '1':
                st.session_state.choose_rec = 0
                with st.sidebar:
                    st.write(f'🤖 Niestety, nie znaleziono miejsc spełniających Twoje oczekiwani)                            
        except:
            try:
                st.session_state.choose_rec = df_rec.index[df_rec['title'] == query_results[1].payload["title"]].tolist()[0]
                if zgodnosc(df_rec, st.session_state.choose_rec, choose__phrase_tr) != '1':
                    st.session_state.choose_rec = 0
                    with st.sidebar:
                        st.write(f'🤖 Niestety, nie znaleziono miejsc spełniających Twoje oczekiwania.')
            except:
                try:
                    st.session_state.choose_rec = df_rec.index[df_rec['title'] == query_results[2].payload["title"]].tolist()[0]
                    if zgodnosc(df_rec, st.session_state.choose_rec, choose__phrase_tr) != '1':
                        st.session_state.choose_rec = 0
                        with st.sidebar:
                            st.write(f'🤖 Niestety, nie znaleziono miejsc spełniających Twoje oczekiwania.')
                except:
                    try:
                    st.session_state.choose_rec = df_rec.index[df_rec['title'] == query_results[3].payload["title"]].tolist()[0]
                    if zgodnosc(df_rec, st.session_state.choose_rec, choose__phrase_tr) != '1':
                        st.session_state.choose_rec = 0
                        with st.sidebar:
                            st.write(f'🤖 Niestety, nie znaleziono miejsc spełniających Twoje oczekiwania.')
                    except:
                        try:
                            st.session_state.choose_rec = df_rec.index[df_rec['title'] == query_results[4].payload["title"]].tolist()[0]
                            if zgodnosc(df_rec, st.session_state.choose_rec, choose__phrase_tr) != '1':
                            st.session_state.choose_rec = 0
                            with st.sidebar:
                                st.write(f'🤖 Niestety, nie znaleziono miejsc spełniających Twoje oczekiwania.')
                        except:
                            with st.sidebar:
                                st.write(f'🤖 Nie znaleziono miejsc spełniających Twoje oczekiwania. Zwiększ liczbę branych pod uwagę miejsc.')
                            st.session_state.choose_rec = 0 

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
        

   



    