# -*- coding: utf-8 -*-
"""
Created on Sat Jun 24 15:18:43 2023

@author: alvar
"""
import streamlit as st
from PIL import Image
from deta import Deta
import datetime
from rembg import remove

st.set_page_config(layout="wide")

# Recuperar info usuario y key Deta de session state
deta = Deta(st.session_state["keydeta"])
username = st.session_state["username"]
# Abrir instancia DETA DRIVE para documentos
docs = deta.Drive(username.replace(" ","_")+'_docs')
# Abrir instancia DETA DRIVE para fotos
fotos = deta.Drive(username.replace(" ","_")+'_fotos')

# Obtener lista de fechas de las fotografias subidas
lista=[item.split("_")[1] for item in fotos.list()["names"]]
posicion=['Frontal','Frontal con flexión de bíceps','Dorsal','Dorsal con flexión de bíceps','Perfil con extensión de brazos']
postr=['frontal1','frontal2','dorsal1','dorsal2','perfil']

if len(lista)==0:
    st.error('No se han encontrado fotografías que mostrar.')
else:
    # Obtener lista de fechas en formato AAAAMMDD y DD/MM/AAAA
    fechas_all = [*set(lista)]
    fechas_all.sort()
    fechas_all_fmt=[item[6:]+'/'+item[4:6]+'/'+item[:4] for item in fechas_all]
    
    st.header('Opción quitar el fondo')
    st.info('Si deseas quitar el fondo a las fotografías, marca la opción que se muestra a continuación.')
    sinfondo=st.checkbox("Quitar el fondo de las fotografías.")
    st.warning('Atención: La opción quitar el fondo aumenta el tiempo en que las fotografías tardan en cargar.')
    
    st.header("Elegir el período de referencia")
    
    st.info('A continuación podrás configurar el inicio del período de referencia que quieras observar.\
            Por defecto, se selecciona el día 1 del mes actual y año anterior a tu última fecha de revisión.')
    st.warning('¡Cuidado! La fecha a elegir se mostrará en formato AAAA/MM/DD. Puedes elegirla desde el menú desplegable\
               o escribirla en el formato especificado directamente.')
    
    finiper = st.date_input(label="Escoge la fecha inicial del período de referencia",
                         value=datetime.datetime(int(fechas_all[-1][:4])-1,int(fechas_all[-1][4:6]),1),
                         max_value=datetime.datetime(int(fechas_all[-1][:4]),int(fechas_all[-1][4:6]),int(fechas_all[-1][6:])))
    st.success('Tu período seleccionado es: '+finiper.strftime("%d/%m/%Y")+'-'+fechas_all_fmt[-1]+'.')
    
    fechas= [fechas_all[i] for i in range(0,len(fechas_all)) if finiper.strftime("%Y%m%d")<=fechas_all[i]]
    fechas_fmt=[fechas_all_fmt[i] for i in range(0,len(fechas_all)) if finiper.strftime("%Y%m%d")<=fechas_all[i]]

    st.header('Comparativa de fotografías')
    if len(fechas)==1:
        st.warning("Se ha encontrado solamente una fecha de registro. Se mostraran únicamente las fotografías de esa fecha")
        for pos in postr:
            st.subheader('Vista '+posicion[postr.index(pos)])
            # No se porque pero se suben en formato .jpg en vez de .png
            foto = fotos.get(username+'_'+fechas[0]+'_'+pos+'.jpg')
            if foto is not None:
                nfoto = username+'_'+fechas[0]+'_'+pos+'.jpg'
                with open(nfoto, "wb+") as f:
                    for chunk in foto.iter_chunks(4096):
                          f.write(chunk)
                foto.close()
                col1, col2 = st.columns(2)
                col1.write(fechas_fmt[0])
                if sinfondo:
                    col1.image(remove(Image.open(nfoto)))
                else:
                    col1.image(nfoto)
            else:
                st.error('No se ha encontrado la fotografia correspondiente a la posición en la fecha indicada.')
    else:
        col1, col2 = st.columns(2)
        fini=col1.selectbox("Selecciona la fecha de inicio de la comparativa",fechas_fmt[:-1])
        ffin=col2.selectbox("Selecciona la fecha de fin de la comparativa",fechas_fmt[fechas_fmt.index(fini)+1:],index=len(fechas_fmt[fechas_fmt.index(fini)+1:])-1)
        for pos in postr:
            st.subheader('Vista '+posicion[postr.index(pos)])
            foto1 = fotos.get(username+'_'+fechas[fechas_fmt.index(fini)]+'_'+pos+'.jpg')
            foto2 = fotos.get(username+'_'+fechas[fechas_fmt.index(ffin)]+'_'+pos+'.jpg')
            col1, col2 = st.columns(2)
            if foto1 is not None:
                nfoto = username+'_'+fechas[fechas_fmt.index(fini)]+'_'+pos+'.jpg'
                with open(nfoto, "wb+") as f:
                    for chunk in foto1.iter_chunks(4096):
                          f.write(chunk)
                foto1.close()
                col1.write(fini)
                if sinfondo:
                    col1.image(remove(Image.open(nfoto)))
                else:
                    col1.image(nfoto)
            else:
                col1.write(fini)
                col1.error('No se ha encontrado la fotografía correspondiente a la posición en la fecha indicada.')
            
            if foto2 is not None:
                nfoto = username+'_'+fechas[fechas_fmt.index(ffin)]+'_'+pos+'.jpg'
                with open(nfoto, "wb+") as f:
                    for chunk in foto2.iter_chunks(4096):
                          f.write(chunk)
                foto2.close()
                col2.write(ffin)
                if sinfondo:
                    col2.image(remove(Image.open(nfoto)))
                else:
                    col2.image(nfoto)
            else:
                col2.write(ffin)
                col2.error('No se ha encontrado la fotografía correspondiente a la posición en la fecha indicada.')