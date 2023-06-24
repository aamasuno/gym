# -*- coding: utf-8 -*-
"""
Created on Sat Jun 24 12:58:37 2023

@author: alvar
"""

import streamlit as st
import pandas as pd
from deta import Deta
import plotly.graph_objects as go
import datetime
import numpy as np

st.set_page_config(page_title="Medidas",
                   page_icon=":man-lifting-weights:",
                   layout="wide")
if "username" or "keydeta" not in st.session_state:
    st.session_state["username"] = "Alvaro Amasuno"
    st.session_state["keydeta"] = "a0k3zvhe_oQqy7qtLHt2jykvZ3nu1VFaEQPY5kRRT"

# Recuperar info usuario y key Deta de session state
deta = Deta(st.session_state["keydeta"])
username = st.session_state["username"]
# Abrir instancia DETA DRIVE para documentos
docs = deta.Drive(username.replace(" ","_")+'_docs')
# Abrir instancia DETA DRIVE para fotos
fotos = deta.Drive(username.replace(" ","_")+'_fotos')

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

