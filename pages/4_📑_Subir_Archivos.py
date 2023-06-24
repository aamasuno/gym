# -*- coding: utf-8 -*-
"""
Created on Sat Jun 24 15:15:48 2023

@author: alvar
"""

import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from PIL import Image
from io import BytesIO
from deta import Deta
import io
import pdfplumber

st.set_page_config(page_title="Subir Archivos",
                   layout="wide")

seleccionado = option_menu("Escoge una opción",
    ["PDF de Control de Medidas y Dieta","Fotografias"],
    icons=['file-earmark-pdf-fill','camera-fill'], menu_icon='cloud-upload-fill',
    default_index=0)

# Recuperar info usuario y key Deta de session state
deta = Deta(st.session_state["keydeta"])
username = st.session_state["username"]
# Abrir instancia DETA DRIVE para documentos
docs = deta.Drive(username.replace(" ","_")+'_docs')
# Abrir instancia DETA DRIVE para fotos
fotos = deta.Drive(username.replace(" ","_")+'_fotos')

if seleccionado == "PDF de Control de Medidas y Dieta":
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
else:
    st.info("Selecciona las fotografías a subir. Al mostrarse la vista previa, rellena los datos solicitados y presiona finalmente el botón 'Subir Fotografías'.")
    giro=['No','90º a la izquierda', '90º a la derecha', '180º']
    posicion=['Frontal','Frontal con flexión de bíceps','Dorsal','Dorsal con flexión de bíceps','Perfil con extensión de brazos']
    postr=['frontal1','frontal2','dorsal1','dorsal2','perfil']
    vimg=[]
    vname=[]
    vext=[]
    
    uploaded_files = st.file_uploader("Elige las fotografias a subir",type=['png','jpg','jpeg'],accept_multiple_files=True)

    if uploaded_files != []:
        st.header("Vista Previa")
        col1, col2 = st.columns(2)
        k=1
        for uploaded_file in uploaded_files:
            st.subheader('Foto '+str(k))
            col1, col2 = st.columns(2)
            im = BytesIO(uploaded_file.read())
            col1.image(im)
            optgiro=col2.selectbox('¿Necesitas girar la imagen respecto a la vista actual?',options=giro,key="giro"+str(k))
            optpos=col2.selectbox('Posición',options=posicion,key="pos"+str(k))
            fecha = col2.date_input(label="Selecciona o escribe la fecha en que se ha tomado la fotografía (Fomato AAAA/MM/DD)",key="fecha"+str(k))
            
            if optgiro=='No':
                vimg.append(Image.open(im))
            elif optgiro == '90º a la izquierda':
                vimg.append(Image.open(im).transpose(Image.Transpose.ROTATE_90))
            elif optgiro == '90º a la derecha':
                vimg.append(Image.open(im).transpose(Image.Transpose.ROTATE_270))
            else:
                vimg.append(Image.open(im).transpose(Image.Transpose.ROTATE_180))
            
            vext.append(uploaded_file.name.split(".")[-1])
            vname.append(username+'_'+fecha.strftime("%Y%m%d")+'_'+postr[posicion.index(optpos)]+'.'+uploaded_file.name.split(".")[-1])
            k=k+1
        
        if st.button("Subir fotografías"):
            if uploaded_files is not None:
                for i in range(0,len(vname)):
                    buf = io.BytesIO()
                    vimg[i].save(buf,format='PNG')
                    fotos.put(vname[i],buf.getvalue())
            
                st.success("Las fotografías se han subido correctamente, podrás visualizarlas en el apartado 'Dashboard Fotos'.")