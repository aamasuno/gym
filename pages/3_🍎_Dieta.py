# -*- coding: utf-8 -*-
"""
Created on Sat Jun 24 19:15:48 2023

@author: alvar
"""

import streamlit as st
from deta import Deta
import pypdfium2 as pdfium

st.set_page_config(layout="wide")
st.title(':green[Dieta]')
# Recuperar info usuario y key Deta de session state
deta = Deta(st.session_state["keydeta"])
username = st.session_state["username"]
# Abrir instancia DETA DRIVE para documentos
docs = deta.Drive(username.replace(" ","_")+'_docs')
# Abrir instancia DETA DRIVE para fotos
fotos = deta.Drive(username.replace(" ","_")+'_fotos')

try:
    pdf = pdfium.PdfDocument(docs.get(username+'.pdf').read())
    n_pages = len(pdf)
    for page_number in range(n_pages):
        page = pdf.get_page(page_number)
        pil_image = page.render(scale=1).to_pil()
        st.image(pil_image)
    
    st.download_button(label="Descargar control de medidas y dieta en PDF", 
             data=docs.get(username+'.pdf').read(),
             file_name=username+'.pdf',
             mime='application/octet-stream')
except:
    st.error("No se ha encontrado datos de medidas. Por favor, sube el PDF correspondiente en el apartado 'Subir Archivos'.")