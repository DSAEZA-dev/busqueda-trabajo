import streamlit as st
import asyncio
import pandas as pd
import time
import json
import os

from config.settings import SIMILARITY_THRESHOLD
from config.geography import REGIONES_CHILE
from database.db_manager import init_db, save_oferta, get_history, get_user_profile, save_user_profile
from core.nlp import get_semantic_model, extraer_habilidades_base, expandir_cv_dinamico, calcular_similitud
from core.scraper import motor_multiscraping
from core.llm_evaluator import evaluar_con_ollama, analizar_perfil, generar_cv_latex, mejorar_redaccion_cv, parsear_cv_a_json
from ui.components import load_css, mostrar_tabla_ofertas, mostrar_historial

# Crear directorios si no existen
os.makedirs("database", exist_ok=True)

# Inicializar DB (Se recrea la tabla con RUT)
init_db()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Agente Buscador de Empleo", page_icon="🤖", layout="wide")
load_css()

# --- ESTADO DE LA SESIÓN ---
if "ofertas_evaluadas" not in st.session_state: st.session_state.ofertas_evaluadas = []
if "perfil_analizado" not in st.session_state: st.session_state.perfil_analizado = False
if "datos_perfil" not in st.session_state: st.session_state.datos_perfil = None
if "current_rut" not in st.session_state: st.session_state.current_rut = ""
if "cv_text" not in st.session_state: st.session_state.cv_text = ""
if "region_casa" not in st.session_state: st.session_state.region_casa = "No especificar"
if "comuna_casa" not in st.session_state: st.session_state.comuna_casa = "No especificar"
if "num_experiencias" not in st.session_state: st.session_state.num_experiencias = 1
if "num_cursos" not in st.session_state: st.session_state.num_cursos = 1

st.title("🤖 Agente Buscador de Empleo Inteligente")

tab_buscar, tab_historial = st.tabs(["🔍 Nueva Búsqueda", "📚 Historial Guardado"])

with tab_buscar:
    st.markdown("### Fase 1: Identidad y Ubicación")
    
    rut_usuario = st.text_input("Ingresa tu RUT (Requerido para iniciar)", value=st.session_state.current_rut, placeholder="Ej: 12345678-9")
    
    if rut_usuario and rut_usuario != st.session_state.current_rut:
        # Intentar cargar perfil
        perfil = get_user_profile(rut_usuario)
        st.session_state.current_rut = rut_usuario
        if perfil:
            st.session_state.region_casa = perfil.get("region_casa", "No especificar")
            st.session_state.comuna_casa = perfil.get("comuna_casa", "No especificar")
            st.session_state.cv_text = perfil.get("cv_text", "")
            st.session_state.datos_perfil = perfil.get("datos_perfil", None)
            if st.session_state.datos_perfil:
                st.session_state.perfil_analizado = True
            st.rerun()

    col_id1, col_id2 = st.columns(2)
    with col_id1:
        st.info("Ingresa tu RUT para cargar o guardar tus configuraciones.")
    with col_id2:
        reg_index = 0
        opciones_reg = ["No especificar"] + list(REGIONES_CHILE.keys())
        if st.session_state.region_casa in opciones_reg:
            reg_index = opciones_reg.index(st.session_state.region_casa)
            
        region_casa = st.selectbox("Región de tu casa (Opcional)", opciones_reg, index=reg_index)
        st.session_state.region_casa = region_casa
        
        comuna_casa = "No especificar"
        if region_casa != "No especificar":
            opciones_com = ["No especificar"] + REGIONES_CHILE[region_casa]
            com_index = 0
            if st.session_state.comuna_casa in opciones_com:
                com_index = opciones_com.index(st.session_state.comuna_casa)
            comuna_casa = st.selectbox("Comuna de tu casa (Opcional)", opciones_com, index=com_index)
            st.session_state.comuna_casa = comuna_casa
        
        direccion_casa = ""
        if region_casa != "No especificar":
            direccion_casa = f"{comuna_casa}, {region_casa}" if comuna_casa != "No especificar" else region_casa

    if rut_usuario:
        st.divider()
        st.markdown("### Fase 2: Radiografía del Perfil")
        
        if st.session_state.perfil_analizado:
            st.success("✅ Perfil cargado desde la memoria. Puedes subir un nuevo CV para sobrescribirlo, o continuar con la Fase 3.")
            
        tab_a, tab_b = st.tabs(["📄 Opción A: Subir Archivo", "🛠️ Opción B: Constructor de CV (IA)"])
        
        with tab_a:
            cv_file = st.file_uploader("Sube tu archivo de CV aquí (.txt o .md)", type=["txt", "md"])
            if cv_file:
                st.session_state.cv_text = cv_file.getvalue().decode("utf-8")
                
        with tab_b:
            st.info("Completa los campos y consolida. Luego puedes usar la IA para mejorar tu currículum.")
            
            if st.session_state.cv_text:
                if st.button("🤖 Autocompletar desde el CV subido", type="secondary"):
                    with st.spinner("Parseando CV... esto tomará unos segundos."):
                        import json
                        datos_parsed = parsear_cv_a_json(st.session_state.cv_text)
                        
                        st.session_state.b_titular = str(datos_parsed.get("titular") or "")
                        st.session_state.b_resumen = str(datos_parsed.get("resumen") or "")
                        
                        exps = datos_parsed.get("experiencias")
                        if not isinstance(exps, list): exps = []
                        if exps:
                            st.session_state.num_experiencias = len(exps)
                            for i, exp in enumerate(exps):
                                if not isinstance(exp, dict): continue
                                st.session_state[f"cargo_{i}"] = str(exp.get("cargo") or "")
                                st.session_state[f"empresa_{i}"] = str(exp.get("empresa") or "")
                                st.session_state[f"fechas_{i}"] = str(exp.get("fechas") or "")
                                
                                logros = exp.get("logros")
                                if isinstance(logros, list): logros = "\n".join(str(l) for l in logros)
                                st.session_state[f"logros_{i}"] = str(logros or "")
                                
                        cursos = datos_parsed.get("cursos")
                        if not isinstance(cursos, list): cursos = []
                        if cursos:
                            st.session_state.num_cursos = len(cursos)
                            for i, cur in enumerate(cursos):
                                if not isinstance(cur, dict): continue
                                st.session_state[f"curso_nombre_{i}"] = str(cur.get("nombre") or "")
                                st.session_state[f"institucion_{i}"] = str(cur.get("institucion") or "")
                                
                        habilidades = datos_parsed.get("habilidades")
                        if isinstance(habilidades, list): habilidades = ", ".join(str(h) for h in habilidades)
                        st.session_state.b_habilidades = str(habilidades or "")
                    st.rerun()
            
            titular = st.text_input("Titular Profesional (Ej: Ingeniero Industrial especializado en Datos)", key="b_titular")
            resumen = st.text_area("Resumen Profesional", height=100, key="b_resumen")
            
            st.markdown("#### Experiencia Laboral")
            for i in range(st.session_state.num_experiencias):
                with st.expander(f"Experiencia {i+1}", expanded=True):
                    st.text_input(f"Cargo", key=f"cargo_{i}")
                    st.text_input(f"Empresa", key=f"empresa_{i}")
                    st.text_input(f"Fechas (Ej: Mar 2022 - Actualidad)", key=f"fechas_{i}")
                    st.text_area(f"Descripción de Logros", key=f"logros_{i}")
                    
            if st.button("➕ Agregar Otra Experiencia"):
                st.session_state.num_experiencias += 1
                st.rerun()
                
            st.markdown("#### Formación y Cursos")
            for i in range(st.session_state.num_cursos):
                with st.expander(f"Curso / Certificación {i+1}", expanded=True):
                    st.text_input(f"Nombre del Curso/Título", key=f"curso_nombre_{i}")
                    st.text_input(f"Institución", key=f"institucion_{i}")
                    
            if st.button("➕ Agregar Otro Curso"):
                st.session_state.num_cursos += 1
                st.rerun()
                
            st.markdown("#### Habilidades Técnicas")
            habilidades = st.text_area("Lista tus herramientas separadas por coma (Ej: Excel, Python, Liderazgo)", key="b_habilidades")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("💾 Consolidar mi CV", use_container_width=True):
                    cv_build = f"TITULAR: {titular}\nRESUMEN: {resumen}\n\nEXPERIENCIA:\n"
                    for i in range(st.session_state.num_experiencias):
                        if st.session_state.get(f"cargo_{i}"):
                            cv_build += f"- {st.session_state.get(f'cargo_{i}')} en {st.session_state.get(f'empresa_{i}')} ({st.session_state.get(f'fechas_{i}')})\n  Logros: {st.session_state.get(f'logros_{i}')}\n"
                    cv_build += "\nFORMACIÓN:\n"
                    for i in range(st.session_state.num_cursos):
                        if st.session_state.get(f"curso_nombre_{i}"):
                            cv_build += f"- {st.session_state.get(f'curso_nombre_{i}')}, {st.session_state.get(f'institucion_{i}')}\n"
                    cv_build += f"\nHABILIDADES: {habilidades}\n"
                    
                    st.session_state.cv_text = cv_build
                    st.success("✅ CV Consolidado exitosamente. Ya puedes analizarlo.")
                    
            with col_b2:
                if st.button("🪄 Mejorar redacción con IA", type="secondary", use_container_width=True):
                    if st.session_state.cv_text:
                        with st.spinner("La IA está reescribiendo tu currículum de forma impactante..."):
                            st.session_state.cv_text = mejorar_redaccion_cv(st.session_state.cv_text)
                        st.success("✅ ¡Currículum mejorado con IA!")
                    else:
                        st.error("Primero debes 'Consolidar mi CV' o subir uno en la Opción A.")
            
            if st.session_state.cv_text:
                with st.expander("👀 Ver texto del CV Actual"):
                    st.text_area("Texto en Memoria:", st.session_state.cv_text, height=150, disabled=True)
        
        if st.session_state.cv_text:
            st.divider()
            btn_analizar = st.button("🧠 Analizar mi Perfil con IA (Ir a Fase 3)", type="primary", width='stretch')
            
            if btn_analizar:
                with st.spinner("Leyendo tu CV y estructurando posibles cargos..."):
                    st.session_state.datos_perfil = analizar_perfil(st.session_state.cv_text)
                    st.session_state.perfil_analizado = True
                    st.session_state.ofertas_evaluadas = []
                    
                    # Guardar perfil en la base de datos
                    prof = st.session_state.datos_perfil.get("profesion", "")
                    save_user_profile(rut_usuario, region_casa, comuna_casa, st.session_state.cv_text, prof, st.session_state.datos_perfil)
                    st.rerun()
                    
        if st.session_state.perfil_analizado and st.session_state.datos_perfil:
            st.divider()
            st.markdown("### Fase 3: Sugerencias Inteligentes de Cargo")
            datos = st.session_state.datos_perfil
            
            is_simulated = datos.get("is_simulated", False)
            model_used = datos.get("model_used", "Desconocido")
            
            if is_simulated:
                fallback_reason = datos.get("fallback_reason", "El servidor de IA local no respondió.")
                st.error(f"❌ **Análisis fallido:** {fallback_reason}")
            else:
                st.info(f"🧠 Análisis impulsado por el modelo **{model_used}**")
                
            profesion = datos.get("profesion", "Desconocida")
            ubicacion_cv = datos.get("ubicacion", "No detectada")
            
            if not is_simulated:
                st.success(f"🎓 **Profesión Detectada:** {profesion} | 📍 **Ubicación extraída del CV:** {ubicacion_cv}")
            
            cargos = datos.get("cargos_sugeridos", [])
            if cargos:
                # Normalizar llaves por si el LLM alucinó 'afinity' o 'affinity'
                for c in cargos:
                    afinidad_val = c.get("afinidad") or c.get("afinity") or c.get("affinity") or 0
                    c["Afinidad (%)"] = float(afinidad_val)
                    c["Cargo"] = c.get("cargo", "Desconocido")
                
                df_cargos = pd.DataFrame(cargos)[["Cargo", "Afinidad (%)"]]
                # Ordenar por afinidad
                df_cargos = df_cargos.sort_values(by="Afinidad (%)", ascending=False)
                
                st.markdown("**Top 10 cargos afines a tu perfil:**")
                st.dataframe(
                    df_cargos.style
                        .bar(subset=['Afinidad (%)'], color='#2ecc71', vmin=0, vmax=100)
                        .format({"Afinidad (%)": "{:.0f}%"}),
                    width='stretch', 
                    hide_index=True
                )
                # Mostrar Glosario Dinámico si existe
                glosario = datos.get("glosario_tecnico")
                if glosario:
                    with st.expander("🔍 Glosario Técnico Detectado (Expansión Semántica)"):
                        st.write("La IA ha detectado estas habilidades clave en tu CV y utilizará las siguientes capas de expansión para encontrar ofertas afines:")
                        for tech, capas in glosario.items():
                            st.markdown(f"**{tech}**")
                            st.markdown(f"- *Sinónimos*: {', '.join(capas.get('sinonimos', []))}")
                            st.markdown(f"- *Herramientas*: {', '.join(capas.get('herramientas', []))}")
                            st.markdown(f"- *Impacto*: {', '.join(capas.get('impacto', []))}")
                
                # Generador LaTeX
                with st.expander("📄 ¿Quieres tu CV optimizado en LaTeX para superar filtros ATS?"):
                    st.write("La IA reestructurará tu CV actual siguiendo el formato estándar de la industria (ATS-friendly).")
                    if st.button("Generar Código LaTeX"):
                        with st.spinner("Escribiendo código LaTeX..."):
                            latex_code = generar_cv_latex(st.session_state.cv_text, profesion)
                            st.download_button(
                                label="📥 Descargar archivo .tex",
                                data=latex_code,
                                file_name=f"CV_Optimizado_{profesion.replace(' ', '_')}.tex",
                                mime="text/plain"
                            )
                
                st.divider()
                st.markdown("### Fase 4: Decisión y Cacería")
                opciones_cargos = [c.get("Cargo", c.get("cargo", "Desconocido")) for c in cargos] + ["Otro (Escribir manualmente)"]
                
                cargos_seleccionados = st.multiselect(
                    "¿A qué cargos te gustaría postular hoy? (Selecciona hasta 3 en orden de prioridad)",
                    opciones_cargos,
                    max_selections=3
                )
                
                cargo_extra = ""
                if "Otro (Escribir manualmente)" in cargos_seleccionados:
                    cargo_extra = st.text_input("Escribe el cargo manual a buscar:")
                    
                st.markdown("**Ubicación Objetivo:**")
                col_loc1, col_loc2, col_loc3 = st.columns(3)
                with col_loc1:
                    modalidad = st.selectbox("Modalidad", ["Indiferente", "Presencial", "Híbrido", "Remoto"])
                with col_loc2:
                    region_post = st.selectbox("Región", ["Cualquier Región"] + list(REGIONES_CHILE.keys())) if modalidad != "Remoto" else "Remoto"
                with col_loc3:
                    comunas_post = []
                    if modalidad != "Remoto" and region_post != "Cualquier Región":
                        comunas_post = st.multiselect("Comuna (Vacío = Toda la región)", REGIONES_CHILE[region_post])
                
                lugar_postulacion = "Remoto"
                if modalidad != "Remoto":
                    if region_post == "Cualquier Región":
                        lugar_postulacion = "Chile"
                    else:
                        if comunas_post:
                            lugar_postulacion = f"{' o '.join(comunas_post)}, {region_post}"
                        else:
                            lugar_postulacion = region_post
                    
                btn_buscar = st.button("🚀 Comenzar Búsqueda Multicargo", type="primary", width='stretch')

                if btn_buscar and cargos_seleccionados and lugar_postulacion:
                    cargos_a_buscar = []
                    for c in cargos_seleccionados:
                        if c != "Otro (Escribir manualmente)":
                            if " / " in c:
                                cargos_a_buscar.extend([x.strip() for x in c.split("/")])
                            else:
                                cargos_a_buscar.append(c.strip())
                                
                    if cargo_extra:
                        if " / " in cargo_extra:
                            cargos_a_buscar.extend([x.strip() for x in cargo_extra.split("/")])
                        else:
                            cargos_a_buscar.append(cargo_extra.strip())
                        
                    # Flujo Original de Búsqueda
                    glosario_dinamico = st.session_state.datos_perfil.get("glosario_tecnico", None)
                    terminos_encontrados = extraer_habilidades_base(st.session_state.cv_text, glosario_dinamico=glosario_dinamico)
                    
                    if not terminos_encontrados:
                        st.warning("⚠️ No se detectaron términos técnicos en el CV para la expansión semántica. Se usará el texto original tal cual.")
                        cv_txt = st.session_state.cv_text
                    else:
                        cv_txt = st.session_state.cv_text
                    
                    cv_expandido, expansiones_dict, total_terminos = expandir_cv_dinamico(cv_txt, terminos_encontrados, glosario_dinamico=glosario_dinamico)
                    
                    st.markdown("### Paso 4: La Cacería Multicargo")
                    with st.spinner("Desplegando robots de búsqueda..."):
                        placeholder_scraper = st.empty()
                        ofertas_scrapeadas = []
                        urls_vistas = set()
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        for cargo_buscar in cargos_a_buscar:
                            def log_ui(msg, cur_cargo=cargo_buscar): placeholder_scraper.markdown(f"**Buscando: {cur_cargo}**\n\n{msg}")
                            ofertas_parciales = loop.run_until_complete(motor_multiscraping(cargo_buscar, log_ui))
                            
                            import unicodedata
                            def norm_text(t):
                                return unicodedata.normalize('NFKD', str(t).lower()).encode('ASCII', 'ignore').decode('utf-8')
                                
                            ofertas_filtradas_loc = []
                            for of in ofertas_parciales:
                                ubi_norm = norm_text(of.get("ubicacion", ""))
                                
                                if modalidad not in ["Remoto", "Indiferente"] and region_post != "Cualquier Región":
                                    reg_norm = norm_text(region_post)
                                    if reg_norm == "metropolitana de santiago": reg_norm = "metropolitana"
                                    elif reg_norm == "libertador general bernardo o'higgins": reg_norm = "o'higgins"
                                    elif reg_norm == "aysen del general carlos ibanez del campo": reg_norm = "aysen"
                                    elif reg_norm == "magallanes y de la antartica chilena": reg_norm = "magallanes"
                                    
                                    match = False
                                    if comunas_post:
                                        for c in comunas_post:
                                            if norm_text(c) in ubi_norm:
                                                match = True
                                                break
                                    else:
                                        # Si no hay comunas seleccionadas, al menos la region deberia coincidir (o la principal ciudad)
                                        if reg_norm in ubi_norm or norm_text(REGIONES_CHILE[region_post][0]) in ubi_norm:
                                            match = True
                                            
                                    if match:
                                        ofertas_filtradas_loc.append(of)
                                else:
                                    ofertas_filtradas_loc.append(of)
                            
                            # Filtro anti-duplicados (por URL)
                            for of in ofertas_filtradas_loc:
                                if of['url'] not in urls_vistas:
                                    urls_vistas.add(of['url'])
                                    ofertas_scrapeadas.append(of)
                                    
                        loop.close()
                    
                    st.markdown("### Paso 5: El Embudo Matemático (El Colador)")
                    modelo = get_semantic_model()
                    embedding_cv = modelo.encode(cv_expandido, convert_to_tensor=True)
                    ofertas_filtradas = []
                    ofertas_descartadas = []
                    
                    progress_bar = st.progress(0)
                    status_texto = st.empty()
                    
                    total_ofertas = len(ofertas_scrapeadas)
                    for i, oferta in enumerate(ofertas_scrapeadas):
                        status_texto.text(f"Calculando similitud cosenoidal... {i+1}/{total_ofertas}")
                        similitud = calcular_similitud(embedding_cv, oferta["descripcion"], modelo)
                        oferta["similitud_semantica"] = similitud
                        
                        # Filtro con el nuevo umbral
                        if similitud > SIMILARITY_THRESHOLD:
                            ofertas_filtradas.append(oferta)
                        else:
                            ofertas_descartadas.append(oferta)
                        progress_bar.progress((i + 1) / total_ofertas)
                        
                    status_texto.empty()
                    progress_bar.empty()
                        
                    total_descartadas = len(ofertas_descartadas)
                    candidatas = len(ofertas_filtradas)
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("📥 Ofertas Totales Extraídas", total_ofertas)
                    c2.metric("🗑️ Descartadas (Poca Similitud con CV)", total_descartadas)
                    c3.metric("🎯 Candidatas (Alta Similitud con CV)", candidatas)
                    
                    if ofertas_descartadas:
                        with st.expander(f"Ver {total_descartadas} ofertas descartadas por falta de similitud con tu CV"):
                            df_desc = pd.DataFrame(ofertas_descartadas)[["titulo", "empresa", "modalidad", "ubicacion", "portal", "similitud_semantica", "url", "fecha_publicacion"]]
                            df_desc["Similitud Semántica con tu CV"] = (df_desc["similitud_semantica"] * 100).round(2).astype(str) + "%"
                            st.dataframe(df_desc[["titulo", "empresa", "modalidad", "ubicacion", "portal", "Similitud Semántica con tu CV", "fecha_publicacion", "url"]], width='stretch', hide_index=True)
                            
                    if ofertas_filtradas:
                        with st.expander(f"Ver {candidatas} ofertas que coinciden con tu CV y pasaron a auditoría"):
                            df_cand = pd.DataFrame(ofertas_filtradas)[["titulo", "empresa", "modalidad", "ubicacion", "portal", "similitud_semantica", "url", "fecha_publicacion"]]
                            df_cand["Similitud Semántica con tu CV"] = (df_cand["similitud_semantica"] * 100).round(2).astype(str) + "%"
                            st.dataframe(df_cand[["titulo", "empresa", "modalidad", "ubicacion", "portal", "Similitud Semántica con tu CV", "fecha_publicacion", "url"]], width='stretch', hide_index=True)
                    
                    st.markdown("### Paso 6: El Juez Implacable (Auditoría con IA Local)")
                    
                    col_stop1, col_stop2 = st.columns([3, 1])
                    with col_stop1:
                        st.info("💡 **Tip de Velocidad:** Si son demasiados candidatos y no quieres esperar, puedes interrumpir el análisis.")
                    with col_stop2:
                        st.button("🛑 Detener y ver resultados parciales", key="btn_stop_audit", use_container_width=True)
                        
                    evaluacion_placeholder = st.empty()
                    
                    # Inicializar vacía y llenar incrementalmente para no perder datos si se interrumpe
                    st.session_state.ofertas_evaluadas = []
                    
                    log_text_lines = []
                    for i, oferta in enumerate(ofertas_filtradas):
                        texto_actual = "\n".join(log_text_lines[-5:])
                        evaluacion_placeholder.markdown(f"```text\n{texto_actual}\n⏳ Evaluando oferta de {oferta['empresa']}... {i}/{candidatas} completadas\n```")
                        
                        dias_antig = oferta.get("dias_antiguedad", 0)
                        evaluacion = evaluar_con_ollama(st.session_state.cv_text, oferta["descripcion"], direccion_casa, oferta.get("ubicacion", ""), dias_antiguedad=dias_antig)
                        oferta.update(evaluacion)
                        
                        st.session_state.ofertas_evaluadas.append(oferta)
                        log_text_lines.append(f"✅ {oferta['empresa']} evaluada correctamente.")
                        
                    evaluacion_placeholder.markdown(f"```text\n" + "\n".join(log_text_lines[-5:]) + f"\n✅ Auditoría completa. {candidatas}/{candidatas} completadas.\n```")
                    
                    st.session_state.ofertas_evaluadas.sort(key=lambda x: x.get("puntaje", 0), reverse=True)

            # Resultados si existen en sesión
            if st.session_state.ofertas_evaluadas:
                # Asegurar orden incluso si se interrumpió el proceso a la mitad
                st.session_state.ofertas_evaluadas.sort(key=lambda x: x.get("puntaje", 0), reverse=True)
                
                st.divider()
                st.markdown("### Paso 7: El Tablero de Comando Final")
                
                if mostrar_tabla_ofertas(st.session_state.ofertas_evaluadas):
                    for idx, oferta in enumerate(st.session_state.ofertas_evaluadas):
                        puntaje = oferta.get("puntaje", 0)
                        emoji_score = "🌟" if puntaje >= 8 else "👍" if puntaje >= 5 else "👎"
                        cerca_badge = " 📍 ¡Muy cerca de tu casa!" if oferta.get("cerca_de_casa") else ""
                        
                        with st.expander(f"{emoji_score} {oferta['titulo']} en {oferta['empresa']} - Puntaje: {puntaje}/10 {cerca_badge}"):
                            st.write(f"**Ubicación de la oferta:** {oferta.get('ubicacion', 'No especificada')}")
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown("✅ **Por qué haces Match (Pros):**")
                                for pro in oferta.get("pros", []): st.markdown(f"- {pro}")
                            with col_b:
                                st.markdown("⚠️ **Lo que te falta (Brechas):**")
                                for falta in oferta.get("faltantes", []): st.markdown(f"- {falta}")
                                    
                            st.info(f"💡 **Consejo Táctico:**\n\n{oferta.get('consejo', 'N/A')}")
                            
                            cc1, cc2, cc3, cc4 = st.columns(4)
                            with cc1:
                                st.link_button("Ir a la postulación", oferta['url'], type="primary", use_container_width=True)
                            with cc2:
                                if st.button("👍 Relevante", key=f"up_{idx}", use_container_width=True):
                                    st.toast("Feedback guardado: Oferta Relevante")
                            with cc3:
                                if st.button("👎 Basura", key=f"down_{idx}", use_container_width=True):
                                    st.toast("Feedback guardado: Oferta Basura")
                            with cc4:
                                if st.button("💾 Guardar en BD", key=f"save_{idx}", use_container_width=True):
                                    save_oferta(rut_usuario, oferta)
                                    st.toast(f"Oferta guardada exitosamente para el RUT {rut_usuario}.")
    else:
        st.info("👈 Por favor, ingresa tu RUT para comenzar.")

with tab_historial:
    st.markdown("### Ofertas Guardadas en Base de Datos")
    rut_buscar = st.text_input("Ingresa tu RUT para ver tu historial", placeholder="Ej: 12345678-9")
    if st.button("🔄 Buscar Historial"):
        if rut_buscar:
            historial_db = get_history(rut_buscar)
            mostrar_historial(historial_db)
        else:
            st.warning("Ingresa un RUT para buscar.")
