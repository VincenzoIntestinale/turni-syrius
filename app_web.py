import os
import json
from datetime import datetime, timedelta
import streamlit as st

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configurazione della pagina web
st.set_page_config(page_title="Gestione Turni Syrius", layout="centered")

giorni_settimana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
CARTELLA_GENERATED = "generated"
os.makedirs(CARTELLA_GENERATED, exist_ok=True)

info_dipendenti = {
    "Domenica Visconte": {"ruolo": "Laboratorio Cucina", "ore_m": "10:30-13:30", "ore_p": "16:30-19:30"},
    "Valentina Rocco": {"ruolo": "Alfabetizzazione Italiano", "ore_m": "09:00-12:00", "ore_p": "15:30-18:30"},
    "Vincenzo Intestinale": {"ruolo": "Alfabetizzazione Digitale", "ore_m": "09:00-12:00", "ore_p": "15:30-18:30"}
}

mesi_italiano = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

# --- INIZIALIZZAZIONE AVANZATA STATO SESSIONE ---
if "calendario" not in st.session_state:
    st.session_state.calendario = {g: [] for g in giorni_settimana}
if "note" not in st.session_state:
    st.session_state.note = ""
# Questo valore controlla il calendario grafico in modo bidirezionale
if "data_selettore" not in st.session_state:
    st.session_state.data_selettore = datetime.now().date() - timedelta(days=datetime.now().weekday())

def formatta_stringhe_date(lunedi):
    domenica = lunedi + timedelta(days=6)
    m_lun = mesi_italiano[lunedi.month - 1].upper()
    m_dom = mesi_italiano[domenica.month - 1].upper()
    if lunedi.month == domenica.month:
        return f"DAL {lunedi.day} AL {domenica.day} {m_lun} {lunedi.year}", f"DAL_{lunedi.day}_AL_{domenica.day}_{m_lun}_{lunedi.year}"
    return f"DAL {lunedi.day} {m_lun} AL {domenica.day} {m_dom} {lunedi.year}", f"DAL_{lunedi.day}_{m_lun}_AL_{domenica.day}_{m_dom}_{lunedi.year}"

def estrai_data_da_nome_file(stringa_file):
    try:
        parti = stringa_file.split("_")
        giorno = int(parti[1])
        anno = int(parti[-1])
        mese_testo = parti[-2].capitalize()
        mese = mesi_italiano.index(mese_testo) + 1
        return datetime(anno, mese, girono if 'girono' not in locals() else giorno).date()
    except:
        return datetime.now().date() - timedelta(days=datetime.now().weekday())

def genera_matrice_pdf(calendario, testo_periodo, note_testo):
    percorso_pdf = f"{CARTELLA_GENERATED}/temp_tabellone.pdf"
    doc = SimpleDocTemplate(percorso_pdf, pagesize=landscape(letter), title="Tabellone Turni")
    story = []
    styles = getSampleStyleSheet()
    t_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=20, leading=24, alignment=1, spaceAfter=5, textColor=colors.HexColor("#1A365D"))
    s_style = ParagraphStyle('T2', fontName="Helvetica-Bold", fontSize=14, leading=18, alignment=1, spaceAfter=20, textColor=colors.HexColor("#4A5568"))
    
    story.append(Paragraph("<b>TABELLONE TURNI SETTIMANALI PERSONALE SYRIUS</b>", t_style))
    story.append(Paragraph(testo_periodo, s_style))
    story.append(Spacer(1, 10))
    
    matrice = [["Dipendente"] + giorni_settimana]
    for nome, info in info_dipendenti.items():
        riga = [f"<b>{nome}</b><br/><font color='#718096'>{info['ruolo']}</font>"]
        for g in giorni_settimana:
            cella = "Riposo"
            for t in calendario[g]:
                if t["nome"] == nome:
                    cella = f"<b>{t['turno']}</b><br/>{t['orario']}"
                    break
            riga.append(cella)
        matrice.append(riga)
        
    formatted = []
    for r_idx, row in enumerate(matrice):
        f_row = []
        for c_idx, cell in enumerate(row):
            if r_idx == 0: 
                p_st = ParagraphStyle(f'H_{r_idx}_{c_idx}', fontName="Helvetica-Bold", fontSize=11, alignment=1, textColor=colors.white)
            else: 
                p_st = ParagraphStyle(
                    f'C_{r_idx}_{c_idx}', 
                    fontName="Helvetica", 
                    fontSize=9, 
                    leading=13, 
                    alignment=0 if c_idx==0 else 1, 
                    leftIndent=4 if c_idx==0 else 0,
                    textColor=colors.HexColor("#2D3748") if "Riposo" not in cell else colors.HexColor("#A0AEC0")
                )
            f_row.append(Paragraph(cell, p_st))
        formatted.append(f_row)
        
    table = Table(formatted, colWidths=[110] + [100]*7)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")), ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
    ]))
    story.append(table)
    
    if note_testo.strip():
        story.append(Spacer(1, 25))
        story.append(Paragraph("📝 NOTE E SPOSTAMENTI SETTIMANALI:", ParagraphStyle('NT', fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#2C5282"), spaceAfter=5)))
        t_nota = Table([[Paragraph(note_testo.replace("\n", "<br/>"), ParagraphStyle('NC', fontName="Helvetica-Oblique", fontSize=10, leading=14, textColor=colors.HexColor("#2D3748")))]], colWidths=[700])
        t_nota.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDF2F7")), ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")), ('PADDING', (0, 0), (-1, -1), 10)]))
        story.append(t_nota)
        
    doc.build(story)
    with open(percorso_pdf, "rb") as f:
        return f.read()

# --- INTERFACCIA GRAFICA WEB ---
st.title("🗓️ Pannello Gestione Turni - Syrius")

# Rilevamento automatico dei backup esistenti
file_json = [f for f in os.listdir(CARTELLA_GENERATED) if f.startswith("backup_") and f.endswith(".json")]

# 1. Menu Modifica Veloce (Carica vecchie settimane)
if file_json:
    opzioni_backup = [f.replace("backup_", "").replace(".json", "").replace("_", " ") for f in sorted(file_json, reverse=True)]
    backup_scelto = st.selectbox("📂 Carica una settimana specifica salvata:", ["Seleziona un backup..."] + opzioni_backup)
    
    if backup_scelto != "Seleziona un backup..." and st.button("🔄 Carica Backup"):
        stringa_file_nome = backup_scelto.replace(' ', '_')
        nome_file_vero = f"backup_{stringa_file_nome}.json"
        
        with open(os.path.join(CARTELLA_GENERATED, nome_file_vero), "r", encoding="utf-8") as f:
            dati = json.load(f)
            st.session_state.calendario = dati.get("calendario", {g: [] for g in giorni_settimana})
            st.session_state.note = dati.get("note", "")
        
        # AGGIORNATO: Questo sposta FISICAMENTE il widget del calendario alla data corretta
        st.session_state.data_selettore = estrai_data_da_nome_file(stringa_file_nome)
        st.session_state.ultima_data_letta = stringa_file_nome
        st.rerun()

# 2. Impostazione Data (Legata stabilmente alla chiave della sessione)
data_selezionata = st.date_input("📅 Settimana di lavoro selezionata:", key="data_selettore")
if data_selezionata.weekday() != 0:
    st.warning("⚠️ La data selezionata non è un Lunedì!")

testo_periodo, stringa_file = formatta_stringhe_date(data_selezionata)

# Controllo se l'utente cambia settimana tramite il calendario grafico
percorso_json_data = f"{CARTELLA_GENERATED}/backup_{stringa_file}.json"
if st.session_state.get("ultima_data_letta") != stringa_file:
    if os.path.exists(percorso_json_data):
        with open(percorso_json_data, "r", encoding="utf-8") as f:
            dati_data = json.load(f)
            st.session_state.calendario = dati_data.get("calendario", {g: [] for g in giorni_settimana})
            st.session_state.note = dati_data.get("note", "")
    else:
        st.session_state.calendario = {g: [] for g in giorni_settimana}
        st.session_state.note = ""
    st.session_state.ultima_data_letta = stringa_file

# 3. Assegnazione Turni
col1, col2 = st.columns(2)

with col1:
    st.subheader("✍️ Assegna Turno")
    dipendente = st.selectbox("Dipendente:", list(info_dipendenti.keys()))
    giorno = st.selectbox("Giorno:", giorni_settimana)
    turno = st.selectbox("Turno:", ["Mattina", "Pomeriggio", "Riposo"])
    
    if st.button("➕ Applica / Aggiorna Turno", use_container_width=True):
        st.session_state.calendario[giorno] = [t for t in st.session_state.calendario[giorno] if t["nome"] != dipendente]
        if turno != "Riposo":
            orario = info_dipendenti[dipendente]["ore_m"] if turno == "Mattina" else info_dipendenti[dipendente]["ore_p"]
            st.session_state.calendario[giorno].append({"nome": dipendente, "turno": turno, "orario": orario})
        
        with open(percorso_json_data, "w", encoding="utf-8") as f:
            json.dump({"calendario": st.session_state.calendario, "note": st.session_state.note}, f, ensure_ascii=False, indent=4)
        st.rerun()

with col2:
    st.subheader("👀 Riepilogo Settimanale")
    for g in giorni_settimana:
        turni_giorno = st.session_state.calendario[g]
        if turni_giorno:
            testo_giorno = ", ".join([f"**{t['nome']}**: {t['turno']}" for t in turni_giorno])
            st.markdown(f"🔹 **{g.upper()}**: {testo_giorno}")
        else:
            st.markdown(f"🔹 **{g.upper()}**: *Tutti in Riposo*")

# 4. Note
st.subheader("📝 Note e Spostamenti")
vecchie_note = st.session_state.note
st.session_state.note = st.text_area("Inserisci eventuali annotazioni:", value=vecchie_note)
if st.session_state.note != vecchie_note:
    with open(percorso_json_data, "w", encoding="utf-8") as f:
        json.dump({"calendario": st.session_state.calendario, "note": st.session_state.note}, f, ensure_ascii=False, indent=4)
#-- BOTTONI DI SALVATAGGIO E DOWNLOAD COMPLETATI ---
st.markdown("---")
col_azioni1, col_azioni2 = st.columns(2)
with col_azioni1:
    if st.button("🗑️ Svuota Tabella Corrente", use_container_width=True):
        st.session_state.calendario = {g: [] for g in giorni_settimana}
        st.session_state.note = ""
        if os.path.exists(percorso_json_data):
            os.remove(percorso_json_data)
        st.rerun()
with col_azioni2:
    try:
        pdf_bytes = genera_matrice_pdf(st.session_state.calendario, testo_periodo, st.session_state.note)
        st.download_button(label="💾 SCARICA TABELLONE PDF", data=pdf_bytes, file_name=f"tabellone_{stringa_file}.pdf", mime="application/pdf", use_container_width=True)
    except Exception as e:
        st.error(f"Errore nella preparazione del PDF: {str(e)}")