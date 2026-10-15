import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Calculadora de Extrusion", layout="wide")
st.markdown("### Calculadora de Produccion - Extrusion")

@st.cache_data
def cargar_configuraciones():
    try:
        df = pd.read_excel("configuraciones.xlsx")
        df.columns = df.columns.str.strip().str.replace(' ', '').str.lower()
        if 'perc_bn' in df.columns:
            df = df.rename(columns={'perc_bn': 'perc_b'})
        if 'id' not in df.columns:
            df.insert(0, 'id', range(1, len(df) + 1))
        return df
    except Exception as e:
        st.error(f"No se pudo cargar 'configuraciones.xlsx'. Error: {e}")
        return pd.DataFrame()

df_configs = cargar_configuraciones()

if df_configs.empty:
    st.warning("No se encontraron configuraciones. Verifica que 'configuraciones.xlsx' esté en el proyecto.")
else:
    st.sidebar.markdown("#### 1. Seleccion de Configuracion")
    config_names = df_configs['nombre'].tolist()
    selected_name = st.sidebar.selectbox("Elige la medida/producto:", config_names)

    selected_id = df_configs[df_configs['nombre'] == selected_name]['id'].values[0]
    config = df_configs[df_configs['id'] == selected_id].iloc[0]

    st.sidebar.markdown("#### 2. Datos de Produccion")
    cant_bobinas = st.sidebar.number_input("Cantidad de Bobinas", min_value=1, value=10)
    long_bobina = st.sidebar.number_input("Longitud por Bobina (mts)", min_value=1, value=480)

    try:
        ancho_m = float(config['ancho_plano']) / 1000.0
        espesor_total_m = float(config['espesor_total']) / 1000000.0

        esp_a_m = espesor_total_m * (float(config['perc_a']) / 100.0)
        esp_b_m = espesor_total_m * (float(config['perc_b']) / 100.0)
        esp_c_m = espesor_total_m * (float(config['perc_c']) / 100.0)

        kg_mts_a = float(config['densidad_a']) * ancho_m * esp_a_m * 2
        kg_mts_b = float(config['densidad_b']) * ancho_m * esp_b_m * 2
        kg_mts_c = float(config['densidad_c']) * ancho_m * esp_c_m * 2

        grs_mts_total = (kg_mts_a + kg_mts_b + kg_mts_c) * 1000
        grs_min = grs_mts_total * float(config['velocidad_m_min'])
        kgrs_hora = (grs_min * 60) / 1000

        long_total = cant_bobinas * long_bobina
        total_kgrs = (long_total * grs_mts_total) / 1000
        peso_bobina = total_kgrs / cant_bobinas

        tiempo_horas_dec = total_kgrs / kgrs_hora if kgrs_hora > 0 else 0
        tiempo_horas = math.floor(tiempo_horas_dec)
        tiempo_minutos = round((tiempo_horas_dec - tiempo_horas) * 60)

        kgrs_mat_a = total_kgrs * (float(config['perc_a']) / 100.0)
        kgrs_mat_b1 = total_kgrs * (float(config['perc_b']) / 100.0) * (float(config['sub_perc_b1']) / 100.0)
        kgrs_mat_b2 = total_kgrs * (float(config['perc_b']) / 100.0) * (float(config['sub_perc_b2']) / 100.0)
        kgrs_mat_c = total_kgrs * (float(config['perc_c']) / 100.0)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Peso por Bobina", f"{peso_bobina:.3f} Kgrs")
        col2.metric("Produccion Total", f"{total_kgrs:.3f} Kgrs")
        col3.metric("Velocidad de Salida", f"{kgrs_hora:.3f} Kgrs/h")
        col4.metric("Tiempo Estimado", f"{tiempo_horas}h {tiempo_minutos}m")

        st.divider()
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("##### Desglose de Valores Teoricos")
            df_teorico = pd.DataFrame({
                "Capa": ["A", "B", "C", "TOTAL"],
                "Espesor (um)": [float(config['espesor_total']) * float(config['perc_a'])/100, 
                                  float(config['espesor_total']) * float(config['perc_b'])/100, 
                                  float(config['espesor_total']) * float(config['perc_c'])/100, 
                                  float(config['espesor_total'])],
                "grs/mts": [round(kg_mts_a*1000, 2), round(kg_mts_b*1000, 2), round(kg_mts_c*1000, 2), round(grs_mts_total, 2)]
            })
            st.dataframe(df_teorico, hide_index=True, width="stretch")

        with col_right:
            st.markdown("##### Consumo de Materia Prima")
            df_materias = pd.DataFrame({
                "Maquina": ["A", "B", "B", "C"],
                "Materia Prima": [str(config['mat_a']), str(config['mat_b1']), str(config['mat_b2']), str(config['mat_c'])],
                "Porcentaje": [f"{config['perc_a']}%", f"{config['sub_perc_b1']}% (del B)", f"{config['sub_perc_b2']}% (del B)", f"{config['perc_c']}%"],
                "Consumo (Kgrs)": [round(kgrs_mat_a, 3), round(kgrs_mat_b1, 3), round(kgrs_mat_b2, 3), round(kgrs_mat_c, 3)]
            })
            st.dataframe(df_materias, hide_index=True, width="stretch")

        if 'kgrs_mts_tot' in config and 'kgrs_min_tot' in config:
            with st.expander("Ver valores de referencia"):
                col_ref1, col_ref2 = st.columns(2)
                col_ref1.metric("kgrs/mts", f"{float(config['kgrs_mts_tot']):.5f}")
                col_ref2.metric("kgrs/min", f"{float(config['kgrs_min_tot']):.5f}")

    except KeyError as e:
        st.error(f"Falta la columna '{e}' en el Excel.")
    except Exception as e:
        st.error(f"Error en el calculo: {e}")