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
import pdfplumber
import plotly.graph_objects as go
import datetime
import numpy as np
from rembg import remove

st.set_page_config(layout="wide")

deta = Deta("f116q")

username="Alvaro Amasuno"

st.sidebar.title('Menú')
menu=st.sidebar.radio('Escoge una opción',['Dashboard Control de Medidas','Dashboard Fotografías','Subir PDF de Control de Medidas y Dieta','Subir Fotografías'])

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
        f.close()
        df_all= pd.read_csv(csv_name,sep=";")
        csv.close()
        df=df_all.copy()
        df[df.columns[-1]]=pd.to_datetime(df[df.columns[-1]],format="%d/%m/%Y")
        
        st.header("Elegir el período de referencia")
        
        st.info('A continuación podrás configurar el inicio del período de referencia que quieras observar.\
                Por defecto, se selecciona el día 1 del mes actual y año anterior a tu última fecha de revisión.')
        st.warning('¡Cuidado! La fecha a elegir se mostrará en formato AAAA/MM/DD. Puedes elegirla desde el menú desplegable\
                   o escribirla en el formato especificado directamente.')
        
        fini = st.date_input(label="Escoge la fecha inicial del período de referencia",
                             value=datetime.datetime(df.iloc[-1,-1].year-1,df.iloc[-1,-1].month,1),
                             max_value=df.iloc[-1,-1])
        st.success('Tu período seleccionado es: '+fini.strftime("%d/%m/%Y")+'-'+df.iloc[-1,-1].date().strftime("%d/%m/%Y")+'.')
        
        df=df[df[df.columns[-1]] >= np.datetime64(fini)]    
        
        st.header('Medidas a fecha ' + df.iloc[-1,len(df.columns)-1].strftime("%d/%m/%Y"))     
        
        # Aviso solo un registro
        if len(df)==1:
            anterior=-1
            st.warning('Solamente consta un registro en el periodo de referencia. No se mostrarán aumentos o diferencias respecto al periodo anterior.')
        else:
            anterior=-2
            st.info('Las flechas indican el aumento o disminución de la medida respecto a la fecha de la penúltima revisión: '+ df.iloc[-2,len(df.columns)-1].strftime("%d/%m/%Y") +'.')
        
        fig=go.Figure()
        k=0
        for i in range(0,2):
            for j in range(0,4):
                fig.add_trace(go.Indicator(
                    mode = "number+delta",
                    value = df.iloc[-1,k],
                    delta = {'reference':df.iloc[anterior,k]},
                    title = {'text':df.columns[k]},
                    domain = {'row':i, 'column':j}
                    ))
                k = k+1
        fig.update_layout(grid = {'rows': 2, 'columns': 4, 'pattern': "independent"})
        
        st.plotly_chart(fig,use_container_width=True)
        
        st.header('Diferencia de medidas acumulada a fecha de ' + df.iloc[-1,len(df.columns)-1].strftime("%d/%m/%Y"))
        st.info('Las flechas indican el aumento o disminución de la medida respecto al primer registro del período de referencia: '+ df.iloc[0,len(df.columns)-1].strftime("%d/%m/%Y") +'.')
        
        # Aviso solo un registro
        if anterior==-1:
            st.warning('Solamente consta un registro en el período de referencia. No se mostrará ninguna diferencia acumulada.')
        fig2=go.Figure()
        k=0
        for i in range(0,2):
            for j in range(0,4):
                fig2.add_trace(go.Indicator(
                    mode = "delta",
                    value = df.iloc[-1,k],
                    delta = {'reference':df.iloc[0,k]},
                    title = {'text':df.columns[k]},
                    domain = {'row':i, 'column':j}
                    ))
                k = k+1
        fig2.update_layout(grid = {'rows': 2, 'columns': 4, 'pattern': "independent"})
        
        st.plotly_chart(fig2,use_container_width=True)
        
    
        st.header("Gráfica interactiva de medidas en el período de referencia")
        st.info("Aprieta o haz click sobre el nombre de una medida para ocultar o mostrar su serie de datos. Si deseas ver una\
                única medida, aprieta o haz doble click en el nombre de esa medida y el resto se ocultarán automáticamente.")
        st.info("Aprieta o pasa el cursor sobre un punto de la gráfica para ver el valor númerico de todas las medidas visibles\
                en una fecha concreta.")

        fig3=go.Figure()
        for column in df.columns[0:-1]:
            fig3.add_trace(go.Scatter(x=df[df.columns[-1]],y=df[column],
                mode='lines+markers',name=column))
        fig3.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M1", tickformat="%d/%m/%Y",title_text='Fecha')
        fig3.update_yaxes(title_text='Valor de la medida')
        fig3.update_layout(hovermode="x unified",title_text="Evolución de medidas")
        st.plotly_chart(fig3,use_container_width=True)
        
        st.header('Descargas')
        st.subheader('Descargar PDF de Control de Medidas y Dieta')
        st.download_button(label="Descargar control de medidas y dieta en PDF", 
                 data=docs.get(username+'.pdf').read(),
                 file_name=username+'.pdf',
                 mime='application/octet-stream')
        st.subheader('Descargar histórico de medidas')
        st.download_button(label="Descargar histórico de medidas en CSV", 
                 data=df_all.to_csv(sep=";",index=False).encode('utf-8'),
                 file_name=username+'.csv',
                 mime='text/csv')
        st.subheader('Descargar medidas en el período de referencia')
        st.download_button(label="Descargar medidas del período de referencia en CSV", 
                 data=df.to_csv(sep=";",index=False).encode('utf-8'),
                 file_name=username+'_filtrado.csv',
                 mime='text/csv')
    else:
        st.error("No se ha encontrado datos de medidas. Por favor, sube el archivo correspondiente en el apartado 'Subir PDF de Control de Medidas y Dieta'.")

elif menu == 'Subir Fotografías':
    st.title ('Subir Fotografías')
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

elif menu=="Dashboard Fotografías":
    
    
    st.title("Dashboard Fotografías")
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
    
    
    
        
    
