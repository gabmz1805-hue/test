import streamlit as st
import tabula
import pandas as pd
import numpy as np
import pdfplumber
import re
from tabulate import tabulate
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D

# ======================================================================
# CONFIGURATION STREAMLIT
# ======================================================================
st.set_page_config(page_title="Analyse Volley PDF", layout="wide")
st.title("🏐 Analyse de Feuille de Match PDF (Volley-Ball)")

# On remplace le print par un message Streamlit
st.sidebar.info("Configuration terminée. Prêt pour l'analyse.")

# ======================================================================
# CONSTANTES GLOBALES
# ======================================================================
TARGET_ROWS = 12
TARGET_COLS = 6
TARGET_COLS_COUNT = 6

# Initialisation des variables dans la session Streamlit pour les garder en mémoire
if 'PDF_FILENAME' not in st.session_state:
    st.session_state.PDF_FILENAME = None

# ======================================================================
# CHARGEMENT DU FICHIER (Remplace files.upload())
# ======================================================================
uploaded_file = st.sidebar.file_uploader("Étape 1 : Choisis le fichier PDF du match", type="pdf")

if uploaded_file:
    # Sauvegarde temporaire du fichier pour Tabula
    with open("temp_match.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.PDF_FILENAME = "temp_match.pdf"
    st.sidebar.success("✅ Fichier chargé avec succès")

# ----------------------------------------------------------------------
# FONCTIONS UTILITAIRES D'AFFICHAGE (Adaptées Streamlit)
# ----------------------------------------------------------------------

def display_dataframe(df: pd.DataFrame, title: str):
    """Affiche un DataFrame structuré proprement dans Streamlit."""
    st.subheader(f"--- {title} ---")

    # On prépare le DataFrame pour l'affichage (index R0, R1...)
    df_display = df.copy().fillna('')
    df_display.index = [f'R{i}' for i in range(len(df_display))]
    df_display.columns = [f'C{i}' for i in range(len(df_display.columns))]

    # Affichage interactif au lieu de tabulate (plus lisible sur le web)
    st.dataframe(df_display, use_container_width=True)

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 1 a
# ======================================================================

def extract_raw_set_1_a(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 1 (Équipe a)."""
    COORDINATES_TEAM_G = [80, 10, 170, 250]

    try:
        # Utilisation de stream=True car Tabula peut parfois mieux lire sans lattice
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_TEAM_G, lattice=True, multiple_tables=False, pandas_options={'header': None})
        if tables:
            st.toast("✅ Extraction Set 1 a réussie") # Petit message discret en bas à droite
            return tables[0].fillna('').astype(str)
    except Exception as e:
        st.error(f"❌ ERREUR lors de l'extraction tabula pour Set 1 a. Détails: {e}")
        return None

    return None

# ======================================================================
# FONCTIONS structure - SET 1 a (Équipe Gauche)
# ======================================================================

def process_and_structure_set_1_a(raw_df: pd.DataFrame) -> pd.DataFrame or None:
    """Crée le DataFrame Cible et y transfère toutes les données brutes du Set 1 - Équipe a."""

    # 1. CRÉATION DU TABLEAU CIBLE VIDE
    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_a = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])

    # On utilise un toast pour informer du début du traitement
    st.toast(f"⏳ Structuration des données Équipe A...")

    # ÉTAPE 4 : Formation de Départ (R2 Source -> R0 Cible)
    if len(raw_df) > 2:
        data = raw_df.iloc[2, 1:7].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[0, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 5 : Remplaçants (R3 Source -> R1 Cible)
    if len(raw_df) > 3:
        data = raw_df.iloc[3, 2:8].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[1, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 6 : Score (R4 Source -> R2 Cible)
    if len(raw_df) > 4:
        data = raw_df.iloc[4, 2:8].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[2, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 7 : Première Ligne d'Action (R5 Source -> R3 Cible)
    if len(raw_df) > 5:
        data = raw_df.iloc[5, 3:9].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[3, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 8 à 11 : Libero/Rotations (Indices spécifiques)
    SOURCE_COL_INDICES_R8 = [3, 5, 7, 9, 11, 13]
    SOURCE_COL_INDICES_R_GEN = [2, 4, 6, 8, 10, 12]

    if len(raw_df) > 6 and len(raw_df.columns) > max(SOURCE_COL_INDICES_R8):
        data = raw_df.iloc[6, SOURCE_COL_INDICES_R8].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[4, 0:TARGET_COLS_COUNT] = data

    for i, row_src in enumerate(range(7, 10)): # Lignes R7, R8, R9
        if len(raw_df) > row_src and len(raw_df.columns) > max(SOURCE_COL_INDICES_R_GEN):
            data = raw_df.iloc[row_src, SOURCE_COL_INDICES_R_GEN].values
            if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[5+i, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 12 à 15 : Actions (Indices spécifiques)
    SOURCE_COL_INDICES_R12 = [4, 6, 8, 10, 12, 14]
    SOURCE_COL_INDICES_ACTIONS = [3, 5, 7, 9, 11, 13]

    if len(raw_df) > 6 and len(raw_df.columns) > max(SOURCE_COL_INDICES_R12):
        data = raw_df.iloc[6, SOURCE_COL_INDICES_R12].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[8, 0:TARGET_COLS_COUNT] = data

    for i, row_src in enumerate(range(7, 10)): # Lignes R7, R8, R9
        if len(raw_df) > row_src and len(raw_df.columns) > max(SOURCE_COL_INDICES_ACTIONS):
            data = raw_df.iloc[row_src, SOURCE_COL_INDICES_ACTIONS].values
            if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[9+i, 0:TARGET_COLS_COUNT] = data

    return FINAL_DATAFRAME_a

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 1 b (Équipe Droite)
# ======================================================================

def extract_raw_set_1_b(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 1 (Équipe b)."""
    COORDINATES_TEAM_D = [80, 240, 170, 460]

    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_TEAM_D, lattice=True, multiple_tables=False, pandas_options={'header': None})
        if tables:
            st.toast("✅ Extraction Set 1 b réussie")
            return tables[0].fillna('').astype(str)
    except Exception as e:
        st.error(f"❌ ERREUR lors de l'extraction Set 1 b: {e}")
        return None
    return None

# ======================================================================
# FONCTIONS structure - SET 1 b
# ======================================================================

def process_and_structure_set_1_b(raw_df_b: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 1 - Équipe b."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_b = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])

    st.toast(f"⏳ Structuration des données Équipe B...")

    # Indices Colonnes
    S_START, S_END = 1, 7
    ODD_1_11 = [1, 3, 5, 7, 9, 11]
    EVEN_2_12 = [2, 4, 6, 8, 10, 12]
    ODD_3_13 = [3, 5, 7, 9, 11, 13]

    # Transferts Standard (Formation, Remplaçants, Score, Action L1)
    for i, src_row in enumerate(range(2, 6)):
        if len(raw_df_b) > src_row:
            data = raw_df_b.iloc[src_row, S_START:S_END].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_b.iloc[i, 0:TARGET_COLS_COUNT] = data

    # Transferts Libero/Rotations
    if len(raw_df_b) > 6 and len(raw_df_b.columns) > max(ODD_1_11):
        FINAL_DATAFRAME_b.iloc[4, 0:TARGET_COLS_COUNT] = raw_df_b.iloc[6, ODD_1_11].values

    for i, src_row in enumerate(range(7, 10)):
        if len(raw_df_b) > src_row and len(raw_df_b.columns) > max(EVEN_2_12):
            FINAL_DATAFRAME_b.iloc[5+i, 0:TARGET_COLS_COUNT] = raw_df_b.iloc[src_row, EVEN_2_12].values

    # Transferts Actions
    if len(raw_df_b) > 6 and len(raw_df_b.columns) > max(EVEN_2_12):
        FINAL_DATAFRAME_b.iloc[8, 0:TARGET_COLS_COUNT] = raw_df_b.iloc[6, EVEN_2_12].values

    for i, src_row in enumerate(range(7, 10)):
        if len(raw_df_b) > src_row and len(raw_df_b.columns) > max(ODD_3_13):
            FINAL_DATAFRAME_b.iloc[9+i, 0:TARGET_COLS_COUNT] = raw_df_b.iloc[src_row, ODD_3_13].values

    return FINAL_DATAFRAME_b

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 2 b (Équipe Gauche au Set 2)
# ======================================================================

def extract_raw_set_2_b(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 2 (Équipe b)."""
    COORDINATES_SET_2_G = [80, 460, 170, 590]

    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_2_G, lattice=True, multiple_tables=False, pandas_options={'header': None})
        if tables:
            st.toast("✅ Extraction Set 2 b réussie")
            return tables[0].fillna('').astype(str)
    except Exception as e:
        st.error(f"❌ ERREUR lors de l'extraction Set 2 b : {e}")
        return None
    return None

# ======================================================================
# FONCTIONS structure - SET 2 b
# ======================================================================

def process_and_structure_set_2_b(raw_df_s2_b: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 2 - Équipe b."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_2_b = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])

    st.toast("⏳ Structuration Set 2 Équipe B...")

    # Configuration des indices
    S_START, S_END = 0, 6
    EVEN_0_10 = [0, 2, 4, 6, 8, 10]
    ODD_1_11 = [1, 3, 5, 7, 9, 11]

    # Transferts Standard (Formation, Remplaçants, Score, Action L1)
    for i, src_row in enumerate(range(2, 6)):
        if len(raw_df_s2_b) > src_row:
            data = raw_df_s2_b.iloc[src_row, S_START:S_END].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_SET_2_b.iloc[i, 0:TARGET_COLS_COUNT] = data

    # Transferts Libero/Rotations (Lignes 4 à 7)
    for i, src_row in enumerate(range(6, 10)):
        if len(raw_df_s2_b) > src_row and len(raw_df_s2_b.columns) > max(EVEN_0_10):
            FINAL_DATAFRAME_SET_2_b.iloc[4+i, 0:TARGET_COLS_COUNT] = raw_df_s2_b.iloc[src_row, EVEN_0_10].values

    # Transferts Actions (Lignes 8 à 11)
    for i, src_row in enumerate(range(6, 10)):
        if len(raw_df_s2_b) > src_row and len(raw_df_s2_b.columns) > max(ODD_1_11):
            FINAL_DATAFRAME_SET_2_b.iloc[8+i, 0:TARGET_COLS_COUNT] = raw_df_s2_b.iloc[src_row, ODD_1_11].values

    return FINAL_DATAFRAME_SET_2_b

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 2 a (Équipe Droite au Set 2)
# ======================================================================

def extract_raw_set_2_a(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 2 (Équipe a)."""
    COORDINATES_SET_2_D = [80, 590, 170, 850]

    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_2_D, lattice=True, multiple_tables=False, pandas_options={'header': None})
        if tables:
            st.toast("✅ Extraction Set 2 a réussie")
            return tables[0].fillna('').astype(str)
    except Exception as e:
        st.error(f"❌ ERREUR lors de l'extraction Set 2 a : {e}")
        return None
    return None

# ======================================================================
# FONCTIONS structure - SET 2 a
# ======================================================================

def process_and_structure_set_2_a(raw_df_s2_a: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 2 - Équipe a."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_2_a = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])

    st.toast("⏳ Structuration Set 2 Équipe A...")

    # Configuration des indices
    S_START, S_END = 1, 7
    ODD_1_11 = [1, 3, 5, 7, 9, 11]
    EVEN_2_12 = [2, 4, 6, 8, 10, 12]

    # Transferts Standard
    for i, src_row in enumerate(range(2, 6)):
        if len(raw_df_s2_a) > src_row:
            data = raw_df_s2_a.iloc[src_row, S_START:S_END].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_SET_2_a.iloc[i, 0:TARGET_COLS_COUNT] = data

    # Transferts Libero/Rotations (Lignes 4 à 7)
    for i, src_row in enumerate(range(6, 10)):
        if len(raw_df_s2_a) > src_row and len(raw_df_s2_a.columns) > max(ODD_1_11):
            FINAL_DATAFRAME_SET_2_a.iloc[4+i, 0:TARGET_COLS_COUNT] = raw_df_s2_a.iloc[src_row, ODD_1_11].values

    # Transferts Actions (Lignes 8 à 11)
    for i, src_row in enumerate(range(6, 10)):
        if len(raw_df_s2_a) > src_row and len(raw_df_s2_a.columns) > max(EVEN_2_12):
            FINAL_DATAFRAME_SET_2_a.iloc[8+i, 0:TARGET_COLS_COUNT] = raw_df_s2_a.iloc[src_row, EVEN_2_12].values

    return FINAL_DATAFRAME_SET_2_a

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 3 a (Équipe Gauche au Set 3)
# ======================================================================

def extract_raw_set_3_a(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 3 (Équipe Gauche)."""
    COORDINATES_SET_3_G = [170, 10, 260, 250]

    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_3_G, lattice=True, multiple_tables=False, pandas_options={'header': None})
        if tables:
            st.toast("✅ Extraction Set 3 a réussie")
            return tables[0].fillna('').astype(str)
    except Exception as e:
        st.error(f"❌ ERREUR lors de l'extraction Set 3 a : {e}")
        return None
    return None

# ======================================================================
# FONCTIONS structure - SET 3 a
# ======================================================================

def process_and_structure_set_3_a(raw_df_s3_a: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 3 - Équipe a."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_3_a = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])

    st.toast("⏳ Structuration Set 3 Équipe A...")

    # Définition des indices sources
    ODD_R6 = [3, 5, 7, 9, 11, 13]
    EVEN_R7_R9 = [2, 4, 6, 8, 10, 12]
    EVEN_ACTION_R6 = [4, 6, 8, 10, 12, 14]
    ODD_ACTION_R7_R9 = [3, 5, 7, 9, 11, 13]

    # Transferts de base (R0 à R3 Cible)
    if len(raw_df_s3_a) > 2: FINAL_DATAFRAME_SET_3_a.iloc[0, 0:6] = raw_df_s3_a.iloc[2, 1:7].values
    if len(raw_df_s3_a) > 3: FINAL_DATAFRAME_SET_3_a.iloc[1, 0:6] = raw_df_s3_a.iloc[3, 2:8].values
    if len(raw_df_s3_a) > 4: FINAL_DATAFRAME_SET_3_a.iloc[2, 0:6] = raw_df_s3_a.iloc[4, 2:8].values
    if len(raw_df_s3_a) > 5: FINAL_DATAFRAME_SET_3_a.iloc[3, 0:6] = raw_df_s3_a.iloc[5, 3:9].values

    # Transferts Libero/Rotations
    if len(raw_df_s3_a) > 6 and len(raw_df_s3_a.columns) > max(ODD_R6):
        FINAL_DATAFRAME_SET_3_a.iloc[4, 0:6] = raw_df_s3_a.iloc[6, ODD_R6].values
    for i, r_src in enumerate(range(7, 10)): # R7, R8, R9
        if len(raw_df_s3_a) > r_src and len(raw_df_s3_a.columns) > max(EVEN_R7_R9):
            FINAL_DATAFRAME_SET_3_a.iloc[5+i, 0:6] = raw_df_s3_a.iloc[r_src, EVEN_R7_R9].values

    # Transferts Actions
    if len(raw_df_s3_a) > 6 and len(raw_df_s3_a.columns) > max(EVEN_ACTION_R6):
        FINAL_DATAFRAME_SET_3_a.iloc[8, 0:6] = raw_df_s3_a.iloc[6, EVEN_ACTION_R6].values
    for i, r_src in enumerate(range(7, 10)): # R7, R8, R9
        if len(raw_df_s3_a) > r_src and len(raw_df_s3_a.columns) > max(ODD_ACTION_R7_R9):
            FINAL_DATAFRAME_SET_3_a.iloc[9+i, 0:6] = raw_df_s3_a.iloc[r_src, ODD_ACTION_R7_R9].values

    return FINAL_DATAFRAME_SET_3_a

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 3 b (Équipe Droite au Set 3)
# ======================================================================

def extract_raw_set_3_b(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 3 (Équipe b)."""
    COORDINATES_SET_3_D = [170, 240, 260, 470]

    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_3_D, lattice=True, multiple_tables=False, pandas_options={'header': None})
        if tables:
            st.toast("✅ Extraction Set 3 b réussie")
            return tables[0].fillna('').astype(str)
    except Exception as e:
        st.error(f"❌ ERREUR lors de l'extraction Set 3 b : {e}")
        return None
    return None

# ======================================================================
# FONCTIONS structure - SET 3 b
# ======================================================================

def process_and_structure_set_3_b(raw_df_s3_b: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 3 - Équipe Droite."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_3_b = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])

    st.toast("⏳ Structuration Set 3 Équipe B...")

    # Indices Colonnes
    S_START, S_END = 1, 7
    ODD_1_11 = [1, 3, 5, 7, 9, 11]
    EVEN_2_12 = [2, 4, 6, 8, 10, 12]
    ODD_3_13 = [3, 5, 7, 9, 11, 13]

    # Transferts Standard (Formation, Remplaçants, Score, Action L1)
    for i, src_row in enumerate(range(2, 6)):
        if len(raw_df_s3_b) > src_row:
            FINAL_DATAFRAME_SET_3_b.iloc[i, 0:6] = raw_df_s3_b.iloc[src_row, S_START:S_END].values

    # Transferts Libero/Rotations
    if len(raw_df_s3_b) > 6 and len(raw_df_s3_b.columns) > max(ODD_1_11):
        FINAL_DATAFRAME_SET_3_b.iloc[4, 0:6] = raw_df_s3_b.iloc[6, ODD_1_11].values
    for i, src_row in enumerate(range(7, 9)): # R7, R8
        if len(raw_df_s3_b) > src_row and len(raw_df_s3_b.columns) > max(EVEN_2_12):
            FINAL_DATAFRAME_SET_3_b.iloc[5+i, 0:6] = raw_df_s3_b.iloc[src_row, EVEN_2_12].values
    if len(raw_df_s3_b) > 9 and len(raw_df_s3_b.columns) > max(ODD_1_11):
        FINAL_DATAFRAME_SET_3_b.iloc[7, 0:6] = raw_df_s3_b.iloc[9, ODD_1_11].values

    # Transferts Actions
    if len(raw_df_s3_b) > 6 and len(raw_df_s3_b.columns) > max(EVEN_2_12):
        FINAL_DATAFRAME_SET_3_b.iloc[8, 0:6] = raw_df_s3_b.iloc[6, EVEN_2_12].values
    for i, src_row in enumerate(range(7, 9)): # R7, R8
        if len(raw_df_s3_b) > src_row and len(raw_df_s3_b.columns) > max(ODD_3_13):
            FINAL_DATAFRAME_SET_3_b.iloc[9+i, 0:6] = raw_df_s3_b.iloc[src_row, ODD_3_13].values
    if len(raw_df_s3_b) > 9 and len(raw_df_s3_b.columns) > max(EVEN_2_12):
        FINAL_DATAFRAME_SET_3_b.iloc[11, 0:6] = raw_df_s3_b.iloc[9, EVEN_2_12].values

    return FINAL_DATAFRAME_SET_3_b

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 4 b (Équipe Gauche au Set 4)
# ======================================================================

def extract_raw_set_4_b(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 4 (Équipe b)."""
    COORDINATES_SET_4_G = [170, 400, 260, 590]

    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_4_G, lattice=True, multiple_tables=False, pandas_options={'header': None})
        if tables:
            st.toast("✅ Extraction Set 4 b réussie")
            return tables[0].fillna('').astype(str)
    except Exception as e:
        st.error(f"❌ ERREUR lors de l'extraction Set 4 b : {e}")
        return None
    return None

# ======================================================================
# FONCTIONS structure - SET 4 b
# ======================================================================

def process_and_structure_set_4_b(raw_df_s4_b: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 4 - Équipe b."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_4_b = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])

    st.toast("⏳ Structuration Set 4 Équipe B...")

    # Constantes d'indices
    S_COLS = (1, 7)
    ODD_R6_R9 = [1, 3, 5, 7, 9, 11]
    EVEN_R7_R8 = [2, 4, 6, 8, 10, 12]
    EVEN_ACTION = [2, 4, 6, 8, 10, 12]
    ODD_ACTION = [3, 5, 7, 9, 11, 13]

    # Transferts Standard (Formation, Remplaçants, Score, Action L1)
    for i, src_row in enumerate(range(2, 6)):
        if len(raw_df_s4_b) > src_row:
            data = raw_df_s4_b.iloc[src_row, S_COLS[0]:S_COLS[1]].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_SET_4_b.iloc[i, 0:6] = data

    # Transferts Libero/Rotations
    if len(raw_df_s4_b) > 6 and len(raw_df_s4_b.columns) > max(ODD_R6_R9):
        FINAL_DATAFRAME_SET_4_b.iloc[4, 0:6] = raw_df_s4_b.iloc[6, ODD_R6_R9].values

    for i, r_src in enumerate([7, 8]):
        if len(raw_df_s4_b) > r_src and len(raw_df_s4_b.columns) > max(EVEN_R7_R8):
            FINAL_DATAFRAME_SET_4_b.iloc[5+i, 0:6] = raw_df_s4_b.iloc[r_src, EVEN_R7_R8].values

    if len(raw_df_s4_b) > 9 and len(raw_df_s4_b.columns) > max(ODD_R6_R9):
        FINAL_DATAFRAME_SET_4_b.iloc[7, 0:6] = raw_df_s4_b.iloc[9, ODD_R6_R9].values

    # Transferts Actions
    if len(raw_df_s4_b) > 6 and len(raw_df_s4_b.columns) > max(EVEN_ACTION):
        FINAL_DATAFRAME_SET_4_b.iloc[8, 0:6] = raw_df_s4_b.iloc[6, EVEN_ACTION].values

    for i, r_src in enumerate([7, 8]):
        if len(raw_df_s4_b) > r_src and len(raw_df_s4_b.columns) > max(ODD_ACTION):
            FINAL_DATAFRAME_SET_4_b.iloc[9+i, 0:6] = raw_df_s4_b.iloc[r_src, ODD_ACTION].values

    if len(raw_df_s4_b) > 9 and len(raw_df_s4_b.columns) > max(EVEN_ACTION):
        FINAL_DATAFRAME_SET_4_b.iloc[11, 0:6] = raw_df_s4_b.iloc[9, EVEN_ACTION].values

    return FINAL_DATAFRAME_SET_4_b

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 4 a (Équipe Droite au Set 4)
# ======================================================================

def extract_raw_set_4_a(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 4 (Équipe a)."""
    COORDINATES_SET_4_D = [170, 580, 260, 860]

    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_4_D, lattice=True, multiple_tables=False, pandas_options={'header': None})
        if tables:
            st.toast("✅ Extraction Set 4 a réussie")
            return tables[0].fillna('').astype(str)
    except Exception as e:
        st.error(f"❌ ERREUR lors de l'extraction Set 4 a : {e}")
        return None
    return None

# ======================================================================
# FONCTIONS structure - SET 4 a
# ======================================================================

def process_and_structure_set_4_a(raw_df_s4_a: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 4 - Équipe a."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_4_a = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])

    st.toast("⏳ Structuration Set 4 Équipe A...")

    # Configuration des indices
    S_START, S_END = 1, 7
    ODD_COLS = [1, 3, 5, 7, 9, 11]
    EVEN_COLS = [2, 4, 6, 8, 10, 12]

    # Transferts de base
    for i, r_src in enumerate(range(2, 6)):
        if len(raw_df_s4_a) > r_src:
            FINAL_DATAFRAME_SET_4_a.iloc[i, 0:6] = raw_df_s4_a.iloc[r_src, S_START:S_END].values

    # Transferts Libero/Rotations (Lignes 4 à 7 Cible)
    for i, r_src in enumerate(range(6, 10)):
        if len(raw_df_s4_a) > r_src and len(raw_df_s4_a.columns) > max(ODD_COLS):
            FINAL_DATAFRAME_SET_4_a.iloc[4+i, 0:6] = raw_df_s4_a.iloc[r_src, ODD_COLS].values

    # Transferts Actions (Lignes 8 à 11 Cible)
    for i, r_src in enumerate(range(6, 10)):
        if len(raw_df_s4_a) > r_src and len(raw_df_s4_a.columns) > max(EVEN_COLS):
            FINAL_DATAFRAME_SET_4_a.iloc[8+i, 0:6] = raw_df_s4_a.iloc[r_src, EVEN_COLS].values

    return FINAL_DATAFRAME_SET_4_a

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 5 (Zone Centrale)
# ======================================================================

def extract_raw_set_5_b(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 5 aux coordonnées spécifiées (Équipe b)."""
    COORDINATES_SET_5 = [280, 140, 360, 480]

    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_5, lattice=True, multiple_tables=False, pandas_options={'header': None})
        if tables:
            st.toast("✅ Extraction Set 5 b réussie")
            return tables[0].fillna('').astype(str)
    except Exception as e:
        st.error(f"❌ ERREUR lors de l'extraction Set 5 b : {e}")
        return None
    return None

def extract_raw_set_5_a(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 5 aux coordonnées spécifiées (Équipe a)."""
    COORDINATES_SET_5 = [280, 0, 360, 200]

    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_5, lattice=True, multiple_tables=False, pandas_options={'header': None})
        if tables:
            st.toast("✅ Extraction Set 5 a réussie")
            return tables[0].fillna('').astype(str)
    except Exception as e:
        st.error(f"❌ ERREUR lors de l'extraction Set 5 a : {e}")
        return None
    return None

# ======================================================================
# FONCTIONS structure - SET 5 b
# ======================================================================

def process_and_structure_set_5_b(raw_df_s5_b: pd.DataFrame) -> pd.DataFrame:
    """Structure les données brutes du Set 5 pour l'Équipe b."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_5_b = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])

    st.toast("⏳ Structuration Set 5 Équipe B...")

    S_START, S_END = 1, 7
    S_ODD_C1_C11 = [1, 3, 5, 7, 9, 11]
    S_EVEN_C2_C12 = [2, 4, 6, 8, 10, 12]
    S_EVEN_C3_C13 = [3, 5, 7, 9, 11, 13]

    # Transferts Standard (Formation, Remplaçants, Score, Action L1)
    for target_row, source_row in enumerate(range(1, 5)):
        if len(raw_df_s5_b) > source_row:
            data = raw_df_s5_b.iloc[source_row, S_START:S_END].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_SET_5_b.iloc[target_row, 0:6] = data

    # Transfert 5 : Libero/Rot. L1
    if len(raw_df_s5_b) > 5 and len(raw_df_s5_b.columns) > max(S_ODD_C1_C11):
        FINAL_DATAFRAME_SET_5_b.iloc[4, 0:6] = raw_df_s5_b.iloc[5, S_ODD_C1_C11].values

    # Transferts 6, 7, 8 (Rotations L2-L4)
    for target_row, source_row in enumerate(range(6, 9), start=5):
        if len(raw_df_s5_b) > source_row and len(raw_df_s5_b.columns) > max(S_EVEN_C2_C12):
            FINAL_DATAFRAME_SET_5_b.iloc[target_row, 0:6] = raw_df_s5_b.iloc[source_row, S_EVEN_C2_C12].values

    # Transfert 9 : Action L2
    if len(raw_df_s5_b) > 5 and len(raw_df_s5_b.columns) > max(S_EVEN_C2_C12):
        FINAL_DATAFRAME_SET_5_b.iloc[8, 0:6] = raw_df_s5_b.iloc[5, S_EVEN_C2_C12].values

    # Transferts 10, 11, 12 (Actions L3-L5)
    for target_row, source_row in enumerate(range(6, 9), start=9):
        if len(raw_df_s5_b) > source_row and len(raw_df_s5_b.columns) > max(S_EVEN_C3_C13):
            FINAL_DATAFRAME_SET_5_b.iloc[target_row, 0:6] = raw_df_s5_b.iloc[source_row, S_EVEN_C3_C13].values

    return FINAL_DATAFRAME_SET_5_b

# ======================================================================
# FONCTIONS structure - SET 5 a
# ======================================================================

def process_and_structure_set_5_a(raw_df_s5_a: pd.DataFrame) -> pd.DataFrame:
    """Structure les données brutes du Set 5 pour l'Équipe a."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_5_a = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])

    st.toast("⏳ Structuration Set 5 Équipe A...")

    S_START, S_END = 0, 6
    S_EVEN_C0_C10 = [0, 2, 4, 6, 8, 10]
    S_ODD_C1_C11 = [1, 3, 5, 7, 9, 11]

    # Transferts Standard
    for target_row, source_row in enumerate(range(1, 5)):
        if len(raw_df_s5_a) > source_row:
            data = raw_df_s5_a.iloc[source_row, S_START:S_END].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_SET_5_a.iloc[target_row, 0:6] = data

    # Transferts 5-8 (Rotations Libero)
    for target_row, source_row in enumerate(range(5, 9), start=4):
        if len(raw_df_s5_a) > source_row and len(raw_df_s5_a.columns) > max(S_EVEN_C0_C10):
            FINAL_DATAFRAME_SET_5_a.iloc[target_row, 0:6] = raw_df_s5_a.iloc[source_row, S_EVEN_C0_C10].values

    # Transferts 9-12 (Actions)
    for target_row, source_row in enumerate(range(5, 9), start=8):
        if len(raw_df_s5_a) > source_row and len(raw_df_s5_a.columns) > max(S_ODD_C1_C11):
            FINAL_DATAFRAME_SET_5_a.iloc[target_row, 0:6] = raw_df_s5_a.iloc[source_row, S_ODD_C1_C11].values

    return FINAL_DATAFRAME_SET_5_a

# ======================================================================
# FONCTIONS TEMPS MORT (SET 1 À 5)
# ======================================================================

def extract_temps_mort_set_1(pdf_file_path: str) -> tuple:
    """Extrait les quatre temps morts (G1, G2, D1, D2) du SET 1."""
    RAW_DATAFRAME_SET_1_D = extract_raw_set_1_b(pdf_file_path)
    T_set_a1, T_set_a2, T_set_b1, T_set_b2 = None, None, None, None

    if RAW_DATAFRAME_SET_1_D is not None and not RAW_DATAFRAME_SET_1_D.empty:
        max_rows, max_cols = RAW_DATAFRAME_SET_1_D.shape
        # Indices (R8, R9) x (C1, C14)
        if 8 < max_rows and 1 < max_cols:
            T_set_a1 = str(RAW_DATAFRAME_SET_1_D.iloc[8, 1]).strip()
        if 9 < max_rows and 1 < max_cols:
            T_set_a2 = str(RAW_DATAFRAME_SET_1_D.iloc[9, 1]).strip()
        if 8 < max_rows and 14 < max_cols:
            T_set_b1 = str(RAW_DATAFRAME_SET_1_D.iloc[8, 14]).strip()
        if 9 < max_rows and 14 < max_cols:
            T_set_b2 = str(RAW_DATAFRAME_SET_1_D.iloc[9, 14]).strip()

    return T_set_a1, T_set_a2, T_set_b1, T_set_b2

def extract_temps_mort_set_2(pdf_file_path: str) -> tuple:
    """Extrait les quatre temps morts du SET 2."""
    RAW_DATAFRAME_SET_2_D = extract_raw_set_2_a(pdf_file_path)
    T_set_b1, T_set_b2, T_set_a1, T_set_a2 = None, None, None, None

    if RAW_DATAFRAME_SET_2_D is not None and not RAW_DATAFRAME_SET_2_D.empty:
        max_rows, max_cols = RAW_DATAFRAME_SET_2_D.shape
        # Indices (R8, R9) x (C0, C13)
        if 8 < max_rows and 0 < max_cols:
            T_set_b1 = str(RAW_DATAFRAME_SET_2_D.iloc[8, 0]).strip()
        if 9 < max_rows and 0 < max_cols:
            T_set_b2 = str(RAW_DATAFRAME_SET_2_D.iloc[9, 0]).strip()
        if 8 < max_rows and 13 < max_cols:
            T_set_a1 = str(RAW_DATAFRAME_SET_2_D.iloc[8, 13]).strip()
        if 9 < max_rows and 13 < max_cols:
            T_set_a2 = str(RAW_DATAFRAME_SET_2_D.iloc[9, 13]).strip()

    return T_set_b1, T_set_b2, T_set_a1, T_set_a2

def extract_temps_mort_set_3(pdf_file_path: str) -> tuple:
    """Extrait les quatre temps morts du SET 3."""
    RAW_DATAFRAME_SET_3_D = extract_raw_set_3_b(pdf_file_path)
    T_set_a1, T_set_a2, T_set_b1, T_set_b2 = None, None, None, None

    if RAW_DATAFRAME_SET_3_D is not None and not RAW_DATAFRAME_SET_3_D.empty:
        max_rows, max_cols = RAW_DATAFRAME_SET_3_D.shape
        # Indices spécifiques Set 3
        if 8 < max_rows and 1 < max_cols:
            T_set_a1 = str(RAW_DATAFRAME_SET_3_D.iloc[8, 1]).strip()
        if 9 < max_rows and 0 < max_cols:
            T_set_a2 = str(RAW_DATAFRAME_SET_3_D.iloc[9, 0]).strip()
        if 8 < max_rows and 14 < max_cols:
            T_set_b1 = str(RAW_DATAFRAME_SET_3_D.iloc[8, 14]).strip()
        if 9 < max_rows and 13 < max_cols:
            T_set_b2 = str(RAW_DATAFRAME_SET_3_D.iloc[9, 13]).strip()

    return T_set_a1, T_set_a2, T_set_b1, T_set_b2

def extract_temps_mort_set_4(pdf_file_path: str) -> tuple:
    """Extrait les quatre temps morts du SET 4."""
    RAW_DATAFRAME_SET_4_D = extract_raw_set_4_a(pdf_file_path)
    T_set_b1, T_set_b2, T_set_a1, T_set_a2 = None, None, None, None

    if RAW_DATAFRAME_SET_4_D is not None and not RAW_DATAFRAME_SET_4_D.empty:
        max_rows, max_cols = RAW_DATAFRAME_SET_4_D.shape
        if 8 < max_rows and 0 < max_cols:
            T_set_b1 = str(RAW_DATAFRAME_SET_4_D.iloc[8, 0]).strip()
        if 9 < max_rows and 0 < max_cols:
            T_set_b2 = str(RAW_DATAFRAME_SET_4_D.iloc[9, 0]).strip()
        if 8 < max_rows and 13 < max_cols:
            T_set_a1 = str(RAW_DATAFRAME_SET_4_D.iloc[8, 13]).strip()
        if 9 < max_rows and 13 < max_cols:
            T_set_a2 = str(RAW_DATAFRAME_SET_4_D.iloc[9, 13]).strip()

    return T_set_b1, T_set_b2, T_set_a1, T_set_a2

def extract_temps_mort_set_5(pdf_file_path: str) -> tuple:
    """Extrait les temps morts du SET 5 avec logique de substitution."""
    RAW_DATAFRAME_SET_5_D = extract_raw_set_5_b(pdf_file_path)
    T_set_a1, T_set_a2, T_set_b1, T_set_b2 = None, None, None, None

    if RAW_DATAFRAME_SET_5_D is not None and not RAW_DATAFRAME_SET_5_D.empty:
        max_rows, max_cols = RAW_DATAFRAME_SET_5_D.shape

        # Extraction Primaire
        T_set_a1 = str(RAW_DATAFRAME_SET_5_D.iloc[7, 1]).strip() if 7 < max_rows and 1 < max_cols else None
        T_set_a2 = str(RAW_DATAFRAME_SET_5_D.iloc[8, 1]).strip() if 8 < max_rows and 1 < max_cols else None
        T_set_b1 = str(RAW_DATAFRAME_SET_5_D.iloc[7, 14]).strip() if 7 < max_rows and 14 < max_cols else None
        T_set_b2 = str(RAW_DATAFRAME_SET_5_D.iloc[8, 14]).strip() if 8 < max_rows and 14 < max_cols else None

        # Logique de Secours pour l'Équipe A (R16, R17)
        if not T_set_a1 or T_set_a1.lower() == 'none':
            T_set_a1 = str(RAW_DATAFRAME_SET_5_D.iloc[16, 12]).strip() if 16 < max_rows and 12 < max_cols else None
        if not T_set_a2 or T_set_a2.lower() == 'none':
            T_set_a2 = str(RAW_DATAFRAME_SET_5_D.iloc[17, 12]).strip() if 17 < max_rows and 12 < max_cols else None

    return T_set_a1, T_set_a2, T_set_b1, T_set_b2

# ======================================================================
# FONCTION Score - Extraction des données brutes
# ======================================================================

def analyze_data(pdf_file_path: str) -> pd.DataFrame or None:
    """
    Extrait le tableau brut pour les DONNÉES DE SCORE aux coordonnées spécifiées.
    Adapté pour Streamlit.
    """
    # Coordonnées de la zone des scores : [Haut, Gauche, Bas, Droite]
    COORD_SCORES = [300, 140, 842, 595]

    try:
        tables = tabula.read_pdf(
            pdf_file_path,
            pages=1,
            area=COORD_SCORES,
            lattice=True,
            multiple_tables=False,
            pandas_options={'header': None}
        )
        if tables and not tables[0].empty:
            st.toast("✅ Extraction des scores réussie.")
            # Nettoyage : Remplir les NaN par des chaînes vides et s'assurer que tout est en string
            return tables[0].fillna('').astype(str)
        else:
            st.error("❌ Échec de la récupération du tableau pour DONNÉES.")
            return None

    except Exception as e:
        st.error(f"❌ ERREUR lors de l'extraction tabula : {e}")
        return None

# ======================================================================
# FONCTION Structure - Organisation des scores par set
# ======================================================================

def process_and_structure_scores(raw_df_data: pd.DataFrame) -> pd.DataFrame:
    """
    Crée un DataFrame cible de 5 lignes et 2 colonnes (R5 x C2) pour les scores.
    Gère les conditions de vérification sur C2, C5 et C6.
    """
    # Initialisation des variables locales
    resultats = {
        'a': [None]*5, # Scores équipe A (indices 0 à 4)
        'b': [None]*5  # Scores équipe B (indices 0 à 4)
    }

    # Définition des lignes cibles (Index 0-basé)
    ROWS = {1: 28, 2: 29, 3: 30, 4: 31, 5: 32}

    # Configuration des colonnes
    COL_SCORE_GAUCHE = 3
    COL_VERIF_GAUCHE = 2
    COL_SCORE_DROITE_SET_1 = 5
    COL_VERIF_DROITE_SET_1 = 6
    COL_SCORE_DROITE_SET_2_5 = 4
    COL_VERIF_DROITE_SET_2_5 = 5

    # --- A. AFFECTATION ÉQUIPE GAUCHE (COLONNE C3) ---
    for set_num, target_row in ROWS.items():
        if raw_df_data is not None and len(raw_df_data) > target_row:
            score_val = str(raw_df_data.iloc[target_row, COL_SCORE_GAUCHE]).strip()
            verif_val = str(raw_df_data.iloc[target_row, COL_VERIF_GAUCHE]).strip()

            if verif_val in ['0', '1']:
                # Logique alternée A/B selon le set
                if set_num in [1, 3, 5]: resultats['a'][set_num-1] = score_val
                else: resultats['b'][set_num-1] = score_val

    # --- B. AFFECTATION ÉQUIPE DROITE ---
    # Set 1 Droite
    r1 = ROWS[1]
    if raw_df_data is not None and len(raw_df_data) > r1 and len(raw_df_data.columns) > COL_VERIF_DROITE_SET_1:
        if str(raw_df_data.iloc[r1, COL_VERIF_DROITE_SET_1]).strip() in ['0', '1']:
            resultats['b'][0] = str(raw_df_data.iloc[r1, COL_SCORE_DROITE_SET_1]).strip()

    # Sets 2, 3, 4, 5 Droite
    for set_num in [2, 3, 4, 5]:
        target_row = ROWS[set_num]
        if raw_df_data is not None and len(raw_df_data) > target_row and len(raw_df_data.columns) > COL_VERIF_DROITE_SET_2_5:
            score_val = str(raw_df_data.iloc[target_row, COL_SCORE_DROITE_SET_2_5]).strip()
            verif_val = str(raw_df_data.iloc[target_row, COL_VERIF_DROITE_SET_2_5]).strip()

            if verif_val in ['0', '1']:
                if set_num in [2, 4]: resultats['a'][set_num-1] = score_val
                else: resultats['b'][set_num-1] = score_val

    # --- 2. CRÉATION DU DATAFRAME FINAL ---
    df_structured = pd.DataFrame({
        'Scores Gauche (C0)': [resultats['a'][0], resultats['b'][1], resultats['a'][2], resultats['b'][3], resultats['a'][4]],
        'Scores Droite (C1)': [resultats['b'][0], resultats['a'][1], resultats['b'][2], resultats['a'][3], resultats['b'][4]]
    }, index=[f'Set {i}' for i in range(1, 6)])

    st.toast("✅ Scores structurés avec succès.")
    return df_structured


# ======================================================================
# FONCTION Graph Set - Duel Chronologique
# ======================================================================

def tracer_duel_equipes(df_g, df_d, titre="Duel", nom_g="Équipe A", nom_d="Équipe B"):
    """Génère le graphique en barres de l'évolution du score."""
    if df_g is None or df_d is None:
        return

    fig, ax = plt.subplots(figsize=(22, 10))
    current_score_g, current_score_d = 0, 0
    x_labels, x_colors = [], []
    pos_x = 0

    color_g, color_d = '#3498db', '#e67e22'

    # Détection du premier serveur
    val_g_start = str(df_g.iloc[4, 0]).upper().strip()
    ordre_equipes = ['G', 'D'] if val_g_start == 'X' else ['D', 'G']

    compteur_sequence = 1
    for ligne_idx in range(4, 12):
        ligne_g = df_g.iloc[ligne_idx, 0:6]
        ligne_d = df_d.iloc[ligne_idx, 0:6]

        if ligne_g.apply(lambda x: str(x).upper().strip() in ['NAN', '', 'NONE']).all() and \
           ligne_d.apply(lambda x: str(x).upper().strip() in ['NAN', '', 'NONE']).all():
            continue

        debut_bloc = pos_x
        suffixe = "ère" if compteur_sequence == 1 else "ème"
        nom_sequence = f"{compteur_sequence}{suffixe} séquence"

        for col_idx in range(6):
            for equipe in ordre_equipes:
                target_df = df_g if equipe == 'G' else df_d
                this_color = color_g if equipe == 'G' else color_d

                joueur_num = str(target_df.iloc[0, col_idx])
                score_val = target_df.iloc[ligne_idx, col_idx]
                s_str = str(score_val).upper().strip()

                x_labels.append(joueur_num)
                x_colors.append(this_color)

                if s_str != 'X' and s_str not in ['NAN', '', 'NONE']:
                    try:
                        score_fin = int(float(s_str))
                        last_score = current_score_g if equipe == 'G' else current_score_d
                        height = score_fin - last_score
                        if height > 0:
                            ax.bar(pos_x, height, bottom=last_score, color=this_color, edgecolor='black', width=0.4)
                        if equipe == 'G': current_score_g = score_fin
                        else: current_score_d = score_fin
                    except: pass
                pos_x += 1

        ax.text((debut_bloc + pos_x - 1) / 2, -3.2, nom_sequence, ha='center', va='top', fontsize=11, fontweight='bold', color='#555555')
        ax.axvline(x=pos_x - 0.5, color='black', linestyle='-', alpha=0.15)
        compteur_sequence += 1

    ax.set_ylim(0, 35)
    ax.set_yticks(range(0, 36))
    ax.set_xticks(range(len(x_labels)))
    xtick_labels = ax.set_xticklabels(x_labels, fontsize=10, fontweight='bold')
    for i, text_label in enumerate(xtick_labels):
        text_label.set_color(x_colors[i])

    custom_lines = [Line2D([0], [0], color=color_g, lw=4), Line2D([0], [0], color=color_d, lw=4)]
    ax.legend(custom_lines, [nom_g, nom_d], loc='upper left', fontsize=12)
    ax.set_title(titre, fontsize=16, fontweight='bold', pad=25)
    plt.subplots_adjust(bottom=0.2)

    st.pyplot(fig) # Affichage Streamlit
# ======================================================================
# FONCTION Check set - Vérifie si un set a été joué
# ======================================================================
def check_set_exists(df_scores, row_idx):
    """Vérifie si un set a été joué via le tableau récapitulatif des scores."""
    try:
        if df_scores is None or row_idx >= len(df_scores):
            return False
        val = str(df_scores.iloc[row_idx, 0]).upper().strip()
        # On valide que la case contient un score réel
        return val != 'NAN' and val != '' and val != 'NONE'
    except:
        return False

# ======================================================================
# FONCTION Extraction brute et Structure Nom équipe
# ======================================================================
def extract_raw_nom_equipe(pdf_path):
    """Extrait les tableaux du quart supérieur pour identifier les noms."""
    zone_quart_haut = [0, 0, 210, 600]
    try:
        liste_tables = tabula.read_pdf(
            pdf_path,
            pages='all',
            area=zone_quart_haut,
            multiple_tables=True,
            pandas_options={'header': None}
        )
        return liste_tables
    except Exception as e:
        st.error(f"❌ Erreur lors de l'extraction de l'en-tête : {e}")
        return None

def process_and_structure_noms_equipes(pdf_path):
    """Récupère et nettoie les noms des équipes A et B."""
    tables = extract_raw_nom_equipe(pdf_path)
    equipe_a, equipe_b = "Équipe A", "Équipe B"

    if tables and len(tables) > 0:
        df = tables[0]
        try:
            # Récupération et nettoyage (enlève les 2 premiers caractères et "Début")
            raw_a = str(df.iloc[4, 1]).replace('\r', ' ').strip()
            raw_b = str(df.iloc[4, 2]).replace('\r', ' ').strip()
            
            equipe_a = raw_a[2:].split("Début")[0].strip()
            equipe_b = raw_b[2:].split("Début")[0].strip()
        except:
            pass
    return (equipe_a or "Équipe A"), (equipe_b or "Équipe B")

# ======================================================================
# FONCTIONS D'EXTRACTION DES JOUEURS, LIBEROS ET STAFF
# ======================================================================
def extraire_joueurs_df(pdf_path):
    """Extrait la liste des joueurs avant la section LIBEROS."""
    motif = re.compile(r'(\d{2})\s+([A-ZÀ-ÿ\s\-]+?)\s+(\d{5,7})')
    joueurs_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texte = "".join([page.extract_text() for page in pdf.pages])
            zone = texte.split("LIBEROS")[0] if "LIBEROS" in texte else texte
            matches = motif.findall(zone)
            for num, identite, licence in matches:
                joueurs_data.append({"Numero": num, "Identite": identite.strip(), "Licence": licence})
        return pd.DataFrame(joueurs_data).drop_duplicates(subset=['Licence'])
    except:
        return pd.DataFrame(columns=["Numero", "Identite", "Licence"])

def extraire_liberos_df(pdf_path):
    """Extrait les liberos entre les sections LIBEROS et Arbitres."""
    motif = re.compile(r'(\d{2})\s+([A-ZÀ-ÿ\s\-]+?)\s+(\d{5,7})')
    liberos_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texte = "".join([page.extract_text() for page in pdf.pages])
            if "LIBEROS" in texte:
                apres = texte.split("LIBEROS")[1]
                zone = apres.split("Arbitres")[0] if "Arbitres" in apres else apres
                matches = motif.findall(zone)
                for num, identite, licence in matches:
                    liberos_data.append({"Numero": num, "Identite": identite.strip(), "Licence": licence})
        return pd.DataFrame(liberos_data).drop_duplicates(subset=['Licence'])
    except:
        return pd.DataFrame(columns=["Numero", "Identite", "Licence"])

def extraire_staff_df(pdf_path):
    """Extrait le staff (EA, EB, EC) après la section Arbitres."""
    motif_staff = re.compile(r'(E[ABC])\s+([A-ZÀ-ÿ\s\-]+?)\s+(\d{5,7})')
    staff_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texte = "".join([page.extract_text() for page in pdf.pages])
            if "Arbitres" in texte:
                zone = texte.split("Arbitres")[1]
                matches = motif_staff.findall(zone)
                for code, identite, licence in matches:
                    staff_data.append({"Code": code, "Identite": identite.strip(), "Licence": licence})
        return pd.DataFrame(staff_data).drop_duplicates(subset=['Licence'])
    except:
        return pd.DataFrame(columns=["Code", "Identite", "Licence"])

# ======================================================================
# FONCTIONS GRAPHIQUES ET CALCULS
# ======================================================================
def dessiner_rotation_couleurs(ax, nom_a, pos_a, nom_b, pos_b, serveur='A'):
    """Dessine le terrain avec les positions des joueurs."""
    ax.add_patch(patches.Rectangle((0, 0), 18, 9, linewidth=2, edgecolor='black', facecolor='#fafafa'))
    ax.plot([9, 9], [0, 9], color='black', linewidth=3) # Filet
    
    color_a, color_b = 'royalblue', 'darkorange'
    coords_a = {'IV': (7.5, 7.5), 'III': (7.5, 4.5), 'II': (7.5, 1.5), 'V': (3.0, 7.5), 'VI': (3.0, 4.5), 'I': (3.0, 1.5)}
    coords_b = {'II': (10.5, 7.5), 'III': (10.5, 4.5), 'IV': (10.5, 1.5), 'I': (15.0, 7.5), 'VI': (15.0, 4.5), 'V': (15.0, 1.5)}

    if serveur == 'A':
        ax.text(-1.5, 1.5, str(pos_a['I']), fontsize=22, weight='bold', color=color_a, ha='center')
        for p, n in pos_b.items(): ax.text(coords_b[p][0], coords_b[p][1], str(n), fontsize=20, weight='bold', color=color_b, ha='center', va='center')
        for p, n in pos_a.items():
            if p != 'I': ax.text(coords_a[p][0], coords_a[p][1], str(n), fontsize=20, weight='bold', color=color_a, ha='center', va='center')
    else:
        ax.text(19.5, 7.5, str(pos_b['I']), fontsize=22, weight='bold', color=color_b, ha='center')
        for p, n in pos_a.items(): ax.text(coords_a[p][0], coords_a[p][1], str(n), fontsize=20, weight='bold', color=color_a, ha='center', va='center')
        for p, n in pos_b.items():
            if p != 'I': ax.text(coords_b[p][0], coords_b[p][1], str(n), fontsize=20, weight='bold', color=color_b, ha='center', va='center')
    ax.set_xlim(-3, 21); ax.set_ylim(-1, 10); ax.axis('off')

def calculer_sequences_precises(df_a, df_b, col_idx):
    """Calcule les gains réels en soustrayant le score précédent (chronologique)."""
    def to_val(v):
        if str(v).upper() == 'X' or pd.isna(v) or str(v).strip() == '': return None
        try: return float(str(v).replace(',', '.'))
        except: return None

    pts_marques, pts_encaisses = [], []
    for r in range(4, len(df_a)):
        val_a, val_b = to_val(df_a.iloc[r, col_idx]), to_val(df_b.iloc[r, col_idx])
        if val_a is not None or val_b is not None:
            if col_idx == 0:
                if r == 4: prev_a, prev_b = 0.0, 0.0
                else: 
                    prev_a = to_val(df_a.iloc[r-1, 5]) or 0.0
                    prev_b = to_val(df_b.iloc[r-1, 5]) or 0.0
            else:
                prev_a = to_val(df_a.iloc[r, col_idx-1]) or 0.0
                prev_b = to_val(df_b.iloc[r, col_idx-1]) or 0.0
            
            pts_marques.append(int(val_a - prev_a) if val_a is not None else 0)
            pts_encaisses.append(int(val_b - prev_b) if val_b is not None else 0)
    return pts_marques, pts_encaisses
# ======================================================================
# ÉTAPE 3 : Pilotage de l'Analyse et Affichage Dynamique
# ======================================================================

if st.session_state.PDF_FILENAME:
    # 0. 🔍 IDENTIFICATION DES ÉQUIPES
    EQUIPE_A, EQUIPE_B = process_and_structure_noms_equipes(st.session_state.PDF_FILENAME)

    st.markdown(f"### 🏐 MATCH : {EQUIPE_A} 🆚 {EQUIPE_B}")
    
    # Zone d'information (Joueurs, Liberos, Staff) en 3 colonnes
    col_j, col_l, col_s = st.columns(3)
    with col_j:
        with st.expander("👥 Liste des Joueurs", expanded=False):
            st.dataframe(extraire_joueurs_df(st.session_state.PDF_FILENAME), use_container_width=True, hide_index=True)
    with col_l:
        with st.expander("🛡️ Liste des Libéros", expanded=False):
            st.dataframe(extraire_liberos_df(st.session_state.PDF_FILENAME), use_container_width=True, hide_index=True)
    with col_s:
        with st.expander("👔 Staff Technique", expanded=False):
            st.dataframe(extraire_staff_df(st.session_state.PDF_FILENAME), use_container_width=True, hide_index=True)

    # 1. ANALYSE DU TABLEAU RÉCAPITULATIF DES SCORES
    RAW_DATA_SCORES = analyze_data(st.session_state.PDF_FILENAME)
    if RAW_DATA_SCORES is not None:
        FINAL_SCORES = process_and_structure_scores(RAW_DATA_SCORES)
        
        # On renomme les colonnes avec les vrais noms
        FINAL_SCORES.columns = [f"Score {EQUIPE_A}", f"Score {EQUIPE_B}"]
        
        st.divider()
        st.subheader("📊 Récapitulatif des Scores")
        st.table(FINAL_SCORES)

        # 2. CRÉATION DES ONGLETS PAR SET
        sets_joues = [f"Set {i+1}" for i in range(5) if check_set_exists(FINAL_SCORES, i)]
        
        if sets_joues:
            tabs = st.tabs(sets_joues)
            
            for idx, tab_name in enumerate(sets_joues):
                with tabs[idx]:
                    set_num = idx + 1
                    sc_a = FINAL_SCORES.iloc[idx, 0]
                    sc_b = FINAL_SCORES.iloc[idx, 1]
                    
                    st.info(f"🔥 ANALYSE DU {tab_name.upper()} ({EQUIPE_A} {sc_a} - {sc_b} {EQUIPE_B})")
                    
                    # Logique d'extraction et structuration spécifique par Set
                    if set_num == 1:
                        df_a = process_and_structure_set_1_a(extract_raw_set_1_a(st.session_state.PDF_FILENAME))
                        df_b = process_and_structure_set_1_b(extract_raw_set_1_b(st.session_state.PDF_FILENAME))
                        tm = extract_temps_mort_set_1(st.session_state.PDF_FILENAME)
                        n_g, n_d = EQUIPE_A, EQUIPE_B
                    elif set_num == 2:
                        df_b = process_and_structure_set_2_b(extract_raw_set_2_b(st.session_state.PDF_FILENAME))
                        df_a = process_and_structure_set_2_a(extract_raw_set_2_a(st.session_state.PDF_FILENAME))
                        tm = extract_temps_mort_set_2(st.session_state.PDF_FILENAME)
                        n_g, n_d = EQUIPE_B, EQUIPE_A
                    elif set_num == 3:
                        df_a = process_and_structure_set_3_a(extract_raw_set_3_a(st.session_state.PDF_FILENAME))
                        df_b = process_and_structure_set_3_b(extract_raw_set_3_b(st.session_state.PDF_FILENAME))
                        tm = extract_temps_mort_set_3(st.session_state.PDF_FILENAME)
                        n_g, n_d = EQUIPE_A, EQUIPE_B
                    elif set_num == 4:
                        df_b = process_and_structure_set_4_b(extract_raw_set_4_b(st.session_state.PDF_FILENAME))
                        df_a = process_and_structure_set_4_a(extract_raw_set_4_a(st.session_state.PDF_FILENAME))
                        tm = extract_temps_mort_set_4(st.session_state.PDF_FILENAME)
                        n_g, n_d = EQUIPE_B, EQUIPE_A
                    elif set_num == 5:
                        df_a = process_and_structure_set_5_a(extract_raw_set_5_a(st.session_state.PDF_FILENAME))
                        df_b = process_and_structure_set_5_b(extract_raw_set_5_b(st.session_state.PDF_FILENAME))
                        tm = extract_temps_mort_set_5(st.session_state.PDF_FILENAME)
                        n_g, n_d = EQUIPE_A, EQUIPE_B

                    # Affichage des Temps Morts
                    st.write(f"⏱️ **Temps Morts :** {EQUIPE_A} (`{tm[0] or '-'}` , `{tm[1] or '-'}`) | {EQUIPE_B} (`{tm[2] or '-'}` , `{tm[3] or '-'}`)")

                    # Graphique Chronologique (Duel)
                    tracer_duel_equipes(df_a, df_b, titre=f"Évolution {tab_name}", nom_g=n_g, nom_d=n_d)

                    # --- ANALYSE DES ROTATIONS ---
                    st.subheader(f"🔄 Analyse des Rotations - {tab_name}")
                    
                    v_a, v_b = df_a.iloc[0].values, df_b.iloc[0].values
                    r_a = [{'I':v_a[i%6],'II':v_a[(i+1)%6],'III':v_a[(i+2)%6],'IV':v_a[(i+3)%6],'V':v_a[(i+4)%6],'VI':v_a[(i+5)%6]} for i in range(6)]
                    r_b = [{'I':v_b[i%6],'II':v_b[(i+1)%6],'III':v_b[(i+2)%6],'IV':v_b[(i+3)%6],'V':v_b[(i+4)%6],'VI':v_b[(i+5)%6]} for i in range(6)]

                    fig_rot, axes = plt.subplots(6, 2, figsize=(18, 45))
                    for i in range(6):
                        m_a, m_b = calculer_sequences_precises(df_a, df_b, i)
                        
                        # Service Équipe GAUCHE
                        dessiner_rotation_couleurs(axes[i, 0], n_g, r_a[i], n_d, r_b[i], serveur='A')
                        if m_a:
                            s_m_a = "\n".join([f"{k+1}   {v}" for k, v in enumerate(m_a)])
                            s_m_b = "\n".join([f"{k+1}   {v}" for k, v in enumerate(m_b)])
                            s_diff = "\n".join([f"{int(va)-int(vb)}" for va,vb in zip(m_a,m_b)])
                            # Affichage aligné monospace
                            axes[i,0].text(1,-1.5, f"pts marqués\n{s_m_a}\n\nTotal: {sum(m_a)}", family='monospace', weight='bold', va='top', color='royalblue')
                            axes[i,0].text(7,-1.5, f"pts encaissés\n{s_m_b}\n\nTotal: {sum(m_b)}", family='monospace', weight='bold', va='top', color='salmon')
                            axes[i,0].text(13,-1.5, f"différence\n{s_diff}\n\nTotal: {sum(m_a)-sum(m_b):+d}", family='monospace', weight='bold', va='top')

                        # Service Équipe DROITE
                        dessiner_rotation_couleurs(axes[i, 1], n_g, r_a[i], n_d, r_b[i], serveur='B')
                        if m_b:
                            s_m_a = "\n".join([f"{k+1}   {v}" for k, v in enumerate(m_a)])
                            s_m_b = "\n".join([f"{k+1}   {v}" for k, v in enumerate(m_b)])
                            s_diff_b = "\n".join([f"{int(vb)-int(va)}" for va,vb in zip(m_a,m_b)])
                            axes[i,1].text(1,-1.5, f"pts marqués\n{s_m_b}\n\nTotal: {sum(m_b)}", family='monospace', weight='bold', va='top', color='darkorange')
                            axes[i,1].text(7,-1.5, f"pts encaissés\n{s_m_a}\n\nTotal: {sum(m_a)}", family='monospace', weight='bold', va='top', color='royalblue')
                            axes[i,1].text(13,-1.5, f"différence\n{s_diff_b}\n\nTotal: {sum(m_b)-sum(m_a):+d}", family='monospace', weight='bold', va='top')
                    
                    st.pyplot(fig_rot)
else:
    st.warning("👈 Veuillez uploader un fichier PDF dans la barre latérale pour commencer.")
