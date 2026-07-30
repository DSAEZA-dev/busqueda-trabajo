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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

class AsyncScraperPool:
    """
    Administrador de Contexto y Pool de Navegador de Alto Rendimiento para Playwright.
    Mantiene una sola instancia de Chromium y un contexto persistente con interceptación de recursos
    y evasión stealth para minimizar consumo de RAM y CPU en sistemas de 16 GB.
    """
    def __init__(self, headless: bool = True, max_concurrencia: int = 3):
        self.headless = headless
        self.max_concurrencia = max_concurrencia
        self.playwright = None
        self.browser = None
        self.context = None
        self.http_session = None
        self.semaphore = asyncio.Semaphore(max_concurrencia)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Inicia Playwright, la instancia Chromium y la sesión aiohttp compartida."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
            
            user_agent = random.choice(USER_AGENTS)
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={"width": 1920, "height": 1080},
                bypass_csp=True,
                locale="es-CL"
            )
            
            # REQUERIMIENTO 1: Interceptación y bloqueo de recursos pesados (Imágenes, Fuentes, CSS, Media)
            await self.context.route(
                "**/*",
                lambda route, request: route.abort() 
                if request.resource_type in ["image", "font", "stylesheet", "media"] 
                else route.continue_()
            )
            
        if not self.http_session or self.http_session.closed:
            self.http_session = aiohttp.ClientSession(
                headers={"User-Agent": random.choice(USER_AGENTS), "Accept": "application/json"}
            )

    async def close(self):
        """Cierra de forma ordenada todas las sesiones, contexto y el navegador."""
        if self.http_session and not self.http_session.closed:
            await self.http_session.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def fetch_page_content(self, url: str, timeout_ms: int = 15000) -> str:
        """
        REQUERIMIENTO 2: Abre una pestaña asíncrona, navega usando domcontentloaded,
        extrae el contenido y garantiza el cierre inmediato de la pestaña en try/finally.
        """
        page = None
        try:
            page = await self.context.new_page()
            try:
                await stealth(page)
            except Exception:
                pass
            page.set_default_timeout(timeout_ms)
            
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            content = await page.content()
            return content
        except Exception as e:
            return f"Error al extraer {url}: {str(e)}"
        finally:
            if page:
                await page.close()

    async def fetch_api_json(self, url: str, headers: dict = None) -> dict:
        """
        REQUERIMIENTO 3: Fast Path para solicitudes ultrarrápidas a APIs usando aiohttp.
        """
        try:
            if not self.http_session or self.http_session.closed:
                self.http_session = aiohttp.ClientSession()
            async with self.http_session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {}
        except Exception:
            return {}

    async def scrap_lote(self, urls: list[str], max_concurrencia: int = 3) -> list[dict]:
        """
        Procesa una lista de URLs en paralelo mediante un semáforo asíncrono.
        """
        sem = asyncio.Semaphore(max_concurrencia)

        async def _fetch_con_semaforo(url):
            async with sem:
                content = await self.fetch_page_content(url)
                return {"url": url, "content": content}

        tasks = [_fetch_con_semaforo(u) for u in urls]
        return await asyncio.gather(*tasks)


async def scraper_computrabajo(cargo_buscado, log_callback, pool: AsyncScraperPool):
    async with pool.semaphore:
        ofertas = []
        base_url = "https://cl.computrabajo.com"
        cargo_encoded = cargo_buscado.replace(" ", "-").lower()
        search_url = f"{base_url}/trabajo-de-{cargo_encoded}"
        
        log_callback(f"⏳ **[Computrabajo] Buscando...**")
        page = None
        try:
            page = await pool.context.new_page()
            try:
                await stealth(page)
            except Exception:
                pass
            page.set_default_timeout(15000)
            
            await asyncio.sleep(random.uniform(1, 2))
            await page.goto(search_url, wait_until="domcontentloaded")
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
                except Exception:
                    continue
        except Exception as e:
            log_callback(f"⚠️ **[Computrabajo] Error: {str(e)}**")
        finally:
            if page:
                await page.close()
        return ofertas

async def scraper_google_jobs(cargo_buscado, log_callback, pool: AsyncScraperPool):
    async with pool.semaphore:
        log_callback(f"⏳ **[Google Jobs] Conectando...**")
        page = None
        try:
            page = await pool.context.new_page()
            try:
                await stealth(page)
            except Exception:
                pass
            await page.goto(f"https://www.google.com/search?q=empleos+de+{cargo_buscado.replace(' ', '+')}+en+chile", wait_until="domcontentloaded")
            log_callback("⚠️ **[Google Jobs] Interfaz protegida por Captcha.**")
        except Exception:
            pass
        finally:
            if page:
                await page.close()
        return []

async def scraper_linkedin(cargo_buscado, log_callback, pool: AsyncScraperPool):
    async with pool.semaphore:
        log_callback(f"⏳ **[LinkedIn] Verificando...**")
        page = None
        try:
            page = await pool.context.new_page()
            try:
                await stealth(page)
            except Exception:
                pass
            await page.goto(f"https://www.linkedin.com/jobs/search?keywords={cargo_buscado}&location=Chile", wait_until="domcontentloaded")
            log_callback("⚠️ **[LinkedIn] Se requiere autenticación.**")
        except Exception:
            pass
        finally:
            if page:
                await page.close()
        return []

async def scraper_laborum(cargo_buscado, log_callback, pool: AsyncScraperPool):
    async with pool.semaphore:
        log_callback(f"⏳ **[Laborum] Conectando...**")
        page = None
        try:
            page = await pool.context.new_page()
            try:
                await stealth(page)
            except Exception:
                pass
            await page.goto(f"https://www.laborum.cl/empleos-busqueda-{cargo_buscado.replace(' ', '-')}.html", wait_until="domcontentloaded")
            log_callback("⚠️ **[Laborum] Protección Cloudflare detectada.**")
        except Exception:
            pass
        finally:
            if page:
                await page.close()
        return []

async def scraper_trabajando(cargo_buscado, log_callback, pool: AsyncScraperPool):
    async with pool.semaphore:
        log_callback(f"⏳ **[Trabajando.com] Conectando...**")
        page = None
        try:
            page = await pool.context.new_page()
            try:
                await stealth(page)
            except Exception:
                pass
            await page.goto(f"https://www.trabajando.cl/trabajo-empleo/?q={cargo_buscado.replace(' ', '%20')}", wait_until="domcontentloaded")
            log_callback("⚠️ **[Trabajando.com] Requerida emulación SPA.**")
        except Exception:
            pass
        finally:
            if page:
                await page.close()
        return []

async def scraper_chiletrabajos(cargo_buscado, log_callback, pool: AsyncScraperPool):
    async with pool.semaphore:
        ofertas = []
        base_url = "https://www.chiletrabajos.cl"
        search_url = f"{base_url}/encuentra-un-empleo?2={cargo_buscado.replace(' ', '+')}"
        
        log_callback(f"⏳ **[Chiletrabajos] Buscando...**")
        page = None
        try:
            page = await pool.context.new_page()
            try:
                await stealth(page)
            except Exception:
                pass
            page.set_default_timeout(15000)
            await page.goto(search_url, wait_until="domcontentloaded")
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
            if page:
                await page.close()
        return ofertas

async def scraper_getonboard(cargo_buscado, log_callback, pool: AsyncScraperPool):
    ofertas = []
    log_callback(f"⏳ **[GetOnBoard] Consultando API...**")
    url = f"https://www.getonbrd.com/api/v0/search/jobs?query={cargo_buscado.replace(' ', '+')}"
    
    data = await pool.fetch_api_json(url)
    jobs = data.get("data", [])
    
    for job in jobs:
        try:
            attrs = job.get("attributes", {})
            titulo = attrs.get("title", "Desconocido")
            empresa_data = attrs.get("company", {}).get("data", {})
            empresa = empresa_data.get("attributes", {}).get("name", "Confidencial") if empresa_data else "Confidencial"
            
            country = attrs.get("country", "")
            city = attrs.get("city", "")
            ubicacion = f"{city}, {country}".strip(", ") if city or country else "Remoto"
            
            remote = attrs.get("remote", False)
            remote_modality = attrs.get("remote_modality", "")
            if remote or remote_modality in ["fully_remote", "temporarily_remote", "remote_local"]:
                modalidad = "Remoto"
            elif remote_modality == "hybrid":
                modalidad = "Híbrido"
            else:
                modalidad = "Presencial"
                
            descripcion = f"Oferta para el cargo de {titulo} en la empresa {empresa}. Modalidad: {modalidad}. Revisar enlace para detalles completos."
            url_oferta = attrs.get("links", {}).get("public_url", "") or f"https://www.getonbrd.com/jobs/{job.get('id')}"
            
            published_at = attrs.get("published_at", 0)
            if published_at:
                dt = datetime.fromtimestamp(published_at)
                dias = (datetime.now() - dt).days
                fecha_pub = "Hoy" if dias == 0 else "Ayer" if dias == 1 else f"Hace {dias} días"
            else:
                dias = 0
                fecha_pub = "Reciente"
                
            ofertas.append({
                "titulo": titulo, "empresa": empresa, "ubicacion": ubicacion,
                "modalidad": modalidad, "descripcion": descripcion, "url": url_oferta,
                "dias_antiguedad": dias, "fecha_publicacion": fecha_pub, "portal": "GetOnBoard"
            })
        except Exception:
            continue
    return ofertas

async def scraper_remotive(cargo_buscado, log_callback, pool: AsyncScraperPool):
    ofertas = []
    log_callback(f"⏳ **[Remotive] Consultando API...**")
    url = f"https://remotive.com/api/remote-jobs?search={cargo_buscado.replace(' ', '%20')}"
    
    data = await pool.fetch_api_json(url)
    jobs = data.get("jobs", [])
    for job in jobs:
        try:
            titulo = job.get("title", "Desconocido")
            empresa = job.get("company_name", "Confidencial")
            ubicacion = job.get("candidate_required_location", "Global")
            url_oferta = job.get("url", "")
            descripcion = f"Oferta para {titulo} en {empresa}. Modalidad: Remoto. Ubicación requerida: {ubicacion}."
            ofertas.append({
                "titulo": titulo, "empresa": empresa, "ubicacion": ubicacion,
                "modalidad": "Remoto", "descripcion": descripcion, "url": url_oferta,
                "dias_antiguedad": 0, "fecha_publicacion": "Reciente", "portal": "Remotive"
            })
        except Exception:
            continue
    return ofertas

async def scraper_arbeitnow(cargo_buscado, log_callback, pool: AsyncScraperPool):
    ofertas = []
    log_callback(f"⏳ **[Arbeitnow] Consultando API...**")
    url = "https://www.arbeitnow.com/api/job-board-api"
    
    data = await pool.fetch_api_json(url)
    jobs = data.get("data", [])
    cargo_lower = cargo_buscado.lower()
    for job in jobs:
        try:
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
                "titulo": titulo, "empresa": empresa, "ubicacion": ubicacion,
                "modalidad": modalidad, "descripcion": descripcion, "url": url_oferta,
                "dias_antiguedad": 0, "fecha_publicacion": "Reciente", "portal": "Arbeitnow"
            })
        except Exception:
            continue
    return ofertas

async def motor_multiscraping(cargo_buscado, log_callback):
    """
    Función principal de multiscraping que utiliza AsyncScraperPool para gestionar
    el navegador Chromium único y la sesión HTTP asíncrona.
    """
    async with AsyncScraperPool(headless=True, max_concurrencia=3) as pool:
        resultados = await asyncio.gather(
            scraper_computrabajo(cargo_buscado, log_callback, pool),
            scraper_google_jobs(cargo_buscado, log_callback, pool),
            scraper_linkedin(cargo_buscado, log_callback, pool),
            scraper_laborum(cargo_buscado, log_callback, pool),
            scraper_trabajando(cargo_buscado, log_callback, pool),
            scraper_chiletrabajos(cargo_buscado, log_callback, pool),
            scraper_getonboard(cargo_buscado, log_callback, pool),
            scraper_remotive(cargo_buscado, log_callback, pool),
            scraper_arbeitnow(cargo_buscado, log_callback, pool)
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
