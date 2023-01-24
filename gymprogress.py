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
            st.info("El archivo PDF estará disponible en el apartado 'Ver y Descargar PDF de Control Medidas y Dieta'")
            st.header("Vista Previa")
            st.write('La tabla generada del control de medidas es la siguiente:')
            st.table(df)
        else:
            # Avisar al usuario que no se ha encontrado archivo
            st.warning('No se ha encontrado archivo para subir.')
    
elif menu == 'Ver y Descargar PDF de Control Medidas y Dieta':
    
    st.title ('Ver y Descargar PDF de Control de Medidas')
    # Aviso de visualización al usuario
    st.info('Sólo podrás visualizar el PDF de Control de Medidas y Dieta vía web correctamente a través de ordenador.')
    
    # Botón de descarga de PDF
    st.download_button(label="Descargar PDF", 
        data=docs.get(username+'.pdf').read(),
        file_name=username+'.pdf',
        mime='application/octet-stream')
    
    # Visor web pdf
    base64_pdf = base64.b64encode(docs.get(username+'.pdf').read()).decode('utf-8')
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    st.markdown(pdf_display, unsafe_allow_html=True)