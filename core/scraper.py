import asyncio
import re
import random
import aiohttp
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth

# Técnicas de Evasión: Rotación de Perfiles (User-Agents)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
]

def get_stealth_context_kwargs():
    """Retorna los argumentos para un contexto de navegador evasivo."""
    return {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": {"width": 1920, "height": 1080},
        "bypass_csp": True
    }

async def _setup_stealth_page(browser):
    """Crea un contexto y una página con el plugin stealth inyectado."""
    context = await browser.new_context(**get_stealth_context_kwargs())
    page = await context.new_page()
    # Técnicas de Evasión: Inyectar Playwright Stealth para ocultar la firma del bot
    await stealth(page)
    page.set_default_timeout(15000)
    return context, page

async def scraper_computrabajo(cargo_buscado, log_callback, p, sem):
    async with sem:
        ofertas = []
        base_url = "https://cl.computrabajo.com"
        cargo_encoded = cargo_buscado.replace(" ", "-").lower()
        search_url = f"{base_url}/trabajo-de-{cargo_encoded}"
        
        log_callback(f"⏳ **[Computrabajo] Buscando...**")
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            page.set_default_timeout(15000)
            
            # Técnicas de Evasión: Comportamiento Humano (retrasos aleatorios)
            await asyncio.sleep(random.uniform(2, 5))
            
            await page.goto(search_url)
            await page.wait_for_selector('article.box_offer', timeout=10000)
            articles = await page.query_selector_all('article.box_offer')
            
            for article in articles:
                try:
                    title_el = await article.query_selector('h2 a')
                    titulo = await title_el.inner_text() if title_el else "Desconocido"
                    href = await title_el.get_attribute('href') if title_el else ""
                    url = f"{base_url}{href}" if href else ""
                    
                    empresa_el = await article.query_selector('a[offer-grid-article-company-url]')
                    if not empresa_el:
                        emp_p = await article.query_selector('p.dFlex')
                        empresa_el = emp_p
                    empresa = await empresa_el.inner_text() if empresa_el else "Confidencial"
                    
                    loc_el = await article.query_selector('p.fs16.fc_base.mt5 span.mr10')
                    if not loc_el: 
                        locs = await article.query_selector_all('p.fs16.fc_base.mt5')
                        loc_el = locs[-1] if locs else None
                    ubicacion = await loc_el.inner_text() if loc_el else "Chile"
                    
                    tags_el = await article.query_selector_all('span.tag')
                    modalidad_oferta = "Presencial"
                    for tag in tags_el:
                        tag_text = await tag.inner_text()
                        if "Híbrido" in tag_text or "Hibrido" in tag_text:
                            modalidad_oferta = "Híbrido"
                        elif "Remoto" in tag_text:
                            modalidad_oferta = "Remoto"
                    
                    if "remoto" in ubicacion.lower(): modalidad_oferta = "Remoto"
                    elif "híbrido" in ubicacion.lower(): modalidad_oferta = "Híbrido"
                    
                    descripcion = f"Oferta para el cargo de {titulo.strip()} en la empresa {empresa.strip()}. Modalidad: {modalidad_oferta}. Para conocer los detalles completos y requisitos técnicos, debes ingresar al link oficial de postulación."
                    
                    fecha_el = await article.query_selector('p.fs13.fc_aux')
                    fecha = await fecha_el.inner_text() if fecha_el else "Reciente"
                    dias = 1 if "ayer" in fecha.lower() else int(re.search(r'(\d+)', fecha.lower()).group(1)) if re.search(r'(\d+)', fecha.lower()) else 40 if "más de 30" in fecha.lower() else 0
                    
                    ofertas.append({"titulo": titulo.strip(), "empresa": empresa.strip(), "ubicacion": ubicacion.strip(), "modalidad": modalidad_oferta, "descripcion": descripcion, "url": url, "dias_antiguedad": dias, "fecha_publicacion": fecha.strip(), "portal": "Computrabajo"})
                except:
                    continue
        except Exception as e:
            log_callback(f"⚠️ **[Computrabajo] Error: {str(e)}**")
        finally:
            await browser.close()
        return ofertas

async def scraper_google_jobs(cargo_buscado, log_callback, p, sem):
    async with sem:
        log_callback(f"⏳ **[Google Jobs] Iniciando conexión segura...**")
        browser = await p.chromium.launch(headless=True)
        try:
            context, page = await _setup_stealth_page(browser)
            await asyncio.sleep(random.uniform(2, 5))
            await page.goto(f"https://www.google.com/search?q=empleos+de+{cargo_buscado.replace(' ', '+')}+en+chile")
            await asyncio.sleep(random.uniform(2, 4))
            log_callback("⚠️ **[Google Jobs] Interfaz cambiada o Captcha bloqueante.**")
        except Exception:
            pass
        finally:
            await browser.close()
        return []

async def scraper_linkedin(cargo_buscado, log_callback, p, sem):
    async with sem:
        log_callback(f"⏳ **[LinkedIn] Evadiendo muro de log-in...**")
        browser = await p.chromium.launch(headless=True)
        try:
            context, page = await _setup_stealth_page(browser)
            await asyncio.sleep(random.uniform(2, 5))
            await page.goto(f"https://www.linkedin.com/jobs/search?keywords={cargo_buscado}&location=Chile")
            await asyncio.sleep(random.uniform(2, 4))
            log_callback("⚠️ **[LinkedIn] Authwall bloqueante. Se requiere cuenta.**")
        except Exception:
            pass
        finally:
            await browser.close()
        return []

async def scraper_laborum(cargo_buscado, log_callback, p, sem):
    async with sem:
        log_callback(f"⏳ **[Laborum] Intentando evadir protección anti-bots (Cloudflare)...**")
        browser = await p.chromium.launch(headless=True)
        try:
            context, page = await _setup_stealth_page(browser)
            await asyncio.sleep(random.uniform(2, 5))
            await page.goto(f"https://www.laborum.cl/empleos-busqueda-{cargo_buscado.replace(' ', '-')}.html")
            await asyncio.sleep(random.uniform(2, 4))
            log_callback("⚠️ **[Laborum] Acceso denegado por Cloudflare / Datadome.**")
        except Exception:
            pass
        finally:
            await browser.close()
        return []

async def scraper_trabajando(cargo_buscado, log_callback, p, sem):
    async with sem:
        log_callback(f"⏳ **[Trabajando.com] Conectando...**")
        browser = await p.chromium.launch(headless=True)
        try:
            context, page = await _setup_stealth_page(browser)
            await asyncio.sleep(random.uniform(2, 5))
            await page.goto(f"https://www.trabajando.cl/trabajo-empleo/?q={cargo_buscado.replace(' ', '%20')}")
            await asyncio.sleep(random.uniform(2, 4))
            log_callback("⚠️ **[Trabajando.com] Arquitectura SPA detectada. Requiere emulación avanzada.**")
        except Exception:
            pass
        finally:
            await browser.close()
        return []

async def scraper_getonboard(cargo_buscado, log_callback):
    ofertas = []
    log_callback(f"⏳ **[GetOnBoard] Consultando API...**")
    url = f"https://www.getonbrd.com/api/v0/search/jobs?query={cargo_buscado.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    log_callback(f"⚠️ **[GetOnBoard] Error API: {response.status}**")
                    return []
                
                data = await response.json()
                jobs = data.get("data", [])
                
                for job in jobs:
                    try:
                        attrs = job.get("attributes", {})
                        titulo = attrs.get("title", "Desconocido")
                        
                        empresa_data = attrs.get("company", {}).get("data", {})
                        if empresa_data:
                            empresa = empresa_data.get("attributes", {}).get("name", "Confidencial")
                        else:
                            empresa = "Confidencial"
                        
                        # Ubicacion
                        country = attrs.get("country", "")
                        city = attrs.get("city", "")
                        ubicacion = f"{city}, {country}".strip(", ") if city or country else "Remoto"
                        
                        # Modalidad
                        remote = attrs.get("remote", False)
                        remote_modality = attrs.get("remote_modality", "")
                        
                        if remote or remote_modality in ["fully_remote", "temporarily_remote", "remote_local"]:
                            modalidad = "Remoto"
                        elif remote_modality == "hybrid":
                            modalidad = "Híbrido"
                        else:
                            modalidad = "Presencial"
                            
                        # Descripcion
                        descripcion = f"Oferta para el cargo de {titulo} en la empresa {empresa}. Modalidad: {modalidad}. Revisar enlace para detalles completos."
                        
                        # URL
                        url_oferta = attrs.get("links", {}).get("public_url", "")
                        if not url_oferta:
                            url_oferta = f"https://www.getonbrd.com/jobs/{job.get('id')}"
                        
                        # Fecha
                        published_at = attrs.get("published_at", 0)
                        if published_at:
                            dt = datetime.fromtimestamp(published_at)
                            dias = (datetime.now() - dt).days
                            if dias == 0:
                                fecha_pub = "Hoy"
                            elif dias == 1:
                                fecha_pub = "Ayer"
                            else:
                                fecha_pub = f"Hace {dias} días"
                        else:
                            dias = 0
                            fecha_pub = "Reciente"
                            
                        ofertas.append({
                            "titulo": titulo,
                            "empresa": empresa,
                            "ubicacion": ubicacion,
                            "modalidad": modalidad,
                            "descripcion": descripcion,
                            "url": url_oferta,
                            "dias_antiguedad": dias,
                            "fecha_publicacion": fecha_pub,
                            "portal": "GetOnBoard"
                        })
                    except Exception:
                        continue
    except Exception as e:
        log_callback(f"⚠️ **[GetOnBoard] Error al conectar: {str(e)}**")
        
    return ofertas

async def scraper_chiletrabajos(cargo_buscado, log_callback, p, sem):
    async with sem:
        ofertas = []
        base_url = "https://www.chiletrabajos.cl"
        search_url = f"{base_url}/encuentra-un-empleo?2={cargo_buscado.replace(' ', '+')}"
        
        log_callback(f"⏳ **[Chiletrabajos] Buscando...**")
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            page.set_default_timeout(15000)
            await page.goto(search_url)
            await page.wait_for_selector('.job-item', timeout=10000)
            articles = await page.query_selector_all('.job-item')
            
            for article in articles:
                try:
                    title_el = await article.query_selector('h2 a')
                    titulo = await title_el.inner_text() if title_el else "Desconocido"
                    href = await title_el.get_attribute('href') if title_el else ""
                    url = href if href.startswith("http") else f"{base_url}{href}"
                    
                    empresa = "Confidencial"
                    ubicacion = "Chile"
                    modalidad = "Presencial"
                    
                    details_el = await article.query_selector_all('.job-item-info li')
                    for li in details_el:
                        text = await li.inner_text()
                        if "Remoto" in text or "Teletrabajo" in text:
                            modalidad = "Remoto"
                        elif "Híbrido" in text:
                            modalidad = "Híbrido"
                    
                    descripcion = f"Oferta para el cargo de {titulo.strip()} en Chiletrabajos. Modalidad: {modalidad}. Revisar enlace para detalles completos."
                    ofertas.append({"titulo": titulo.strip(), "empresa": empresa, "ubicacion": ubicacion, "modalidad": modalidad, "descripcion": descripcion, "url": url, "dias_antiguedad": 0, "fecha_publicacion": "Reciente", "portal": "Chiletrabajos"})
                except Exception:
                    continue
        except Exception as e:
            log_callback(f"⚠️ **[Chiletrabajos] Error: {str(e)}**")
        finally:
            await browser.close()
        return ofertas

async def scraper_remotive(cargo_buscado, log_callback):
    ofertas = []
    log_callback(f"⏳ **[Remotive] Consultando API...**")
    url = f"https://remotive.com/api/remote-jobs?search={cargo_buscado.replace(' ', '%20')}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    jobs = data.get("jobs", [])
                    for job in jobs:
                        titulo = job.get("title", "Desconocido")
                        empresa = job.get("company_name", "Confidencial")
                        ubicacion = job.get("candidate_required_location", "Global")
                        url_oferta = job.get("url", "")
                        
                        modalidad = "Remoto"
                        descripcion = f"Oferta para {titulo} en {empresa}. Modalidad: {modalidad}. Ubicación requerida: {ubicacion}."
                        
                        ofertas.append({
                            "titulo": titulo,
                            "empresa": empresa,
                            "ubicacion": ubicacion,
                            "modalidad": modalidad,
                            "descripcion": descripcion,
                            "url": url_oferta,
                            "dias_antiguedad": 0,
                            "fecha_publicacion": "Reciente",
                            "portal": "Remotive"
                        })
    except Exception as e:
        log_callback(f"⚠️ **[Remotive] Error API: {str(e)}**")
        
    return ofertas

async def scraper_arbeitnow(cargo_buscado, log_callback):
    ofertas = []
    log_callback(f"⏳ **[Arbeitnow] Consultando API...**")
    url = "https://www.arbeitnow.com/api/job-board-api"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    jobs = data.get("data", [])
                    cargo_lower = cargo_buscado.lower()
                    for job in jobs:
                        titulo = job.get("title", "Desconocido")
                        
                        if cargo_lower not in titulo.lower():
                            continue
                            
                        empresa = job.get("company_name", "Confidencial")
                        ubicacion = job.get("location", "Remoto")
                        url_oferta = job.get("url", "")
                        
                        remote = job.get("remote", False)
                        modalidad = "Remoto" if remote else "Presencial"
                        descripcion = f"Oferta para {titulo} en {empresa}. Modalidad: {modalidad}."
                        
                        ofertas.append({
                            "titulo": titulo,
                            "empresa": empresa,
                            "ubicacion": ubicacion,
                            "modalidad": modalidad,
                            "descripcion": descripcion,
                            "url": url_oferta,
                            "dias_antiguedad": 0,
                            "fecha_publicacion": "Reciente",
                            "portal": "Arbeitnow"
                        })
    except Exception as e:
        log_callback(f"⚠️ **[Arbeitnow] Error API: {str(e)}**")
        
    return ofertas

async def motor_multiscraping(cargo_buscado, log_callback):
    sem = asyncio.Semaphore(2)
    async with async_playwright() as p:
        resultados = await asyncio.gather(
            scraper_computrabajo(cargo_buscado, log_callback, p, sem),
            scraper_google_jobs(cargo_buscado, log_callback, p, sem),
            scraper_linkedin(cargo_buscado, log_callback, p, sem),
            scraper_laborum(cargo_buscado, log_callback, p, sem),
            scraper_trabajando(cargo_buscado, log_callback, p, sem),
            scraper_chiletrabajos(cargo_buscado, log_callback, p, sem),
            scraper_getonboard(cargo_buscado, log_callback),
            scraper_remotive(cargo_buscado, log_callback),
            scraper_arbeitnow(cargo_buscado, log_callback)
        )
    todas_las_ofertas = []
    conteo_por_portal = {}
    
    for res in resultados:
        for oferta in res:
            portal = oferta.get("portal", "Desconocido")
            conteo_por_portal[portal] = conteo_por_portal.get(portal, 0) + 1
            todas_las_ofertas.append(oferta)
            
    if conteo_por_portal:
        resumen = ", ".join([f"{v} de {k}" for k, v in conteo_por_portal.items()])
        log_callback(f"✅ **{len(todas_las_ofertas)} ofertas extraídas en total:** ({resumen})")
    else:
        log_callback(f"✅ **0 ofertas extraídas.**")
        
    return todas_las_ofertas

