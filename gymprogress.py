# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 21:26:12 2023

@author: alvar
"""

import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
from deta import Deta
import io
import base64
import pdfplumber
import plotly.graph_objects as go


deta = Deta("a0k3zvhe_oQqy7qtLHt2jykvZ3nu1VFaEQPY5kRRT")

username="Alvaro Amasuno"

menu=st.sidebar.radio('Escoge una opción',['Subir PDF de Control de Medidas y Dieta','Subir Fotos','Dashboard Control de Medidas','Dashboard Fotos','Ver y Descargar PDF de Control Medidas y Dieta'])

# Abrir instancia DETA DRIVE para documentos
docs = deta.Drive(username.replace(" ","_")+'_docs')
# Abrir instancia DETA DRIVE para fotos
fotos = deta.Drive(username.replace(" ","_")+'_fotos')



if menu=="Subir PDF de Control de Medidas y Dieta":
    st.title ('Subir archivo PDF de Control de Medidas y Dieta')
    uploaded_file = st.file_uploader("Elige un archivo para subir en formato PDF",type='pdf')
    
    if st.button('Subir archivo PDF de Control de Medidas y Dieta'):
        if uploaded_file is not None:
            #Subir PDF a DETA DRIVE (Da error si se hace despues de extraer las tablas)
            docs.put(uploaded_file.name,BytesIO(uploaded_file.read()))
            
            # Abrir archivo
            pdf = pdfplumber.open(uploaded_file)
            # Extraer tabla de medidas
            first_table = False
            for page in pdf.pages:
                for table in page.extract_tables(table_settings={}):
                    # Las otras tablas tienen como máximo 4 columnas
                    if len(table[0])>4:
                        if first_table == False:
                            df=pd.DataFrame(table)
                            first_table = True
                        else:
                            df2=pd.DataFrame(table)
                            df=pd.concat([df,df2],ignore_index=True)
            
            pdf.close()
            
            # Utilizar la primera fila oara definir columnas
            df.columns=df.iloc[0]
            df=df[1:]
            
            # Guardar DataFrame en CSV y subir a DETA DRIVE
            s_buf = io.StringIO()
            df.to_csv(s_buf,sep=";",index=False)
            docs.put(username+'.csv',s_buf.getvalue())
            
            # Avisar al usuario de que el archivo se ha subido correctamente
            st.success('El archivo PDF se ha subido correctamente y se han extraido las medidas correspondientes.')
            #st.info("El archivo PDF estará disponible en el apartado 'Ver y Descargar PDF de Control Medidas y Dieta'")
            st.header("Vista Previa")
            st.write('La tabla generada del control de medidas es la siguiente:')
            st.table(df)
        else:
            # Avisar al usuario que no se ha encontrado archivo
            st.warning('No se ha encontrado archivo para subir.')
    
elif menu == 'Dashboard Control de Medidas':
    
    st.title('Dashboard Control de Medidas')
    
    # Llamar a deta para coger el CSV de medidas
    csv=docs.get(username + '.csv')
    
    if csv is not None:
        
        # Cargar el archivo CSV y volcarlo en un DataFrame
        csv_name= username + ".csv"
        with open(csv_name, "wb+") as f:
            f.write(csv.read())
        df= pd.read_csv(csv_name,sep=";")
        csv.close()
    
        # fig2 = go.Figure(go.Indicator(
        #     mode = "number+delta",
        #     value = df.iloc[-1,0],
        #     title = {'text': df.columns[0]},
        #     delta = {'reference':df.iloc[-2,0]},
        #     domain = {'x': [0, 1], 'y': [0, 1]}
        # ))
        # st.plotly_chart(fig2)
        
        st.header('Medidas a fecha ' + str(df.iloc[-1,len(df.columns)-1]) )     
        st.info('Las flechas indican el aumento o disminución de la medida respecto al período anterior: '+ str(df.iloc[-2,len(df.columns)-1]) +'.')
        
        fig=go.Figure()
        k=0
        for i in range(0,2):
            for j in range(0,4):
                fig.add_trace(go.Indicator(
                    mode = "number+delta",
                    value = df.iloc[-1,k],
                    delta = {'reference':df.iloc[-2,k]},
                    title = {'text':df.columns[k]},
                    domain = {'row':i, 'column':j}
                    ))
                k = k+1
        fig.update_layout(grid = {'rows': 2, 'columns': 4, 'pattern': "independent"})
        
        st.plotly_chart(fig,use_container_width=True)
        
    else:
        st.error("No se ha encontrado datos de medidas. Por favor, sube el archivo correspondiente en el apartado 'Subir PDF de Control de Medidas y Dieta'.")

# elif menu == 'Ver y Descargar PDF de Control Medidas y Dieta':
    
#     st.title ('Ver y Descargar PDF de Control de Medidas')
#     # Aviso de visualización al usuario
#     st.info('Sólo podrás visualizar el PDF de Control de Medidas y Dieta vía web correctamente a través de ordenador.')
    
#     # Botón de descarga de PDF
#     st.download_button(label="Descargar PDF", 
#         data=docs.get(username+'.pdf').read(),
#         file_name=username+'.pdf',
#         mime='application/octet-stream')
    
#     # Visor web pdf
#     base64_pdf = base64.b64encode(docs.get(username+'.pdf').read()).decode('utf-8')
#     pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
#     st.markdown(pdf_display, unsafe_allow_html=True)