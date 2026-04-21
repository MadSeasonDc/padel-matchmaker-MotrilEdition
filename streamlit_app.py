import streamlit as st
import json
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io 


DATA_FILE = "padel_data.json"

JUGADORES_INICIALES = [
    "Rafa",
    "Varo",
    "Manolo",
    "Carlitos",
    "Baró"
]


LOCATIONS_INICIALES = [
    {
        "club": "Factory Fit",
        "address": "Calle Santa Leonor, 52",
        "telephone": "913 040 291",
        "whatsapp": "639 556 378",
        "email": "info@factoryfit.es",
        "inout": "Outdoor",
        "wall": "Crystal",
        "price": "12 € hasta las 14:00 / 14 € a partir de las 14:00",
        "comments": "Pista más cercana a la oficina"
    },
    {
        "club": "AQA Los Prunos",
        "address": "Avda. Los Prunos 98-100",
        "telephone": "917 43 20 01",
        "whatsapp": "N/A",
        "email": "recepcion@aqalosprunos.com",
        "inout": "All",
        "wall": "Wall",
        "price": "8,90 € interior / 6,90 € exterior",
        "comments": ""
    },
    {
        "club": "Urb. Lela",
        "address": "N/A",
        "telephone": "N/A",
        "whatsapp": "N/A",
        "email": "N/A",
        "inout": "",
        "wall": "",
        "price": "(La voluntad)",
        "comments": "Solo partidos en los que participe Lela"
    }
]



from pathlib import Path
import streamlit as st

@st.dialog("📕 Las aventuras del Result Book")
def mostrar_result_book_easter_egg():
    imagen_path = Path(__file__).parent / "assets" / "resultbookimage.png"
    st.image(imagen_path, use_container_width=True)
    st.markdown("### ¡El Result Book se resiste a ser generado!")
    st.button("Cerrar")

    
 

def avanzar_punto(puntos):
    """
    Devuelve el siguiente estado de puntos.
    """
    orden = ["0", "15", "30", "40", "AD"]
    idx = orden.index(puntos)
    return orden[min(idx + 1, len(orden) - 1)]



def procesar_punto(equipo):
    rival = "B" if equipo == "A" else "A"

    p = st.session_state.puntos
    sets = st.session_state.sets
    set_actual = st.session_state.set_actual

    # Si estamos en deuce
    if p[equipo] == "40" and p[rival] == "40":
        p[equipo] = "AD"
        return

    # Si tengo ventaja y gano punto → GANO JUEGO
    if p[equipo] == "AD":
        sets[set_actual][equipo] += 1
        p["A"] = "0"
        p["B"] = "0"
        return

    # Si el rival tenía AD → volver a deuce
    if p[rival] == "AD":
        p[rival] = "40"
        p[equipo] = "40"
        return

    # Avanzar punto normalmente
    nuevo = avanzar_punto(p[equipo])
    p[equipo] = nuevo

    # Si llego a 40 y el rival < 40 → GANO JUEGO
    if nuevo == "40" and p[rival] in ["0", "15", "30"]:
        sets[set_actual][equipo] += 1
        p["A"] = "0"
        p["B"] = "0"
        return


 

def siguiente_punto(valor_actual):
    orden = ["0", "15", "30", "40", "AD"]
    if valor_actual not in orden:
        return valor_actual
    idx = orden.index(valor_actual)
    if idx < len(orden) - 1:
        return orden[idx + 1]
    return valor_actual








def partido_tiene_jugadores_repetidos(partido):
    jugadores = []
    for pareja in ("pareja_1", "pareja_2"):
        jugadores.extend([j for j in partido.get(pareja, []) if j])
    return len(jugadores) != len(set(jugadores))



def jugadores_usados_en_otros_partidos(jornada, partido_actual):
    usados = set()
    for p in jornada.get("partidos", []):
        if p is partido_actual:
            continue
        for pareja in ("pareja_1", "pareja_2"):
            for j in p.get(pareja, []):
                if j:
                    usados.add(j)
    return usados



def calcular_ranking_rows(data):
    stats = {
        j["nombre"]: {"PJ": 0, "PG": 0, "PP": 0, "Pts": 0, "JG": 0, "JP": 0}
        for j in data["jugadores"]
    }

    for jornada in data.get("jornadas", []):
        for p in jornada.get("partidos", []):
            p1 = p.get("pareja_1", [])
            p2 = p.get("pareja_2", [])

            if len(p1) != 2 or len(p2) != 2:
                continue

            s1_p1, s1_p2 = p["set1_p1"], p["set1_p2"]
            s2_p1, s2_p2 = p["set2_p1"], p["set2_p2"]
            s3_p1, s3_p2 = p["set3_p1"], p["set3_p2"]

            if (s1_p1 + s1_p2) == 0:
                continue

            juegos_p1 = s1_p1 + s2_p1 + s3_p1
            juegos_p2 = s1_p2 + s2_p2 + s3_p2

            sets_p1 = (s1_p1 > s1_p2) + (s2_p1 > s2_p2)
            sets_p2 = (s1_p2 > s1_p1) + (s2_p2 > s2_p1)

            if (s3_p1 + s3_p2) > 0:
                ganadores = p1 if s3_p1 > s3_p2 else p2
                perdedores = p2 if ganadores == p1 else p1

                for j in ganadores:
                    stats[j]["PG"] += 1
                    stats[j]["Pts"] += 3
                for j in perdedores:
                    stats[j]["PP"] += 1
                    stats[j]["Pts"] += 1
            else:
                if sets_p1 > sets_p2:
                    for j in p1:
                        stats[j]["PG"] += 1
                        stats[j]["Pts"] += 3
                elif sets_p2 > sets_p1:
                    for j in p2:
                        stats[j]["PG"] += 1
                        stats[j]["Pts"] += 3
                else:
                    for j in p1 + p2:
                        stats[j]["Pts"] += 1

            for j in p1:
                stats[j]["PJ"] += 1
                stats[j]["JG"] += juegos_p1
                stats[j]["JP"] += juegos_p2
            for j in p2:
                stats[j]["PJ"] += 1
                stats[j]["JG"] += juegos_p2
                stats[j]["JP"] += juegos_p1

    filas = []
    for nombre, s in stats.items():
        filas.append({
            "Jugador": nombre,
            "PJ": s["PJ"],
            "PG": s["PG"],
            "PP": s["PP"],
            "Pts": s["Pts"],
            "JG": s["JG"],
            "JP": s["JP"],
            "Dif": s["JG"] - s["JP"]
        })

    filas.sort(key=lambda x: (x["Pts"], x["PG"], x["Dif"]), reverse=True)

    for i, f in enumerate(filas, start=1):
        f["RK"] = i

    return filas

def partido_vacio():
    return {
        "pareja_1": [],
        "pareja_2": [],
        "lugar": "",
        "pista": "",
        "fecha": "",
        "hora": "18:00",
        "set1_p1": 0, "set1_p2": 0,
        "set2_p1": 0, "set2_p2": 0,
        "set3_p1": 0, "set3_p2": 0
    }

def partido_con_jugadores(p1, p2):
    return {
        "pareja_1": p1,
        "pareja_2": p2,
        "lugar": "",
        "fecha": "",
        "hora": "18:00",
        "set1_p1": 0, "set1_p2": 0,
        "set2_p1": 0, "set2_p2": 0,
        "set3_p1": 0, "set3_p2": 0
    }




def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            # ----------------------------
            # JUGADORES FIJOS
            # ----------------------------
            "jugadores": [
                {
                    "nombre": nombre,
                    "disponible": False,
                    "puntos": 0,
                    "fijo": True
                }
                for nombre in JUGADORES_INICIALES
            ],

            # ----------------------------
            # JORNADAS (MAX 4)
            # ----------------------------
            "jornadas": [
                {
                    "numero": i + 1,
                    "partidos": []
                }
                for i in range(4)
            ],

            # ----------------------------
            # DATA ENTRY - ESTADÍSTICAS POR JUGADOR
            # ----------------------------
            "players_stats": {
                nombre: [] for nombre in JUGADORES_INICIALES
            },

            # ----------------------------
            # BORRADORES
            # ----------------------------
            "partidos_borrador": [],

            # ----------------------------
            # CLUBS / LOCATIONS
            # ----------------------------
            "locations": LOCATIONS_INICIALES.copy()
        }

        save_data(data)
        return data

    # --------------------------------------------------
    # SI EL ARCHIVO EXISTE → ASEGURAR ESTRUCTURA
    # --------------------------------------------------
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # ----------------------------
    # ASEGURAR JUGADORES
    # ----------------------------
    if "jugadores" not in data:
        data["jugadores"] = []

    nombres_existentes = {j["nombre"] for j in data["jugadores"]}
    for nombre in JUGADORES_INICIALES:
        if nombre not in nombres_existentes:
            data["jugadores"].append({
                "nombre": nombre,
                "disponible": False,
                "puntos": 0,
                "fijo": True
            })

    # ----------------------------
    # ASEGURAR JORNADAS (MAX 4)
    # ----------------------------
    if "jornadas" not in data:
        data["jornadas"] = []

    data["jornadas"] = data["jornadas"][:4]

    while len(data["jornadas"]) < 4:
        data["jornadas"].append({
            "numero": len(data["jornadas"]) + 1,
            "partidos": []
        })

    # ----------------------------
    # ASEGURAR DATA ENTRY
    # ----------------------------
    if "players_stats" not in data:
        data["players_stats"] = {}

    for nombre in JUGADORES_INICIALES:
        if nombre not in data["players_stats"]:
            data["players_stats"][nombre] = []

    # ----------------------------
    # BORRADORES
    # ----------------------------
    if "partidos_borrador" not in data:
        data["partidos_borrador"] = []

    # ----------------------------
    # LOCATIONS
    # ----------------------------
    if "locations" not in data or not data["locations"]:
        data["locations"] = LOCATIONS_INICIALES.copy()

    save_data(data)
    return data






def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)




from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from datetime import date
import io


def generar_pdf_results(jornada):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 2 * cm
    right = width - 2 * cm
    top = height - 2 * cm
    footer_y = 2 * cm
    y = top

    logo_path = "assets/Logo padel.png"
    logo_size = 2.0 * cm

    # =========================
    # LOGO (MISMA POSICIÓN QUE RANKING Y SCHEDULE)
    # =========================
    c.drawImage(
        ImageReader(logo_path),
        left - 0.3 * cm,
        y - logo_size + 20,
        width=logo_size,
        height=logo_size,
        mask="auto"
    )

    # =========================
    # TÍTULO
    # =========================
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(
        width / 2,
        y - 6,
        f"JORNADA {jornada['numero']} – RESULTS"
    )
    y -= 31

    # =========================
    # SUBTÍTULO
    # =========================
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, y, "Liga de Pádel Atos MEV")
    y -= 22

    # =========================
    # LÍNEA
    # =========================
    c.line(left, y, right, y)
    y -= 34

    # =========================
    # DIVISIONES
    # =========================
    for idx, partido in enumerate(jornada.get("partidos", [])):

        if y < footer_y + 125:
            c.showPage()
            y = top

            # Repetir encabezado en nueva página
            c.drawImage(
                ImageReader(logo_path),
                left - 0.3 * cm,
                y - logo_size + 20,
                width=logo_size,
                height=logo_size,
                mask="auto"
            )

            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(
                width / 2,
                y - 6,
                f"JORNADA {jornada['numero']} – RESULTS"
            )
            y -= 31

            c.setFont("Helvetica", 11)
            c.drawCentredString(width / 2, y, "Liga de Pádel Atos MEV")
            y -= 22

            c.line(left, y, right, y)
            y -= 34

        # Altura de celda (compactada)
        cell_height = 118
        cell_top = y

        # Caja
        c.rect(left, y - cell_height + 8, right - left, cell_height, stroke=1, fill=0)
        y -= 14

        # División
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left + 8, y, f"División {idx + 1}")
        y -= 12

        fecha = partido.get("fecha", "")
        hora = partido.get("hora", "")
        lugar = partido.get("lugar", "")
        pista = partido.get("pista", "")

        # Fecha / Hora
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left + 8, y, "Fecha:")
        c.setFont("Helvetica", 9)
        c.drawString(left + 45, y, fecha)

        c.setFont("Helvetica-Bold", 9)
        c.drawString(left + 230, y, "Hora:")
        c.setFont("Helvetica", 9)
        c.drawString(left + 265, y, hora)
        y -= 10

        # Lugar / Pista
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left + 8, y, "Lugar:")
        c.setFont("Helvetica", 9)
        c.drawString(left + 45, y, lugar)

        c.setFont("Helvetica-Bold", 9)
        c.drawString(left + 230, y, "Pista:")
        c.setFont("Helvetica", 9)
        c.drawString(left + 265, y, str(pista))
        y -= 14

        # =========================
        # TABLA DE SETS
        # =========================
        pareja_1 = partido.get("pareja_1", [])
        pareja_2 = partido.get("pareja_2", [])

        eq1 = " / ".join(pareja_1) if len(pareja_1) == 2 else "—"
        eq2 = " / ".join(pareja_2) if len(pareja_2) == 2 else "—"

        set1_p1 = partido.get("set1_p1", 0)
        set1_p2 = partido.get("set1_p2", 0)
        set2_p1 = partido.get("set2_p1", 0)
        set2_p2 = partido.get("set2_p2", 0)
        set3_p1 = partido.get("set3_p1", 0)
        set3_p2 = partido.get("set3_p2", 0)

        mostrar_set3 = not (set3_p1 == 0 and set3_p2 == 0)

        col_name = left + 20
        col_set1 = left + 260
        col_set2 = left + 320
        col_set3 = left + 380

        c.setFont("Helvetica-Bold", 9)
        c.drawString(col_set1, y, "Set 1")
        c.drawString(col_set2, y, "Set 2")
        if mostrar_set3:
            c.drawString(col_set3, y, "Set 3")
        y -= 9

        c.setFont("Helvetica-Bold", 9)
        c.drawString(col_name, y, eq1)
        c.setFont("Helvetica", 9)
        c.drawString(col_set1, y, str(set1_p1))
        c.drawString(col_set2, y, str(set2_p1))
        if mostrar_set3:
            c.drawString(col_set3, y, str(set3_p1))
        y -= 9

        c.setFont("Helvetica-Bold", 9)
        c.drawString(col_name, y, eq2)
        c.setFont("Helvetica", 9)
        c.drawString(col_set1, y, str(set1_p2))
        c.drawString(col_set2, y, str(set2_p2))
        if mostrar_set3:
            c.drawString(col_set3, y, str(set3_p2))

        y = cell_top - cell_height - 8

    # =========================
    # FOOTER
    # =========================
    c.setFont("Helvetica", 8)
    c.drawRightString(
        right,
        footer_y + 20,
        f"Documento generado el {date.today().strftime('%d/%m/%Y')}"
    )

    c.line(left, footer_y + 15, right, footer_y + 15)

    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(
        width / 2,
        footer_y,
        "Report provided by Manolo ©. All rights reserved."
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer



from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from datetime import date
import io


def generar_pdf_schedule(jornada):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Márgenes
    left = 2 * cm
    right = width - 2 * cm
    top = height - 2 * cm
    footer_y = 2 * cm
    y = top

    # =========================
    # LOGO (MISMA POSICIÓN QUE RANKING)
    # =========================
    logo_path = "assets/Logo padel.png"
    logo_size = 2.0 * cm

    c.drawImage(
        ImageReader(logo_path),
        left - 0.3 * cm,
        y - logo_size + 20,
        width=logo_size,
        height=logo_size,
        mask="auto"
    )

    # =========================
    # TÍTULO
    # =========================
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(
        width / 2,
        y - 6,
        f"JORNADA {jornada['numero']} – HORARIO"
    )
    y -= 31

    # =========================
    # SUBTÍTULO
    # =========================
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, y, "Liga de Pádel Atos MEV")
    y -= 22

    # =========================
    # LÍNEA
    # =========================
    c.line(left, y, right, y)
    y -= 34

    # =========================
    # DIVISIONES
    # =========================
    for idx, partido in enumerate(jornada.get("partidos", [])):

        if y < footer_y + 125:
            c.showPage()
            y = top

            c.drawImage(
                ImageReader(logo_path),
                left - 0.3 * cm,
                y - logo_size + 20,
                width=logo_size,
                height=logo_size,
                mask="auto"
            )

            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(
                width / 2,
                y - 6,
                f"JORNADA {jornada['numero']} – HORARIO"
            )
            y -= 31

            c.setFont("Helvetica", 11)
            c.drawCentredString(width / 2, y, "Liga de Pádel Empresa")
            y -= 22

            c.line(left, y, right, y)
            y -= 34

        # 🔽 Altura reducida
        cell_height = 112
        cell_top = y

        # Caja
        c.rect(left, y - cell_height + 8, right - left, cell_height, stroke=1, fill=0)
        y -= 14

        # División
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left + 8, y, f"División {idx + 1}")
        y -= 12

        fecha = partido.get("fecha", "")
        hora = partido.get("hora", "")
        lugar = partido.get("lugar", "")
        pista = partido.get("pista", "")

        # Fecha / Hora
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left + 8, y, "Fecha:")
        c.setFont("Helvetica", 9)
        c.drawString(left + 45, y, fecha)

        c.setFont("Helvetica-Bold", 9)
        c.drawString(left + 230, y, "Hora:")
        c.setFont("Helvetica", 9)
        c.drawString(left + 265, y, hora)
        y -= 10

        # Lugar / Pista
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left + 8, y, "Lugar:")
        c.setFont("Helvetica", 9)
        c.drawString(left + 45, y, lugar)

        c.setFont("Helvetica-Bold", 9)
        c.drawString(left + 230, y, "Pista:")
        c.setFont("Helvetica", 9)
        c.drawString(left + 265, y, str(pista))

        # ✅ Más aire entre datos y equipos
        y -= 22

        # =========================
        # EQUIPOS (COMPACTOS)
        # =========================
        pareja_1 = partido.get("pareja_1", [])
        pareja_2 = partido.get("pareja_2", [])

        eq1 = " / ".join(pareja_1) if len(pareja_1) == 2 else "—"
        eq2 = " / ".join(pareja_2) if len(pareja_2) == 2 else "—"

        col_A = left + 170
        col_B = left + 360
        vs_x = (col_A + col_B) / 2

        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(col_A, y, eq1)
        c.drawCentredString(vs_x, y, "vs.")
        c.drawCentredString(col_B, y, eq2)

        # 🔽 menos espacio inferior
        y = cell_top - cell_height - 8

    # =========================
    # FOOTER
    # =========================
    c.setFont("Helvetica", 8)
    c.drawRightString(
        right,
        footer_y + 20,
        f"Documento generado el {date.today().strftime('%d/%m/%Y')}"
    )

    c.line(left, footer_y + 15, right, footer_y + 15)

    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(
        width / 2,
        footer_y,
        "Report provided by Manolo ©. All rights reserved."
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from datetime import date
import io


def generar_pdf_ranking(ranking_rows):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Márgenes
    left = 2 * cm
    right = width - 2 * cm
    top = height - 2 * cm
    footer_y = 2 * cm
    y = top

    # ---------- LOGO ----------
    logo_path = "assets/Logo padel.png"
    logo_size = 2.0 * cm

    c.drawImage(
        ImageReader(logo_path),
        left - 0.3 * cm,
        y - logo_size + 20,
        width=logo_size,
        height=logo_size,
        mask="auto"
    )

    # ---------- TÍTULO ----------
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y - 6, "RANKING GENERAL")
    y -= 31

    # ---------- SUBTÍTULO ----------
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, y, "Liga de Pádel Atos MEV")
    y -= 22

    # ---------- LÍNEA ----------
    c.line(left, y, right, y)
    y -= 34

    # ---------- CABECERA DE TABLA ----------
    c.setFont("Helvetica-Bold", 9)

    headers = ["RK", "Jugador", "PJ", "PG", "PP", "Pts", "JG", "JP", "Dif"]
    col_x = [
        left,                 # RK
        left + 1.3 * cm,      # Jugador
        left + 7.6 * cm,      # PJ
        left + 9.0 * cm,      # PG
        left + 10.4 * cm,     # PP
        left + 11.8 * cm,     # Pts
        left + 13.2 * cm,     # JG
        left + 14.6 * cm,     # JP
        left + 16.0 * cm,     # Dif
    ]

    for header, x in zip(headers, col_x):
        c.drawString(x, y, header)

    y -= 12
    c.line(left, y, right, y)
    y -= 14

    # ---------- FILAS ----------
    c.setFont("Helvetica", 9)

    for row in ranking_rows:
        if y < footer_y + 40:
            c.showPage()
            y = top

        values = [
            row["RK"],
            row["Jugador"],
            row["PJ"],
            row["PG"],
            row["PP"],
            row["Pts"],
            row["JG"],
            row["JP"],
        ]

        # Pintar columnas excepto Dif
        for value, x in zip(values, col_x[:-1]):
            c.drawString(x, y, str(value))

        # Dif con signo +
        dif = row["Dif"]
        if dif > 0:
            dif_text = f"+{dif}"
        else:
            dif_text = str(dif)

        c.drawString(col_x[-1], y, dif_text)

        y -= 11

    # ---------- FOOTER ----------
    c.setFont("Helvetica", 8)
    c.drawRightString(
        right,
        footer_y + 20,
        f"Documento generado el {date.today().strftime('%d/%m/%Y')}"
    )

    c.line(left, footer_y + 15, right, footer_y + 15)

    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(
        width / 2,
        footer_y,
        "Report provided by Manolo ©. All rights reserved."
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def obtener_ranking_df(data):
    import pandas as pd

    jornadas = data.get("jornadas", [])

    # Inicializar estadísticas
    stats = {
        j["nombre"]: {
            "PJ": 0, "PG": 0, "PP": 0,
            "Pts": 0, "JG": 0, "JP": 0
        }
        for j in data["jugadores"]
    }

    for jornada in jornadas:
        for p in jornada.get("partidos", []):

            p1 = p.get("pareja_1", [])
            p2 = p.get("pareja_2", [])

            if len(p1) != 2 or len(p2) != 2:
                continue

            s1_p1, s1_p2 = p["set1_p1"], p["set1_p2"]
            s2_p1, s2_p2 = p["set2_p1"], p["set2_p2"]
            s3_p1, s3_p2 = p["set3_p1"], p["set3_p2"]

            if (s1_p1 + s1_p2) == 0:
                continue

            juegos_p1 = s1_p1 + s2_p1 + s3_p1
            juegos_p2 = s1_p2 + s2_p2 + s3_p2

            sets_p1 = (s1_p1 > s1_p2) + (s2_p1 > s2_p2)
            sets_p2 = (s1_p2 > s1_p1) + (s2_p2 > s2_p1)

            for j in p1:
                stats[j]["PJ"] += 1
                stats[j]["JG"] += juegos_p1
                stats[j]["JP"] += juegos_p2

            for j in p2:
                stats[j]["PJ"] += 1
                stats[j]["JG"] += juegos_p2
                stats[j]["JP"] += juegos_p1

            if (s3_p1 + s3_p2) > 0:
                ganadores = p1 if s3_p1 > s3_p2 else p2
                perdedores = p2 if ganadores == p1 else p1

                for j in ganadores:
                    stats[j]["PG"] += 1
                    stats[j]["Pts"] += 3
                for j in perdedores:
                    stats[j]["PP"] += 1
                    stats[j]["Pts"] += 1
            else:
                if sets_p1 > sets_p2:
                    for j in p1:
                        stats[j]["PG"] += 1
                        stats[j]["Pts"] += 3
                    for j in p2:
                        stats[j]["PP"] += 1
                elif sets_p2 > sets_p1:
                    for j in p2:
                        stats[j]["PG"] += 1
                        stats[j]["Pts"] += 3
                    for j in p1:
                        stats[j]["PP"] += 1
                else:
                    for j in p1 + p2:
                        stats[j]["Pts"] += 1

    # Convertir a DataFrame
    filas = []
    for nombre, s in stats.items():
        filas.append({
            "Jugador": nombre,
            "PJ": s["PJ"],
            "PG": s["PG"],
            "PP": s["PP"],
            "Pts": s["Pts"],
            "JG": s["JG"],
            "JP": s["JP"],
            "Dif": s["JG"] - s["JP"]
        })

    filas.sort(key=lambda x: (x["Pts"], x["PG"], x["Dif"]), reverse=True)
    df = pd.DataFrame(filas)
    df.insert(0, "RK", range(1, len(df) + 1))

    return df


data = load_data()

st.set_page_config(page_title="Pádel Matchmaker", layout="wide")
st.title("🏓 Pádel Matchmaker")













menu = st.sidebar.radio(
    "Menú",
    ["Jornadas", "Ranking", "Locations", "Import / Export", "PDF / PRINT","Data Entry"] )


def safe_index(options, value):
    return options.index(value) if value in options else 0



# ----------------------------
# JORNADAS (MOTRIL EDITION)
# ----------------------------
if menu == "Jornadas":
    import datetime

    st.header("📅 Jornadas")

    # -------- helpers seguros --------
    def safe_index(options, value):
        return options.index(value) if value in options else 0

    def ensure_pair(pair):
        if not isinstance(pair, list):
            return ["", ""]
        if len(pair) == 0:
            return ["", ""]
        if len(pair) == 1:
            return [pair[0], ""]
        return pair[:2]

    # -------- asegurar 4 jornadas --------
    if "jornadas" not in data:
        data["jornadas"] = []

    for i in range(4):
        if len(data["jornadas"]) <= i:
            data["jornadas"].append({
                "numero": i + 1,
                "partidos": []
            })

    save_data(data)

    jornada_index = st.selectbox(
        "Selecciona una jornada",
        range(4),
        format_func=lambda i: f"Jornada {data['jornadas'][i]['numero']}"
    )

    jornada = data["jornadas"][jornada_index]
    st.subheader(f"🎾 Jornada {jornada['numero']}")

    jugadores = sorted(j["nombre"] for j in data["jugadores"])
    clubs = [loc["club"] for loc in data.get("locations", [])]

    # -------- un solo partido por jornada --------
    if len(jornada["partidos"]) == 0:
        jornada["partidos"].append(partido_vacio())
        save_data(data)
        st.rerun()

    partido = jornada["partidos"][0]

    # Normalizar parejas
    partido["pareja_1"] = ensure_pair(partido.get("pareja_1"))
    partido["pareja_2"] = ensure_pair(partido.get("pareja_2"))

    with st.container(border=True):
        st.markdown("### 🎯 Partido único")

        # -------- info básica --------
        c1, c2, c3, c4 = st.columns(4)

        partido["lugar"] = c1.selectbox(
            "Lugar",
            [""] + clubs,
            index=safe_index([""] + clubs, partido.get("lugar", "")),
            key=f"j{jornada_index}_lugar"
        )

        pistas = [""] + [str(i) for i in range(1, 11)]
        partido["pista"] = c2.selectbox(
            "Pista",
            pistas,
            index=safe_index(pistas, str(partido.get("pista", ""))),
            key=f"j{jornada_index}_pista"
        )

        try:
            fecha_val = datetime.date.fromisoformat(partido.get("fecha", ""))
        except Exception:
            fecha_val = datetime.date.today()

        partido["fecha"] = str(
            c3.date_input(
                "Fecha",
                fecha_val,
                key=f"j{jornada_index}_fecha"
            )
        )

        horas = [f"{h:02d}:{m:02d}" for h in range(16, 23) for m in (0, 30)]
        partido["hora"] = c4.selectbox(
            "Hora",
            horas,
            index=safe_index(horas, partido.get("hora", "18:00")),
            key=f"j{jornada_index}_hora"
        )

        # -------- parejas --------
        opts = [""] + jugadores
        p1 = partido["pareja_1"]
        p2 = partido["pareja_2"]

        col_p1, col_p2 = st.columns(2)

        with col_p1:
            st.markdown("**Pareja 1**")
            p1d = st.selectbox(
                "Derecha",
                opts,
                index=safe_index(opts, p1[0]),
                key=f"j{jornada_index}_p1_d"
            )
            p1r = st.selectbox(
                "Revés",
                opts,
                index=safe_index(opts, p1[1]),
                key=f"j{jornada_index}_p1_r"
            )

        with col_p2:
            st.markdown("**Pareja 2**")
            p2d = st.selectbox(
                "Derecha",
                opts,
                index=safe_index(opts, p2[0]),
                key=f"j{jornada_index}_p2_d"
            )
            p2r = st.selectbox(
                "Revés",
                opts,
                index=safe_index(opts, p2[1]),
                key=f"j{jornada_index}_p2_r"
            )

        partido["pareja_1"] = [p1d, p1r]
        partido["pareja_2"] = [p2d, p2r]

        # -------- resultado --------
        st.markdown("**Resultado**")
        s1, s2, s3 = st.columns(3)

        partido["set1_p1"] = s1.number_input(
            "Set 1 P1", 0, 7, partido.get("set1_p1", 0),
            key=f"j{jornada_index}_s1p1"
        )
        partido["set1_p2"] = s1.number_input(
            "Set 1 P2", 0, 7, partido.get("set1_p2", 0),
            key=f"j{jornada_index}_s1p2"
        )

        partido["set2_p1"] = s2.number_input(
            "Set 2 P1", 0, 7, partido.get("set2_p1", 0),
            key=f"j{jornada_index}_s2p1"
        )
        partido["set2_p2"] = s2.number_input(
            "Set 2 P2", 0, 7, partido.get("set2_p2", 0),
            key=f"j{jornada_index}_s2p2"
        )

        partido["set3_p1"] = s3.number_input(
            "Set 3 P1", 0, 7, partido.get("set3_p1", 0),
            key=f"j{jornada_index}_s3p1"
        )
        partido["set3_p2"] = s3.number_input(
            "Set 3 P2", 0, 7, partido.get("set3_p2", 0),
            key=f"j{jornada_index}_s3p2"
        )

        if st.button("💾 Guardar partido", key=f"j{jornada_index}_guardar"):
            save_data(data)
            st.success("✅ Partido guardado correctamente")




# RANKING (MOTRIL EDITION)
# ----------------------------
elif menu == "Ranking":
    import pandas as pd

    st.header("🏆 Ranking")

    jornadas = data.get("jornadas", [])

    # Inicializar estadísticas para los 5 jugadores
    stats = {
        nombre: {
            "PJ": 0,
            "PG": 0,
            "PP": 0,
            "Pts": 0,
            "JG": 0,
            "JP": 0
        }
        for nombre in JUGADORES_INICIALES
    }

    # Procesar partidos
    for jornada in jornadas:
        for p in jornada.get("partidos", []):
            p1 = p.get("pareja_1", [])
            p2 = p.get("pareja_2", [])

            # Ignorar partidos incompletos
            if not p1 or not p2:
                continue
            if len(p1) != 2 or len(p2) != 2:
                continue
            if "" in p1 or "" in p2:
                continue

            s1_p1, s1_p2 = p.get("set1_p1", 0), p.get("set1_p2", 0)
            s2_p1, s2_p2 = p.get("set2_p1", 0), p.get("set2_p2", 0)
            s3_p1, s3_p2 = p.get("set3_p1", 0), p.get("set3_p2", 0)

            if (s1_p1 + s1_p2) == 0:
                continue

            juegos_p1 = s1_p1 + s2_p1 + s3_p1
            juegos_p2 = s1_p2 + s2_p2 + s3_p2

            for j in p1:
                stats[j]["PJ"] += 1
                stats[j]["JG"] += juegos_p1
                stats[j]["JP"] += juegos_p2

            for j in p2:
                stats[j]["PJ"] += 1
                stats[j]["JG"] += juegos_p2
                stats[j]["JP"] += juegos_p1

            sets_p1 = (s1_p1 > s1_p2) + (s2_p1 > s2_p2)
            sets_p2 = (s1_p2 > s1_p1) + (s2_p2 > s2_p1)

            if (s3_p1 + s3_p2) > 0:
                ganadores = p1 if s3_p1 > s3_p2 else p2
                perdedores = p2 if ganadores == p1 else p1

                for j in ganadores:
                    stats[j]["PG"] += 1
                    stats[j]["Pts"] += 3

                for j in perdedores:
                    stats[j]["PP"] += 1
                    stats[j]["Pts"] += 1
            else:
                if sets_p1 > sets_p2:
                    for j in p1:
                        stats[j]["PG"] += 1
                        stats[j]["Pts"] += 3
                    for j in p2:
                        stats[j]["PP"] += 1
                elif sets_p2 > sets_p1:
                    for j in p2:
                        stats[j]["PG"] += 1
                        stats[j]["Pts"] += 3
                    for j in p1:
                        stats[j]["PP"] += 1
                else:
                    for j in p1 + p2:
                        stats[j]["Pts"] += 1

    # Construir DataFrame
    filas = []
    for nombre, s in stats.items():
        filas.append({
            "Jugador": nombre,
            "PJ": s["PJ"],
            "PG": s["PG"],
            "PP": s["PP"],
            "Pts": s["Pts"],
            "Dif": s["JG"] - s["JP"]
        })

    filas.sort(
        key=lambda x: (x["Pts"], x["PG"], x["Dif"]),
        reverse=True
    )

    df = pd.DataFrame(filas)
    df.insert(0, "RK", range(1, len(df) + 1))

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown(
        """
### 📘 Leyenda
- **RK** → Posición  
- **PJ** → Partidos jugados  
- **PG** → Partidos ganados  
- **PP** → Partidos perdidos  
- **Pts** → Puntos  
- **Dif** → Juegos ganados − perdidos  

### 🏓 Sistema de puntuación
- Victoria → **3 puntos**
- Partido a 3 sets → **3 / 1**
- Empate → **1 punto por jugador**
"""
    )


# ----------------------------
# LOCATIONS
# ----------------------------
elif menu == "Locations":
    st.header("📍 Locations / Clubs")

    if "locations" not in data:
        data["locations"] = []

    st.markdown("### ➕ Añadir nuevo club")

    with st.expander("Añadir nuevo club"):
        club = st.text_input("Club")
        address = st.text_input("Dirección")
        telephone = st.text_input("Teléfono")
        whatsapp = st.text_input("Whatsapp")
        email = st.text_input("E-mail")
        inout = st.selectbox("In / Out", ["Indoor", "Outdoor", "All"])
        wall = st.selectbox("Crystal / Wall", ["Crystal", "Wall"])
        price = st.text_input("Precio aproximado")
        comments = st.text_input("Comentarios adicionales")

        if st.button("Guardar club"):
            if club:
                data["locations"].append({
                    "club": club,
                    "address": address,
                    "telephone": telephone,
                    "whatsapp": whatsapp,
                    "email": email,
                    "inout": inout,
                    "wall": wall,
                    "price": price,
                    "comments": comments
                })
                save_data(data)
                st.success("✅ Club añadido correctamente")
                st.rerun()
            else:
                st.error("El nombre del club es obligatorio")

    st.markdown("---")
    st.markdown("### 📋 Clubs guardados")

    if not data["locations"]:
        st.info("No hay clubs añadidos todavía")
    else:
        import pandas as pd

        df_locations = pd.DataFrame(data["locations"])
        st.dataframe(df_locations, use_container_width=True)


# ----------------------------
# IMPORT / EXPORT
# ----------------------------
elif menu == "Import / Export":
    st.header("🔄 Importar / Exportar Jornadas")

    st.markdown(
        """
        Este apartado sirve para **guardar una copia de seguridad** de las jornadas
        o **restaurarlas más adelante**.

        ✅ Incluye solo **jornadas y partidos**  
        ❌ No modifica jugadores ni locations
        """
    )

    # ----------------------------
    # EXPORTAR JORNADAS
    # ----------------------------
    st.markdown("### 📤 Exportar jornadas")

    export_data = {
        "jornadas": data.get("jornadas", [])
    }

    export_json = json.dumps(export_data, indent=4, ensure_ascii=False)

    st.download_button(
        label="⬇️ Descargar backup de jornadas",
        data=export_json,
        file_name="padel_jornadas_backup.json",
        mime="application/json"
    )

    st.markdown("---")

    # ----------------------------
    # IMPORTAR JORNADAS
    # ----------------------------
    st.markdown("### 📥 Importar jornadas")

    uploaded_file = st.file_uploader(
        "Selecciona un archivo de backup (.json)",
        type="json"
    )

    if uploaded_file is not None:
        try:
            imported_data = json.load(uploaded_file)

            if "jornadas" not in imported_data:
                st.error("❌ El archivo no contiene jornadas válidas")
            else:
                st.warning(
                    "⚠️ Esta acción sobrescribirá las jornadas actuales."
                )

                if st.button("✅ Importar y reemplazar jornadas"):
                    data["jornadas"] = imported_data["jornadas"]
                    save_data(data)
                    st.success("✅ Jornadas importadas correctamente")
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {e}") 
# ----------------------------
# PDF / PRINT
# ----------------------------
elif menu == "PDF / PRINT":
    st.header("🖨️ PDF / Print")

    # -------- RANKING PDF --------
    if st.button("🏆 Ranking PDF"):
        ranking_rows = calcular_ranking_rows(data)
        pdf_buffer = generar_pdf_ranking(ranking_rows)

        st.download_button(
            label="⬇️ Descargar Ranking PDF",
            data=pdf_buffer,
            file_name="ranking.pdf",
            mime="application/pdf"
        )

    st.markdown("---")

    # -------- SCHEDULE (SIEMPRE ABIERTO) --------
    with st.expander("📅 Schedule", expanded=True):

        col_left, col_right = st.columns([3, 1])

        with col_left:
            st.markdown("#### Jornada")
            jornadas_opciones = [f"Jornada {i}" for i in range(1, 5)]

            jornada_schedule = st.selectbox(
                "Selecciona la jornada",
                jornadas_opciones,
                key="schedule_jornada"
            )

        with col_right:
            if st.button("⚙️ Generar", key="schedule_generar"):
                jornada_num = int(jornada_schedule.split()[-1]) - 1
                jornada_data = data["jornadas"][jornada_num]

                pdf_buffer = generar_pdf_schedule(jornada_data)

                st.download_button(
                    label="⬇️ Descargar Schedule PDF",
                    data=pdf_buffer,
                    file_name=f"schedule_jornada_{jornada_data['numero']}.pdf",
                    mime="application/pdf"
                )

    # -------- RESULTS (SIEMPRE ABIERTO) --------
    with st.expander("📊 Results", expanded=True):

        col_left, col_right = st.columns([3, 1])

        with col_left:
            st.markdown("#### Jornada")
            jornadas_opciones = [f"Jornada {i}" for i in range(1, 8)]

            jornada_results = st.selectbox(
                "Selecciona la jornada",
                jornadas_opciones,
                key="results_jornada"
            )

        with col_right:
            if st.button("⚙️ Generar", key="results_generar"):
                jornada_num = int(jornada_results.split()[-1]) - 1
                jornada_data = data["jornadas"][jornada_num]

                pdf_buffer = generar_pdf_results(jornada_data)

                st.download_button(
                    label="⬇️ Descargar Results PDF",
                    data=pdf_buffer,
                    file_name=f"results_jornada_{jornada_data['numero']}.pdf",
                    mime="application/pdf"
                )

    # -------- RESULTS BOOK (EASTER EGG) --------
    st.markdown("---")

    if st.button("📕 Generate Results Book"):
        mostrar_result_book_easter_egg()



# ----------------------------
# DATA ENTRY
# ----------------------------
elif menu == "Data Entry":
    import datetime

    st.header("📊 Data Entry – Puntos del partido")

    # =========================================================
    # SESSION STATE (UNA SOLA VEZ)
    # =========================================================
    if "set_actual" not in st.session_state:
        st.session_state.set_actual = "Set 1"

    if "juego_actual" not in st.session_state:
        st.session_state.juego_actual = 1

    if "puntos_a" not in st.session_state:
        st.session_state.puntos_a = "0"

    if "puntos_b" not in st.session_state:
        st.session_state.puntos_b = "0"

    st.divider()

    # =========================================================
    # LAYOUT PRINCIPAL
    # =========================================================
    col_left, col_right = st.columns([1, 2])

    # ---------------------------------------------------------
    # IZQUIERDA – HISTÓRICO DE JUGADAS
    # ---------------------------------------------------------
    with col_left:
        st.subheader("📋 Jugadas registradas")

        todas = []
        for jug, pts in data.get("players_stats", {}).items():
            for p in pts:
                todas.append((jug, p))

        if not todas:
            st.info("Aún no hay jugadas registradas")
        else:
            for jug, p in reversed(todas[-15:]):
                st.markdown(
                    f"""
**{jug}**  
Set {p['set']} · Juego {p['game']}  
{p['accion']} → {p['detalle']}
"""
                )

    # ---------------------------------------------------------
    # DERECHA – DATA ENTRY DEL PUNTO
    # ---------------------------------------------------------
    with col_right:
        st.subheader("🎾 Registrar punto")

        # ---------- Equipo ----------
        equipo = st.radio(
            "¿Quién gana el punto?",
            ["Equipo A", "Equipo B"],
            horizontal=True
        )

        # ---------- Jugador ----------
        if equipo == "Equipo A":
            jugador = st.radio("Jugador", ["Jugador 1", "Jugador 2"], horizontal=True)
        else:
            jugador = st.radio("Jugador", ["Jugador 3", "Jugador 4"], horizontal=True)

        # ---------- Acción ----------
        accion = st.radio(
            "Tipo de punto",
            ["Saque", "Jugada", "Error del rival"],
            horizontal=True
        )

        detalle = None
        if accion == "Saque":
            detalle = st.radio("Tipo de saque", ["Directo", "Segundo saque"], horizontal=True)
        elif accion == "Jugada":
            detalle = st.radio("Tipo de jugada", ["Normal", "Globo", "Smash"], horizontal=True)
        else:
            error = st.radio("Tipo de error", ["Red", "Fuera"], horizontal=True)
            falla = st.radio(
                "Jugador que falla",
                ["Jugador 1", "Jugador 2", "Jugador 3", "Jugador 4"],
                horizontal=True
            )
            detalle = f"{error} – {falla}"

        st.divider()

        # ---------- Registrar punto ----------
        if st.button("➕ Registrar punto", use_container_width=True):
            punto = {
                "set": st.session_state.set_actual,
                "game": st.session_state.juego_actual,
                "equipo": equipo,
                "jugador": jugador,
                "accion": accion,
                "detalle": detalle,
                "timestamp": datetime.datetime.now().isoformat()
            }

            if jugador not in data["players_stats"]:
                data["players_stats"][jugador] = []

            data["players_stats"][jugador].append(punto)
            save_data(data)

            st.success("✅ Punto registrado")

    st.divider()

    # =========================================================
    # MARCADOR (DATA ENTRY)
    # =========================================================
    st.subheader("📊 Marcador")

    col_set, col_game = st.columns(2)
    with col_set:
        st.session_state.set_actual = st.selectbox(
            "Set actual",
            ["Set 1", "Set 2", "Set 3"],
            index=["Set 1", "Set 2", "Set 3"].index(st.session_state.set_actual)
        )

    with col_game:
        st.session_state.juego_actual = st.number_input(
            "Juego actual",
            min_value=1,
            max_value=30,
            value=st.session_state.juego_actual
        )

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Equipo A", st.session_state.puntos_a)
    with c2:
        st.metric("Equipo B", st.session_state.puntos_b)
