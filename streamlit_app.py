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
            "jugadores": [
                {
                    "nombre": nombre,
                    "disponible": False,
                    "puntos": 0,
                    "fijo": True
                }
                for nombre in JUGADORES_INICIALES
            ],
            "jornadas": [
                {"numero": i + 1, "partidos": []}
                for i in range(7)
            ],
            "partidos_borrador": [],
            "locations": LOCATIONS_INICIALES.copy()
        }
        save_data(data)
        return data

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # Asegurar jugadores
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

    # Asegurar jornadas
    if "jornadas" not in data:
        data["jornadas"] = [{"numero": i + 1, "partidos": []} for i in range(7)]

    # Asegurar borrador
    if "partidos_borrador" not in data:
        data["partidos_borrador"] = []

    # Asegurar locations
    if "locations" not in data or len(data["locations"]) == 0:
        data["locations"] = LOCATIONS_INICIALES.copy()

    save_data(data)
    return data



def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


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
    ["Jornadas", "Ranking", "Locations", "Import / Export", "PDF / PRINT"] )


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

    # -------- un solo partido --------
    if len(jornada["partidos"]) == 0:
        jornada["partidos"].append(partido_vacio())
        save_data(data)
        st.rerun()

    partido = jornada["partidos"][0]

    # Normalizar parejas (CLAVE)
    partido["pareja_1"] = ensure_pair(partido.get("pareja_1"))
    partido["pareja_2"] = ensure_pair(partido.get("pareja_2"))

    with st.container(border=True):
        st.markdown("### 🎯 Partido único")

        # -------- info básica --------
        c1, c2, c3, c4 = st.columns(4)

        partido["lugar"] = c1.selectbox(
            "Lugar",
            [""] + clubs,
            index=safe_index([""] + clubs, partido.get("lugar", ""))
        )

        pistas = [""] + [str(i) for i in range(1, 11)]
        partido["pista"] = c2.selectbox(
            "Pista",
            pistas,
            index=safe_index(pistas, str(partido.get("pista", "")))
        )

        try:
            fecha_val = datetime.date.fromisoformat(partido.get("fecha", ""))
        except Exception:
            fecha_val = datetime.date.today()

        partido["fecha"] = str(c3.date_input("Fecha", fecha_val))

        horas = [f"{h:02d}:{m:02d}" for h in range(16, 23) for m in (0, 30)]
        partido["hora"] = c4.selectbox(
            "Hora",
            horas,
            index=safe_index(horas, partido.get("hora", "18:00"))
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
        key=f"j{jornada_index}_p1_derecha"
    )
    p1r = st.selectbox(
        "Revés",
        opts,
        index=safe_index(opts, p1[1]),
        key=f"j{jornada_index}_p1_reves"
    )

with col_p2:
    st.markdown("**Pareja 2**")
    p2d = st.selectbox(
        "Derecha",
        opts,
        index=safe_index(opts, p2[0]),
        key=f"j{jornada_index}_p2_derecha"
    )
    p2r = st.selectbox(
        "Revés",
        opts,
        index=safe_index(opts, p2[1]),
        key=f"j{jornada_index}_p2_reves"
    )

partido["pareja_1"] = [p1d, p1r]
partido["pareja_2"] = [p2d, p2r]

     # -------- resultado --------
st.markdown("**Resultado**")
s1, s2, s3 = st.columns(3)

partido["set1_p1"] = s1.number_input(
    "Set 1 P1", 0, 7, partido.get("set1_p1", 0)
)
partido["set1_p2"] = s1.number_input(
    "Set 1 P2", 0, 7, partido.get("set1_p2", 0)
)

partido["set2_p1"] = s2.number_input(
    "Set 2 P1", 0, 7, partido.get("set2_p1", 0)
)
partido["set2_p2"] = s2.number_input(
    "Set 2 P2", 0, 7, partido.get("set2_p2", 0)
)

partido["set3_p1"] = s3.number_input(
    "Set 3 P1", 0, 7, partido.get("set3_p1", 0)
)
partido["set3_p2"] = s3.number_input(
    "Set 3 P2", 0, 7, partido.get("set3_p2", 0)
)


        if st.button("💾 Guardar partido"):
            save_data(data)
            st.success("✅ Partido guardado correctamente")


# ----------------------------
# RANKING
# ----------------------------
elif menu == "Ranking":
    import pandas as pd

    st.header("🏆 Ranking")

    jornadas = data.get("jornadas", [])

    # ----------------------------
    # INICIALIZAR ESTADÍSTICAS
    # ----------------------------
    stats = {
        j["nombre"]: {
            "PJ": 0,
            "PG": 0,
            "PP": 0,
            "Pts": 0,
            "JG": 0,
            "JP": 0
        }
        for j in data["jugadores"]
    }

    # ----------------------------
    # CALCULAR ESTADÍSTICAS
    # ----------------------------
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
                if s3_p1 > s3_p2:
                    ganadores, perdedores = p1, p2
                else:
                    ganadores, perdedores = p2, p1

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

    # ----------------------------
    # DATAFRAME
    # ----------------------------
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

    # ----------------------------
    # ICONOS
    # ----------------------------
    def nombre_con_icono(row):
        nombre = row["Jugador"]
        if nombre in JUGADORES_LESIONADOS:
            nombre = f"{nombre} ➕"
        if row["RK"] == 1:
            return f"🥇 {nombre}"
        elif row["RK"] == 2:
            return f"🥈 {nombre}"
        elif row["RK"] == 3:
            return f"🥉 {nombre}"
        return nombre

    df["Jugador"] = df.apply(nombre_con_icono, axis=1)

    # ----------------------------
    # ESTILO
    # ----------------------------
    def style_row(row):
        estilos = ["" for _ in row.index]

        idx_jugador = row.index.get_loc("Jugador")
        if row["RK"] == 1:
            estilos[idx_jugador] = "background-color:#FFD700;font-weight:bold"
        elif row["RK"] == 2:
            estilos[idx_jugador] = "background-color:#C0C0C0"
        elif row["RK"] == 3:
            estilos[idx_jugador] = "background-color:#CD7F32"

        idx_dif = row.index.get_loc("Dif")
        if row["Dif"] > 0:
            estilos[idx_dif] = "color:green;font-weight:bold"
        elif row["Dif"] < 0:
            estilos[idx_dif] = "color:red;font-weight:bold"

        return estilos

    df_styled = (
        df.style
        .apply(style_row, axis=1)
        .set_properties(
            subset=["PJ", "PG", "PP", "Pts", "JG", "JP", "Dif"],
            **{"width": "55px", "text-align": "center"}
        )
        .set_properties(
            subset=["Jugador"],
            **{"width": "240px"}
        )
    )

    # ----------------------------
    # TABLA CENTRADA
    # ----------------------------
    st.markdown("<div style='display:flex; justify-content:center;'>", unsafe_allow_html=True)
    st.dataframe(
        df_styled,
        use_container_width=False,
        hide_index=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------
    # LEYENDA (CUADRO AJUSTADO AL TEXTO)
    # ----------------------------
    st.markdown(
        """
<div style="
    display: inline-block;
    border: 1px solid rgba(200,200,200,0.4);
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 14px;
    margin-bottom: 16px;
">
<h4 style="margin-top:0;">📘 Leyenda del ranking</h4>
<ul style="margin-left:0; padding-left:18px;">
  <li><strong>RK</strong> → Posición</li>
  <li><strong>PJ</strong> → Partidos jugados</li>
  <li><strong>PG</strong> → Partidos ganados</li>
  <li><strong>PP</strong> → Partidos perdidos</li>
  <li><strong>Pts</strong> → Puntos totales</li>
  <li><strong>JG</strong> → Juegos ganados</li>
  <li><strong>JP</strong> → Juegos perdidos</li>
  <li><strong>Dif</strong> → Diferencia de juegos (<strong>JG − JP</strong>)</li>
  <li>➕ → <strong>No participan más.</strong></li>
</ul>
</div>
""",
        unsafe_allow_html=True
    )

    # ----------------------------
    # SISTEMA DE PUNTUACIÓN (SUELTO)
    # ----------------------------
    st.markdown(
        """
### 🏓 Sistema de puntuación

- ✅ **Partido ganado en 1 set** → **3 puntos**  
- ✅ **Partido ganado en 2 sets (2‑0)** → **3 puntos**  
- ✅ **Partido a 3 sets (1‑1 + set decisivo)** → **3 puntos ganador / 1 punto perdedor**  
- ✅ **Empate sin tercer set (1‑1)** → **1 punto por jugador**
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

