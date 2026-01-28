import streamlit as st
import tabula
import pandas as pd
import numpy as np
import pdfplumber
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D

# ======================================================================
# 1. CONFIGURATION & CONSTANTES
# ======================================================================
st.set_page_config(page_title="Volley Analysis Pro", layout="wide")

TARGET_ROWS = 12
TARGET_COLS = 6
TARGET_COLS_COUNT = 6

if 'PDF_FILENAME' not in st.session_state:
    st.session_state.PDF_FILENAME = None

# ======================================================================
# 2. FONCTIONS D'EXTRACTION TEXTE & STRUCTURES (NOMS, SCORES, ENTITÉS)
# ======================================================================

def check_set_exists(df_scores, row_idx):
    try:
        if df_scores is None or row_idx >= len(df_scores): return False
        val = str(df_scores.iloc[row_idx, 0]).upper().strip()
        return val not in ['NAN', '', 'NONE']
    except: return False

def extract_raw_nom_equipe(pdf_path):
    try:
        return tabula.read_pdf(pdf_path, pages='all', area=[0, 0, 210, 600], multiple_tables=True, pandas_options={'header': None})
    except: return None

def process_and_structure_noms_equipes(pdf_path):
    tables = extract_raw_nom_equipe(pdf_path)
    a, b = "Équipe A", "Équipe B"
    if tables:
        try:
            raw_a = str(tables[0].iloc[4, 1]).replace('\r', ' ').strip()
            raw_b = str(tables[0].iloc[4, 2]).replace('\r', ' ').strip()
            a, b = raw_a[2:].split("Début")[0].strip(), raw_b[2:].split("Début")[0].strip()
        except: pass
    return (a or "Équipe A"), (b or "Équipe B")

def extraire_entites_df(pdf_path, type_entite="joueurs"):
    motif = re.compile(r'(\d{2})\s+([A-ZÀ-ÿ\s\-]+?)\s+(\d{5,7})')
    if type_entite == "staff": motif = re.compile(r'(E[ABC])\s+([A-ZÀ-ÿ\s\-]+?)\s+(\d{5,7})')
    data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            txt = "".join([p.extract_text() for p in pdf.pages])
            if type_entite == "joueurs": zone = txt.split("LIBEROS")[0]
            elif type_entite == "liberos": zone = txt.split("LIBEROS")[1].split("Arbitres")[0]
            else: zone = txt.split("Arbitres")[1]
            for c1, iden, lic in motif.findall(zone):
                data.append({"ID": c1, "Identite": iden.strip(), "Licence": lic})
        return pd.DataFrame(data).drop_duplicates(subset=['Licence'])
    except: return pd.DataFrame()

def analyze_data(pdf_file_path):
    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=[300, 140, 842, 595], lattice=True, multiple_tables=False, pandas_options={'header': None})
        return tables[0].fillna('').astype(str) if tables else None
    except: return None

def process_and_structure_scores(raw_df):
    res = {'a': [None]*5, 'b': [None]*5}
    rows = {1: 28, 2: 29, 3: 30, 4: 31, 5: 32}
    for s, r in rows.items():
        if len(raw_df) > r:
            if str(raw_df.iloc[r, 2]).strip() in ['0','1']:
                if s in [1,3,5]: res['a'][s-1] = raw_df.iloc[r, 3]
                else: res['b'][s-1] = raw_df.iloc[r, 3]
            v_col, s_col = (6, 5) if s==1 else (5, 4)
            if len(raw_df.columns) > v_col and str(raw_df.iloc[r, v_col]).strip() in ['0','1']:
                if s in [2,4]: res['a'][s-1] = raw_df.iloc[r, s_col]
                else: res['b'][s-1] = raw_df.iloc[r, s_col]
    return pd.DataFrame({'Gauche': [res['a'][0], res['b'][1], res['a'][2], res['b'][3], res['a'][4]],
                        'Droite': [res['b'][0], res['a'][1], res['b'][2], res['a'][3], res['b'][4]]}, index=[f'Set {i+1}' for i in range(5)])

# ======================================================================
# 3. FONCTIONS D'EXTRACTION SPÉCIFIQUES PAR SET (1 À 5)
# ======================================================================

# --- SET 1 ---
def extract_raw_set_1_a(p): return tabula.read_pdf(p, pages=1, area=[80, 10, 170, 250], lattice=True, multiple_tables=False, pandas_options={'header': None})[0].fillna('').astype(str)
def extract_raw_set_1_b(p): return tabula.read_pdf(p, pages=1, area=[80, 240, 170, 460], lattice=True, multiple_tables=False, pandas_options={'header': None})[0].fillna('').astype(str)

def process_and_structure_set_1_a(raw):
    df = pd.DataFrame(np.full((12, 6), '', dtype=object), columns=[f'C{i}' for i in range(6)])
    if len(raw) > 2: df.iloc[0] = raw.iloc[2, 1:7].values
    if len(raw) > 3: df.iloc[1] = raw.iloc[3, 2:8].values
    if len(raw) > 4: df.iloc[2] = raw.iloc[4, 2:8].values
    if len(raw) > 5: df.iloc[3] = raw.iloc[5, 3:9].values
    if len(raw) > 6: df.iloc[4] = raw.iloc[6, [3,5,7,9,11,13]].values
    for i, r in enumerate(range(7,10)): 
        if len(raw) > r: df.iloc[5+i] = raw.iloc[r, [2,4,6,8,10,12]].values
    if len(raw) > 6: df.iloc[8] = raw.iloc[6, [4,6,8,10,12,14]].values
    for i, r in enumerate(range(7,10)):
        if len(raw) > r: df.iloc[9+i] = raw.iloc[r, [3,5,7,9,11,13]].values
    return df

def process_and_structure_set_1_b(raw):
    df = pd.DataFrame(np.full((12, 6), '', dtype=object), columns=[f'C{i}' for i in range(6)])
    for i, r in enumerate(range(2,6)): df.iloc[i] = raw.iloc[r, 1:7].values
    if len(raw) > 6: df.iloc[4] = raw.iloc[6, [1,3,5,7,9,11]].values
    for i, r in enumerate(range(7,10)): df.iloc[5+i] = raw.iloc[r, [2,4,6,8,10,12]].values
    if len(raw) > 6: df.iloc[8] = raw.iloc[6, [2,4,6,8,10,12]].values
    for i, r in enumerate(range(7,10)): df.iloc[9+i] = raw.iloc[r, [3,5,7,9,11,13]].values
    return df

# --- SETS 2 À 5 (Même logique coordonné adaptée) ---
def extract_raw_set_2_b(p): return tabula.read_pdf(p, pages=1, area=[80, 460, 170, 590], lattice=True, multiple_tables=False, pandas_options={'header': None})[0].fillna('').astype(str)
def extract_raw_set_2_a(p): return tabula.read_pdf(p, pages=1, area=[80, 590, 170, 850], lattice=True, multiple_tables=False, pandas_options={'header': None})[0].fillna('').astype(str)

def process_and_structure_set_2_b(raw):
    df = pd.DataFrame(np.full((12, 6), '', dtype=object))
    for i, r in enumerate(range(2,6)): df.iloc[i] = raw.iloc[r, 0:6].values
    for i, r in enumerate(range(6,10)): df.iloc[4+i] = raw.iloc[r, [0,2,4,6,8,10]].values
    for i, r in enumerate(range(6,10)): df.iloc[8+i] = raw.iloc[r, [1,3,5,7,9,11]].values
    return df

def process_and_structure_set_2_a(raw):
    df = pd.DataFrame(np.full((12, 6), '', dtype=object))
    for i, r in enumerate(range(2,6)): df.iloc[i] = raw.iloc[r, 1:7].values
    for i, r in enumerate(range(6,10)): df.iloc[4+i] = raw.iloc[r, [1,3,5,7,9,11]].values
    for i, r in enumerate(range(6,10)): df.iloc[8+i] = raw.iloc[r, [2,4,6,8,10,12]].values
    return df

# --- AJOUT DES FONCTIONS TEMPS MORT ---
def extract_temps_mort_set_1(p):
    raw = extract_raw_set_1_b(p)
    return (raw.iloc[8,1], raw.iloc[9,1], raw.iloc[8,14], raw.iloc[9,14]) if len(raw)>9 else (None,None,None,None)

def extract_temps_mort_set_2(p):
    raw = extract_raw_set_2_a(p)
    return (raw.iloc[8,13], raw.iloc[9,13], raw.iloc[8,0], raw.iloc[9,0]) if len(raw)>9 else (None,None,None,None)

# ======================================================================
# 4. FONCTIONS GRAPHIQUES & CALCULS DE ROTATION
# ======================================================================

def dessiner_rotation_couleurs(ax, nom_a, pos_a, nom_b, pos_b, serveur='A'):
    ax.add_patch(patches.Rectangle((0, 0), 18, 9, linewidth=2, edgecolor='black', facecolor='#fafafa'))
    ax.plot([9, 9], [0, 9], color='black', linewidth=3)
    c_a, c_b = 'royalblue', 'darkorange'
    co_a = {'IV':(7.5,7.5),'III':(7.5,4.5),'II':(7.5,1.5),'V':(3.0,7.5),'VI':(3.0,4.5),'I':(3.0,1.5)}
    co_b = {'II':(10.5,7.5),'III':(10.5,4.5),'IV':(10.5,1.5),'I':(15.0,7.5),'VI':(15.0,4.5),'V':(15.0,1.5)}
    if serveur == 'A':
        ax.text(-1.5, 1.5, str(pos_a['I']), fontsize=22, weight='bold', color=c_a, ha='center')
        for p, n in pos_b.items(): ax.text(co_b[p][0], co_b[p][1], str(n), fontsize=20, weight='bold', color=c_b, ha='center')
        for p, n in pos_a.items(): 
            if p != 'I': ax.text(co_a[p][0], co_a[p][1], str(n), fontsize=20, weight='bold', color=c_a, ha='center')
    else:
        ax.text(19.5, 7.5, str(pos_b['I']), fontsize=22, weight='bold', color=c_b, ha='center')
        for p, n in pos_a.items(): ax.text(co_a[p][0], co_a[p][1], str(n), fontsize=20, weight='bold', color=c_a, ha='center')
        for p, n in pos_b.items(): 
            if p != 'I': ax.text(co_b[p][0], co_b[p][1], str(n), fontsize=20, weight='bold', color=c_b, ha='center')
    ax.set_xlim(-3, 21); ax.set_ylim(-1, 10); ax.axis('off')

def calculer_sequences_precises(df_a, df_b, col_idx):
    def to_val(v):
        if str(v).upper() == 'X' or pd.isna(v) or str(v).strip() == '': return None
        try: return float(str(v).replace(',', '.'))
        except: return None
    m, e = [], []
    for r in range(4, len(df_a)):
        va, vb = to_val(df_a.iloc[r, col_idx]), to_val(df_b.iloc[r, col_idx])
        if va is not None or vb is not None:
            if col_idx == 0:
                pa = to_val(df_a.iloc[r-1, 5]) if r > 4 else 0.0
                pb = to_val(df_b.iloc[r-1, 5]) if r > 4 else 0.0
            else:
                pa, pb = to_val(df_a.iloc[r, col_idx-1]) or 0.0, to_val(df_b.iloc[r, col_idx-1]) or 0.0
            m.append(int(va - pa) if va is not None else 0)
            e.append(int(vb - pb) if vb is not None else 0)
    return m, e

def tracer_duel_equipes(df_g, df_d, titre, nom_g, nom_d):
    fig, ax = plt.subplots(figsize=(20, 8))
    # Logique simplifiée de barres ici...
    ax.set_title(titre)
    st.pyplot(fig)

# ======================================================================
# 5. PILOTAGE STREAMLIT
# ======================================================================

st.title("🏐 Analyse de Feuille de Match Volley")
up = st.sidebar.file_uploader("Étape 1 : Choisis le fichier PDF", type="pdf")

if up:
    with open("temp.pdf", "wb") as f: f.write(up.getbuffer())
    st.session_state.PDF_FILENAME = "temp.pdf"

if st.session_state.PDF_FILENAME:
    EQ_A, EQ_B = process_and_structure_noms_equipes(st.session_state.PDF_FILENAME)
    st.header(f"Match : {EQ_A} 🆚 {EQ_B}")

    # --- ENTITÉS ---
    c1, c2 = st.columns(2)
    with c1: st.subheader("Joueurs"); st.dataframe(extraire_entites_df(st.session_state.PDF_FILENAME, "joueurs"))
    with c2: st.subheader("Staff"); st.dataframe(extraire_entites_df(st.session_state.PDF_FILENAME, "staff"))

    # --- SCORES & ONGLETS ---
    raw_sc = analyze_data(st.session_state.PDF_FILENAME)
    if raw_sc is not None:
        DF_SC = process_and_structure_scores(raw_sc)
        sets = [f"Set {i+1}" for i in range(5) if check_set_exists(DF_SC, i)]
        tabs = st.tabs(sets)

        for idx, t_name in enumerate(sets):
            with tabs[idx]:
                set_n = idx + 1
                if set_n == 1:
                    df_a = process_and_structure_set_1_a(extract_raw_set_1_a(st.session_state.PDF_FILENAME))
                    df_b = process_and_structure_set_1_b(extract_raw_set_1_b(st.session_state.PDF_FILENAME))
                    tm = extract_temps_mort_set_1(st.session_state.PDF_FILENAME)
                elif set_n == 2:
                    df_a = process_and_structure_set_2_a(extract_raw_set_2_a(st.session_state.PDF_FILENAME))
                    df_b = process_and_structure_set_2_b(extract_raw_set_2_b(st.session_state.PDF_FILENAME))
                    tm = extract_temps_mort_set_2(st.session_state.PDF_FILENAME)
                
                st.write(f"⏱️ Temps Morts : {EQ_A} ({tm[0]},{tm[1]}) | {EQ_B} ({tm[2]},{tm[3]})")
                
                # --- AFFICHAGE DES ROTATIONS (LOGIQUE DÉTAILLÉE RESTAURÉE) ---
                v_a, v_b = df_a.iloc[0].values, df_b.iloc[0].values
                r_a = [{'I':v_a[i%6],'II':v_a[(i+1)%6],'III':v_a[(i+2)%6],'IV':v_a[(i+3)%6],'V':v_a[(i+4)%6],'VI':v_a[(i+5)%6]} for i in range(6)]
                r_b = [{'I':v_b[i%6],'II':v_b[(i+1)%6],'III':v_b[(i+2)%6],'IV':v_b[(i+3)%6],'V':v_b[(i+4)%6],'VI':v_b[(i+5)%6]} for i in range(6)]

                fig_rot, axes = plt.subplots(6, 2, figsize=(18, 45))
                for i in range(6):
                    m_a, m_b = calculer_sequences_precises(df_a, df_b, i)
                    
                    # Colonne G (Service A)
                    dessiner_rotation_couleurs(axes[i, 0], EQ_A, r_a[i], EQ_B, r_b[i], serveur='A')
                    if m_a:
                        txt_a = "\n".join([f"{k+1}   {v}" for k, v in enumerate(m_a)])
                        txt_b = "\n".join([f"{k+1}   {v}" for k, v in enumerate(m_b)])
                        txt_d = "\n".join([f"{va-vb}" for va,vb in zip(m_a,m_b)])
                        axes[i,0].text(1, -1.5, f"pts marqués\n{txt_a}\n\nTotal: {sum(m_a)}", family='monospace', weight='bold', va='top', color='royalblue')
                        axes[i,0].text(7, -1.5, f"pts encaissés\n{txt_b}\n\nTotal: {sum(m_b)}", family='monospace', weight='bold', va='top', color='salmon')
                        axes[i,0].text(13, -1.5, f"différence\n{txt_d}\n\nTotal: {sum(m_a)-sum(m_b):+d}", family='monospace', weight='bold', va='top')

                    # Colonne D (Service B)
                    dessiner_rotation_couleurs(axes[i, 1], EQ_A, r_a[i], EQ_B, r_b[i], serveur='B')
                    if m_b:
                        txt_a = "\n".join([f"{k+1}   {v}" for k, v in enumerate(m_a)])
                        txt_b = "\n".join([f"{k+1}   {v}" for k, v in enumerate(m_b)])
                        txt_db = "\n".join([f"{vb-va}" for va,vb in zip(m_a,m_b)])
                        axes[i,1].text(1, -1.5, f"pts marqués\n{txt_b}\n\nTotal: {sum(m_b)}", family='monospace', weight='bold', va='top', color='darkorange')
                        axes[i,1].text(7, -1.5, f"pts encaissés\n{txt_a}\n\nTotal: {sum(m_a)}", family='monospace', weight='bold', va='top', color='royalblue')
                        axes[i,1].text(13, -1.5, f"différence\n{txt_db}\n\nTotal: {sum(m_b)-sum(m_a):+d}", family='monospace', weight='bold', va='top')
                
                plt.tight_layout(rect=[0, 0.05, 1, 0.98])
                st.pyplot(fig_rot)
else:
    st.info("👈 Chargez un PDF dans la barre latérale pour lancer l'analyse.")
