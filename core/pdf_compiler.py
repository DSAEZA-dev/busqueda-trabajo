import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Tuple, Optional

def sanitizar_latex(texto: str) -> str:
    """
    REQUERIMIENTO 1: Sanitiza cadenas de texto para evitar errores de sintaxis al insertarlas en LaTeX.
    Escapa caracteres especiales (&, %, $, #, _, {, }) evitando doble escape y manteniendo
    la codificación UTF-8 nativa para tildes y caracteres en español.

    Args:
        texto: Cadena de texto plano a sanitizar.

    Returns:
        str: Cadena sanitizada compatible con LaTeX.
    """
    if not isinstance(texto, str):
        return str(texto) if texto is not None else ""

    # Mapeo de reemplazos usando expresiones regulares con negative lookbehind (?<!\\)
    # para evitar doble escape si el texto ya contiene un escape válido.
    reemplazos = [
        (r'(?<!\\)&', r'\&'),
        (r'(?<!\\)%', r'\%'),
        (r'(?<!\\)\$', r'\$'),
        (r'(?<!\\)#', r'\#'),
        (r'(?<!\\)_', r'\_'),
        (r'(?<!\\)\{', r'\{'),
        (r'(?<!\\)\}', r'\}'),
        (r'~', r'\textasciitilde{}'),
        (r'\^', r'\textasciicircum{}')
    ]

    texto_sanitizado = texto
    for patron, reemplazo in reemplazos:
        texto_sanitizado = re.sub(patron, reemplazo, texto_sanitizado)

    return texto_sanitizado


def _buscar_pdflatex() -> Optional[Path]:
    """
    Localiza el ejecutable pdflatex o xelatex en el PATH del sistema o en rutas habituales de MiKTeX en Windows 11.
    """
    # 1. Buscar en el PATH global
    cmd = shutil.which("pdflatex") or shutil.which("xelatex")
    if cmd:
        return Path(cmd)

    # 2. Buscar en rutas estándar de MiKTeX en Windows 11
    rutas_miktex = [
        Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe")),
        Path(os.path.expandvars(r"%PROGRAMFILES%\MiKTeX\miktex\bin\x64\pdflatex.exe")),
        Path(r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe")
    ]

    for ruta in rutas_miktex:
        if ruta.exists():
            return ruta

    return None


def compilar_cv_pdf(
    codigo_tex: str,
    nombre_salida: str = "cv_compilado",
    directorio_salida: str = "output"
) -> Tuple[Optional[Path], Optional[str]]:
    """
    REQUERIMIENTO 2 & 3: Guarda y compila código LaTeX a PDF utilizando MiKTeX/pdflatex de forma defensiva en Windows 11.

    Args:
        codigo_tex: Código fuente LaTeX (.tex) en UTF-8.
        nombre_salida: Nombre del archivo de salida sin extensión.
        directorio_salida: Carpeta de destino donde se guardarán los resultados.

    Returns:
        Tuple[Optional[Path], Optional[str]]: (Ruta Path del PDF generado, Mensaje de error si falla).
    """
    try:
        dir_out = Path(directorio_salida).resolve()
        dir_out.mkdir(parents=True, exist_ok=True)

        tex_path = dir_out / f"{nombre_salida}.tex"
        pdf_path = dir_out / f"{nombre_salida}.pdf"
        log_path = dir_out / f"{nombre_salida}.log"

        # 1. Guardar código .tex asegurando UTF-8
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(codigo_tex)

        # 2. Localizar ejecutable pdflatex
        pdflatex_cmd = _buscar_pdflatex()
        if not pdflatex_cmd:
            return None, (
                "No se encontró 'pdflatex' en el sistema. Asegúrate de tener MiKTeX o TeX Live "
                "instalado y agregado a las variables de entorno de Windows."
            )

        # 3. Preparar comando defensivo (nonstopmode + halt-on-error)
        cmd = [
            str(pdflatex_cmd),
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={dir_out}",
            str(tex_path)
        ]

        # 4. Ejecutar 2 veces para resolver referencias cruzadas/paginación
        process = None
        for _ in range(2):
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=60,
                cwd=str(dir_out)
            )
            if process.returncode != 0 and not pdf_path.exists():
                break

        # 5. Si la compilación falló o no generó PDF, procesar el archivo .log
        if not pdf_path.exists() or (process and process.returncode != 0):
            error_msg = "Error de compilación en LaTeX."
            if log_path.exists():
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    log_lines = f.readlines()

                # Extraer líneas principales de error (! Undefined control sequence, ! Missing $, etc.)
                errores_latex = [linea.strip() for linea in log_lines if linea.startswith("!") or "Fatal error" in linea]
                if errores_latex:
                    error_msg = f"Errores LaTeX detectados: {' | '.join(errores_latex[:5])}"
                else:
                    ultimas_lineas = [l.strip() for l in log_lines[-15:] if l.strip()]
                    error_msg = f"Detalle de compilación log:\n" + "\n".join(ultimas_lineas)

            return None, error_msg

        # 6. Limpieza defensiva de archivos auxiliares (.aux, .log, .out, etc.)
        extensiones_limpieza = [".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk"]
        for ext in extensiones_limpieza:
            aux_file = dir_out / f"{nombre_salida}{ext}"
            if aux_file.exists():
                try:
                    aux_file.unlink()
                except Exception:
                    pass

        return pdf_path, None

    except subprocess.TimeoutExpired:
        return None, "La compilación tardó más de 60 segundos y se canceló (TimeoutExpired)."
    except Exception as e:
        return None, f"Error inesperado durante la compilación a PDF: {str(e)}"


def compilar_latex_pdf(codigo_tex: str) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Función envolvente para compatibilidad directa con el pipeline principal de Streamlit.
    Compila el código LaTeX y retorna (bytes_del_pdf, mensaje_error).
    """
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path, err = compilar_cv_pdf(codigo_tex, nombre_salida="cv_temp", directorio_salida=tmpdir)
        if pdf_path and pdf_path.exists():
            with open(pdf_path, "rb") as f:
                return f.read(), None
        return None, err or "Error al compilar el PDF."
