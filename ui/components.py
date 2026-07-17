import streamlit as st
import pandas as pd
import json

def load_css():
    try:
        with open("ui/styles.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def mostrar_tabla_ofertas(ofertas_filtradas):
    df_mostrar = pd.DataFrame(ofertas_filtradas)
    if df_mostrar.empty:
        st.warning("Ninguna oferta pasó el proceso de selección.")
        return False
        
    df_tabla = df_mostrar[["titulo", "empresa", "puntaje", "url"]].copy()
    
    def highlight_top(row):
        return ['background-color: rgba(46, 204, 113, 0.2)' if row.puntaje >= 8 else '' for _ in row]
    
    st.dataframe(
        df_tabla.style.apply(highlight_top, axis=1), 
        width='stretch', 
        hide_index=True,
        column_config={
            "url": st.column_config.LinkColumn("Link Oficial", display_text="Ir a la Oferta 🔗")
        }
    )
    return True

def mostrar_historial(historial):
    if not historial:
        st.info("No hay ofertas guardadas en el historial.")
        return
        
    for item in historial:
        puntaje = item['puntaje']
        emoji_score = "🌟" if puntaje >= 8 else "👍" if puntaje >= 5 else "👎"
        
        with st.expander(f"{emoji_score} {item['titulo']} en {item['empresa']} (Guardado el {item['fecha']})"):
            st.markdown(f"**URL:** {item['url']}")
            st.markdown(f"**Resumen:** {item['descripcion_breve']}")
            
            c1, c2 = st.columns(2)
            try:
                pros = json.loads(item['pros'])
                faltantes = json.loads(item['faltantes'])
            except:
                pros = [item['pros']]
                faltantes = [item['faltantes']]
                
            with c1:
                st.markdown("✅ **Pros:**")
                for p in pros: st.markdown(f"- {p}")
            with c2:
                st.markdown("⚠️ **Faltantes:**")
                for f in faltantes: st.markdown(f"- {f}")
            
            st.info(f"💡 **Consejo Táctico:**\n\n{item.get('consejo', 'N/A')}")
