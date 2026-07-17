import asyncio
import re
from playwright.async_api import async_playwright

async def scraper_computrabajo(cargo_buscado, log_callback, p):
    ofertas = []
    base_url = "https://cl.computrabajo.com"
    cargo_encoded = cargo_buscado.replace(" ", "-").lower()
    search_url = f"{base_url}/trabajo-de-{cargo_encoded}"
    
    log_callback(f"⏳ **[Computrabajo] Buscando...**")
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    page.set_default_timeout(15000)
    
    try:
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
                    # Alternativa si no es enlace
                    emp_p = await article.query_selector('p.dFlex')
                    empresa_el = emp_p
                empresa = await empresa_el.inner_text() if empresa_el else "Confidencial"
                # Ubicacion
                loc_el = await article.query_selector('p.fs16.fc_base.mt5 span.mr10')
                if not loc_el: loc_el = (await article.query_selector_all('p.fs16.fc_base.mt5'))[-1] if await article.query_selector_all('p.fs16.fc_base.mt5') else None
                ubicacion = await loc_el.inner_text() if loc_el else "Chile"
                # Modalidad
                # Computrabajo a veces pone la modalidad en un tag span con clase 'tag'
                tags_el = await article.query_selector_all('span.tag')
                modalidad_oferta = "Presencial"
                for tag in tags_el:
                    tag_text = await tag.inner_text()
                    if "Híbrido" in tag_text or "Hibrido" in tag_text:
                        modalidad_oferta = "Híbrido"
                    elif "Remoto" in tag_text:
                        modalidad_oferta = "Remoto"
                
                # Si no está en tags, chequear la ubicación
                if "remoto" in ubicacion.lower(): modalidad_oferta = "Remoto"
                elif "híbrido" in ubicacion.lower(): modalidad_oferta = "Híbrido"
                
                # Computrabajo no muestra descripcion en la vista principal, creamos un extracto
                descripcion = f"Oferta para el cargo de {titulo.strip()} en la empresa {empresa.strip()}. Modalidad: {modalidad_oferta}. Para conocer los detalles completos y requisitos técnicos, debes ingresar al link oficial de postulación."
                
                fecha_el = await article.query_selector('p.fs13.fc_aux')
                fecha = await fecha_el.inner_text() if fecha_el else "Reciente"
                dias = 1 if "ayer" in fecha.lower() else int(re.search(r'(\d+)', fecha.lower()).group(1)) if re.search(r'(\d+)', fecha.lower()) else 40 if "más de 30" in fecha.lower() else 0
                
                ofertas.append({"titulo": titulo.strip(), "empresa": empresa.strip(), "ubicacion": ubicacion.strip(), "modalidad": modalidad_oferta, "descripcion": descripcion, "url": url, "dias_antiguedad": dias, "fecha_publicacion": fecha.strip(), "portal": "Computrabajo"})
            except: continue
    except Exception:
        log_callback("⚠️ **[Computrabajo] Anti-bots activado o bloqueado.**")
    finally:
        await browser.close()
    return ofertas

async def scraper_google_jobs(cargo_buscado, log_callback, p):
    log_callback(f"⏳ **[Google Jobs] Iniciando conexión segura...**")
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    page = await context.new_page()
    page.set_default_timeout(10000)
    try:
        await page.goto(f"https://www.google.com/search?q=empleos+de+{cargo_buscado.replace(' ', '+')}+en+chile")
        await asyncio.sleep(2)
        # Google Jobs usa selectores dinamicos, requiere API para extraccion fiable.
        # Si no logra extraer, retorna lista vacia.
        log_callback("⚠️ **[Google Jobs] Interfaz cambiada o Captcha bloqueante.**")
    except Exception:
        pass
    finally:
        await browser.close()
    return []

async def scraper_linkedin(cargo_buscado, log_callback, p):
    log_callback(f"⏳ **[LinkedIn] Evadiendo muro de log-in...**")
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    page = await context.new_page()
    page.set_default_timeout(10000)
    try:
        await page.goto(f"https://www.linkedin.com/jobs/search?keywords={cargo_buscado}&location=Chile")
        await asyncio.sleep(2)
        log_callback("⚠️ **[LinkedIn] Authwall bloqueante. Se requiere cuenta.**")
    except Exception:
        pass
    finally:
        await browser.close()
    return []

async def scraper_laborum(cargo_buscado, log_callback, p):
    log_callback(f"⏳ **[Laborum] Intentando evadir protección anti-bots (Cloudflare)...**")
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    page = await context.new_page()
    page.set_default_timeout(10000)
    try:
        await page.goto(f"https://www.laborum.cl/empleos-busqueda-{cargo_buscado.replace(' ', '-')}.html")
        await asyncio.sleep(2)
        log_callback("⚠️ **[Laborum] Acceso denegado por Cloudflare / Datadome.**")
    except Exception:
        pass
    finally:
        await browser.close()
    return []

async def scraper_trabajando(cargo_buscado, log_callback, p):
    log_callback(f"⏳ **[Trabajando.com] Conectando...**")
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    page = await context.new_page()
    page.set_default_timeout(10000)
    try:
        await page.goto(f"https://www.trabajando.cl/trabajo-empleo/?q={cargo_buscado.replace(' ', '%20')}")
        await asyncio.sleep(2)
        log_callback("⚠️ **[Trabajando.com] Arquitectura SPA detectada. Requiere emulación avanzada.**")
    except Exception:
        pass
    finally:
        await browser.close()
    return []

async def motor_multiscraping(cargo_buscado, log_callback):
    async with async_playwright() as p:
        resultados = await asyncio.gather(
            scraper_computrabajo(cargo_buscado, log_callback, p),
            scraper_google_jobs(cargo_buscado, log_callback, p),
            scraper_linkedin(cargo_buscado, log_callback, p),
            scraper_laborum(cargo_buscado, log_callback, p),
            scraper_trabajando(cargo_buscado, log_callback, p)
        )
    todas_las_ofertas = []
    for res in resultados:
        todas_las_ofertas.extend(res)
    log_callback(f"✅ **{len(todas_las_ofertas)} ofertas extraídas.**")
    return todas_las_ofertas
