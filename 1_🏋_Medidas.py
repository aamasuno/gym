# -*- coding: utf-8 -*-
"""
Created on Sat Jun 24 12:58:37 2023

@author: alvar
"""

import streamlit as st
import pandas as pd
from deta import Deta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    
    st.header(":green[Período de referencia]")
    
    st.info('A continuación podrás configurar el inicio del período de referencia que quieras observar.\
            Por defecto, se selecciona el día uno del mes actual y año anterior a tu última fecha de revisión.')
    
    fini = st.date_input(label="Escoge la fecha inicial del período de referencia (formato AAAA/MM/DD) ",
                         value=datetime.datetime(df.iloc[-1,-1].year-1,df.iloc[-1,-1].month,1),
                         max_value=df.iloc[-1,-1])
    st.success('Tu período seleccionado es: '+fini.strftime("%d/%m/%Y")+'-'+df.iloc[-1,-1].date().strftime("%d/%m/%Y")+'.')
    
    df=df[df[df.columns[-1]] >= np.datetime64(fini)]    
    
    st.header(':green[Medidas a fecha ' + df.iloc[-1,len(df.columns)-1].strftime("%d/%m/%Y")+']')     
    
    # Aviso solo un registro
    if len(df)==1:
        anterior=-1
        st.warning('Solamente consta un registro en el periodo de referencia. No se mostrarán aumentos o diferencias respecto al periodo anterior o acumulado.')
    else:
        anterior=-2
        st.info('La primera flecha indica el aumento o disminución de la medida respecto a la fecha de la\
                penúltima revisión: '+ df.iloc[-2,len(df.columns)-1].strftime("%d/%m/%Y") +'. La segunda flecha\
                indica el aumento o disminución de la medida respecto al primer registro del período \
                de referencia: '+ df.iloc[0,len(df.columns)-1].strftime("%d/%m/%Y") +'.')
    
    for i in range(len(df.columns)-1):
        st.subheader(':green['+df.columns[i]+']')
        c1,c2=st.columns([0.25,0.75])
        fig=make_subplots(rows=2,cols=1,row_heights=[0.7,0.3])
        fig.update_layout(grid = {'rows': 2, 'columns': 1, 'pattern': "independent"})
        fig.add_trace(go.Indicator(
        mode = "number+delta",
        value = df.iloc[-1,i],
        delta = {'reference':df.iloc[anterior,i]},domain={'x': [0,1], 'y': [0.3,1]}
        ))
        fig.add_trace(go.Indicator(
        mode = "delta",
        value = df.iloc[-1,i],
        delta = {'reference':df.iloc[0,i]},
        title = {'text':'Dif. acumulada'},domain={'x': [0.15,0.85], 'y': [0,0.3]}
        ))
        #fig.update_layout(grid = {'rows': 2, 'columns': 1, 'pattern': "independent"})
        c1.plotly_chart(fig,use_container_width=True)
        fig1=go.Figure()
        fig1.add_trace(go.Scatter(x=df[df.columns[-1]],y=df[df.columns[i]],
            mode='lines+markers',line_shape='spline',name=df.columns[i],line_color='rgb(0,204,102)'))
        fig1.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M1", tickformat="%d/%m/%Y",title_text='Fecha')
        if (df.columns[i]=='PESO'):
            fig1.update_yaxes(title_text='kg')
        else:
            fig1.update_yaxes(title_text='cm')
        fig1.update_layout(hovermode="x unified")
        c2.plotly_chart(fig1,use_container_width=True)
    
# Descargas   

    st.subheader(':green[Descargar histórico de medidas]')
    st.download_button(label="Descargar histórico de medidas en CSV", 
             data=df_all.to_csv(sep=";",index=False).encode('utf-8'),
             file_name=username+'.csv',
             mime='text/csv')
    st.subheader(':green[Descargar medidas en el período de referencia]')
    st.download_button(label="Descargar medidas del período de referencia en CSV", 
             data=df.to_csv(sep=";",index=False).encode('utf-8'),
             file_name=username+'_filtrado.csv',
             mime='text/csv')

else:
    st.error("No se ha encontrado datos de medidas. Por favor, sube el archivo correspondiente en el apartado 'Subir PDF de Control de Medidas y Dieta'.")

