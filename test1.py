## 🏐 Analyse de Feuille de Match PDF (Volley-Ball)

# ======================================================================
# ÉTAPE 1 : Configuration et Installation
# ======================================================================
print("1. Configuration des dépendances...")

# Installation de tabula-py et tabulate (pour Colab/Jupyter)
!pip install tabula-py tabulate > /dev/null
!pip install pdfplumber
import streamlit as st
import tabula
import pandas as pd
import numpy as np
import pdfplumber
import re
from google.colab import files
from tabulate import tabulate
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D

print("Configuration terminée. Prêt pour l'analyse.")

# ======================================================================
# CONSTANTES GLOBALES
# ======================================================================
TARGET_ROWS = 12
TARGET_COLS = 6
TARGET_COLS_COUNT = 6

# Variables globales pour les DataFrames (initialisées à None)
RAW_DATAFRAME_SET_1_a = None
FINAL_DATAFRAME_a = None
RAW_DATAFRAME_SET_1_b = None
FINAL_DATAFRAME_b = None
# NOUVELLES VARIABLES GLOBALES
RAW_DATAFRAME_SET_2_b = None
FINAL_DATAFRAME_SET_2_b = None
RAW_DATAFRAME_SET_2_a = None # NOUVELLE VARIABLE GLOBALE POUR SET 2 DROITE
FINAL_DATAFRAME_SET_2_a = None # NOUVELLE VARIABLE GLOBALE POUR SET 2 DROITE
PDF_FILENAME = None


# ----------------------------------------------------------------------
# FONCTIONS UTILITAIRES D'AFFICHAGE
# ----------------------------------------------------------------------

def display_dataframe(df: pd.DataFrame, title: str):
    """Affiche un DataFrame brut ou structuré avec les en-têtes R/C."""
    print(f"\n--- {title} ---")
    num_cols = len(df.columns)
    col_headers = [f'C{i}' for i in range(num_cols)]
    data_for_display = []
    # Remplacer NaN par une chaîne vide pour un affichage propre, puis convertir en liste
    df_data = df.fillna('').values.tolist()

    for r_index, row in enumerate(df_data):
        # Ajoute l'en-tête de ligne (R0, R1, etc.)
        data_for_display.append([f'R{r_index}'] + row)

    # Création du tableau pour l'affichage avec tabulate
    tabulate_data = [[''] + col_headers] + data_for_display
    print(tabulate(tabulate_data, tablefmt="fancy_grid", headers="firstrow"))
    #print(f"R: Ligne / C: Colonne (Python). Dimensions: {len(df)} lignes, {num_cols} colonnes.")
    print("--------------------------------------------------")


# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 1 a
# ======================================================================

def extract_raw_set_1_a(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 1 (Équipe a) aux coordonnées spécifiées."""

    # Coordonnées spécifiques pour le Set 1 a
    COORDINATES_TEAM_G = [80, 10, 170, 250]
    #print(f"\n--- Début de l'extraction du tableau brut absolu : Set 1 a (Zone {COORDINATES_TEAM_G}) ---")

    tables = []
    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_TEAM_G, lattice=True, multiple_tables=False, pandas_options={'header': None})
        print("✅ Extraction Set 1 a réussie.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction tabula pour Set 1 a. Détails: {e}")
        return None

    if not tables or tables[0].empty:
        print("❌ Échec de la récupération du tableau pour Set 1 a dans la zone spécifiée.")
        return None

    # Convertir toutes les colonnes en chaîne de caractères
    df_source = tables[0].fillna('').astype(str)
    # display_dataframe(df_source, "TABLEAU SOURCE (BRUT) ÉQUIPE a (SET 1)")
    return df_source

# ======================================================================
# FONCTIONS structure - SET 1 a
# ======================================================================

def process_and_structure_set_1_a(raw_df: pd.DataFrame) -> pd.DataFrame or None:
    """Crée le DataFrame Cible et y transfère toutes les données brutes du Set 1 - Équipe a."""

    # 1. CRÉATION DU TABLEAU CIBLE VIDE
    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_a = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])

    #print(f"\n✅ Transferts COMPLETS pour le Set 1 a en cours...")

    # --- Définition des indices pour l'Équipe a ---

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

    # ÉTAPE 8 : Libero/Rot. L1 (R6 Source -> R4 Cible)
    SOURCE_COL_INDICES_R8 = [3, 5, 7, 9, 11, 13]
    if len(raw_df) > 6 and len(raw_df.columns) > max(SOURCE_COL_INDICES_R8):
        data = raw_df.iloc[6, SOURCE_COL_INDICES_R8].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[4, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 9 : Libero/Rot. L2 (R7 Source -> R5 Cible)
    SOURCE_COL_INDICES_R9 = [2, 4, 6, 8, 10, 12]
    if len(raw_df) > 7 and len(raw_df.columns) > max(SOURCE_COL_INDICES_R9):
        data = raw_df.iloc[7, SOURCE_COL_INDICES_R9].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[5, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 10 : Libero/Rot. L3 (R8 Source -> R6 Cible)
    SOURCE_COL_INDICES_R10 = [2, 4, 6, 8, 10, 12]
    if len(raw_df) > 8 and len(raw_df.columns) > max(SOURCE_COL_INDICES_R10):
        data = raw_df.iloc[8, SOURCE_COL_INDICES_R10].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[6, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 11 : Libero/Rot. L4 (R9 Source -> R7 Cible)
    SOURCE_COL_INDICES_R11 = [2, 4, 6, 8, 10, 12]
    if len(raw_df) > 9 and len(raw_df.columns) > max(SOURCE_COL_INDICES_R11):
        data = raw_df.iloc[9, SOURCE_COL_INDICES_R11].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[7, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 12 : Action L2 - Colonnes paires (R6 Source -> R8 Cible)
    SOURCE_COL_INDICES_R12 = [4, 6, 8, 10, 12, 14]
    if len(raw_df) > 6 and len(raw_df.columns) > max(SOURCE_COL_INDICES_R12):
        data = raw_df.iloc[6, SOURCE_COL_INDICES_R12].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[8, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 13 : Action L3 - Colonnes impaires (R7 Source -> R9 Cible)
    SOURCE_COL_INDICES_R13 = [3, 5, 7, 9, 11, 13]
    if len(raw_df) > 7 and len(raw_df.columns) > max(SOURCE_COL_INDICES_R13):
        data = raw_df.iloc[7, SOURCE_COL_INDICES_R13].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[9, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 14 : Action L4 - Colonnes impaires (R8 Source -> R10 Cible)
    SOURCE_COL_INDICES_R14 = [3, 5, 7, 9, 11, 13]
    if len(raw_df) > 8 and len(raw_df.columns) > max(SOURCE_COL_INDICES_R14):
        data = raw_df.iloc[8, SOURCE_COL_INDICES_R14].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[10, 0:TARGET_COLS_COUNT] = data

    # ÉTAPE 15 : Action L5 - Colonnes impaires (R9 Source -> R11 Cible)
    SOURCE_COL_INDICES_R15 = [3, 5, 7, 9, 11, 13]
    if len(raw_df) > 9 and len(raw_df.columns) > max(SOURCE_COL_INDICES_R15):
        data = raw_df.iloc[9, SOURCE_COL_INDICES_R15].values
        if len(data) == TARGET_COLS_COUNT: FINAL_DATAFRAME_a.iloc[11, 0:TARGET_COLS_COUNT] = data

    #print(f"✅ Transferts COMPLETS pour le Set 1 a terminés.")

    return FINAL_DATAFRAME_a

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 1 b
# ======================================================================

def extract_raw_set_1_b(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 1 (Équipe b) aux coordonnées spécifiées."""

    # Coordonnées spécifiques pour le Set 1 b
    COORDINATES_TEAM_D = [80, 240, 170, 460]
    #print(f"\n--- Début de l'extraction du tableau brut absolu : Set 1 b (Zone {COORDINATES_TEAM_D}) ---")

    tables = []
    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_TEAM_D, lattice=True, multiple_tables=False, pandas_options={'header': None})
        print("✅ Extraction Set 1 b réussie.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction tabula pour Set 1 b. Détails: {e}")
        return None

    if not tables or tables[0].empty:
        print("❌ Échec de la récupération du tableau pour Set 1 b dans la zone spécifiée.")
        return None

    # Convertir toutes les colonnes en chaîne de caractères
    df_source = tables[0].fillna('').astype(str)
    # display_dataframe(df_source, "TABLEAU SOURCE (BRUT) ÉQUIPE b (SET 1)")
    return df_source

# ======================================================================
# FONCTIONS structure - SET 1 b
# ======================================================================

def process_and_structure_set_1_b(raw_df_b: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 1 - Équipe b."""

    # 1. CRÉATION DU TABLEAU CIBLE VIDE
    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_b = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])
    #print(f"\n✅ Tableau Cible Vierge créé : {TARGET_ROWS} lignes x {TARGET_COLS} colonnes dans `FINAL_DATAFRAME_b` (Set 1 Équipe b).")

    # --- DÉBUT DES TRANSFERTS SET 1 ÉQUIPE b ---

    # Définition des indices de colonne C1 à C6 (index Python 1:7)
    SOURCE_COL_START_C1_C6 = 1
    SOURCE_COL_END_C1_C6 = 7
    TARGET_ROW_START_INDEX = 0

    # Définition des indices pour les transferts par colonnes paires/impaires
    # Colonnes impaires C1, C3, C5, C7, C9, C11 (Indices Python 1, 3, 5, 7, 9, 11)
    SOURCE_COL_INDICES_ODD_C1_C11 = [1, 3, 5, 7, 9, 11]
    # Colonnes paires C2, C4, C6, C8, C10, C12 (Indices Python 2, 4, 6, 8, 10, 12)
    SOURCE_COL_INDICES_EVEN_C2_C12 = [2, 4, 6, 8, 10, 12]
    # Colonnes impaires C3, C5, C7, C9, C11, C13 (Indices Python 3, 5, 7, 9, 11, 13)
    SOURCE_COL_INDICES_ODD_C3_C13 = [3, 5, 7, 9, 11, 13]

    # TRANSFERT 1 : Formation de Départ (R2 Source -> R0 Cible)
    SOURCE_ROW_INDEX = 2
    if len(raw_df_b) > SOURCE_ROW_INDEX:
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_START_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 1 (Formation de Départ) Set 1 Droite : R{SOURCE_ROW_INDEX} C1-C6 Source -> R0 Cible effectué.")

    # TRANSFERT 2 : Remplaçants (R3 Source -> R1 Cible)
    SOURCE_ROW_INDEX = 3
    if len(raw_df_b) > SOURCE_ROW_INDEX:
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_START_INDEX + 1, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 2 (Remplaçants) Set 1 Droite : R{SOURCE_ROW_INDEX} C1-C6 Source -> R1 Cible effectué.")

    # TRANSFERT 3 : Score (R4 Source -> R2 Cible)
    SOURCE_ROW_INDEX = 4
    if len(raw_df_b) > SOURCE_ROW_INDEX:
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_START_INDEX + 2, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 3 (Score) Set 1 Droite : R{SOURCE_ROW_INDEX} C1-C6 Source -> R2 Cible effectué.")

    # TRANSFERT 4 : Première Ligne d'Action (R5 Source -> R3 Cible)
    SOURCE_ROW_INDEX = 5
    if len(raw_df_b) > SOURCE_ROW_INDEX:
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_START_INDEX + 3, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 4 (Première Ligne d'Action) Set 1 Droite : R{SOURCE_ROW_INDEX} C1-C6 Source -> R3 Cible effectué.")


    # TRANSFERT 5 : Libero/Rot. L1 (R6 Source, Colonnes Impaires C1-C11 -> R4 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 4
    if len(raw_df_b) > SOURCE_ROW_INDEX and len(raw_df_b.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 5 (Libero/Rot. Ligne 1) Set 1 Droite : R{SOURCE_ROW_INDEX} C_impaires C1-C11 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 6 : Libero/Rot. L2 (R7 Source, Colonnes Paires C2-C12 -> R5 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 5
    if len(raw_df_b) > SOURCE_ROW_INDEX and len(raw_df_b.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 6 (Libero/Rot. Ligne 2) Set 1 Droite : R{SOURCE_ROW_INDEX} C_paires C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 7 : Libero/Rot. L3 (R8 Source, Colonnes Paires C2-C12 -> R6 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 6
    if len(raw_df_b) > SOURCE_ROW_INDEX and len(raw_df_b.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 7 (Libero/Rot. Ligne 3) Set 1 Droite : R{SOURCE_ROW_INDEX} C_paires C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 8 : Libero/Rot. L4 (R9 Source, Colonnes Paires C2-C12 -> R7 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 7
    if len(raw_df_b) > SOURCE_ROW_INDEX and len(raw_df_b.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 8 (Libero/Rot. Ligne 4) Set 1 Droite : R{SOURCE_ROW_INDEX} C_paires C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 9 : Action L2 (R6 Source, Colonnes Paires C2-C12 -> R8 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 8
    if len(raw_df_b) > SOURCE_ROW_INDEX and len(raw_df_b.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 9 (Action Ligne 2) Set 1 Droite : R{SOURCE_ROW_INDEX} C_paires C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 10 : Action L3 (R7 Source, Colonnes Impaires C3-C13 -> R9 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 9
    if len(raw_df_b) > SOURCE_ROW_INDEX and len(raw_df_b.columns) > max(SOURCE_COL_INDICES_ODD_C3_C13):
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C3_C13].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 10 (Action Ligne 3) Set 1 Droite : R{SOURCE_ROW_INDEX} C_impaires C3-C13 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 11 : Action L4 (R8 Source, Colonnes Impaires C3-C13 -> R10 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 10
    if len(raw_df_b) > SOURCE_ROW_INDEX and len(raw_df_b.columns) > max(SOURCE_COL_INDICES_ODD_C3_C13):
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C3_C13].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 11 (Action Ligne 4) Set 1 Droite : R{SOURCE_ROW_INDEX} C_impaires C3-C13 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 12 : Action L5 (R9 Source, Colonnes Impaires C3-C13 -> R11 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 11
    if len(raw_df_b) > SOURCE_ROW_INDEX and len(raw_df_b.columns) > max(SOURCE_COL_INDICES_ODD_C3_C13):
        data = raw_df_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C3_C13].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 12 (Action Ligne 5) Set 1 Droite : R{SOURCE_ROW_INDEX} C_impaires C3-C13 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # --- FIN DES TRANSFERTS SET 1 ÉQUIPE DROITE ---

    return FINAL_DATAFRAME_b



# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 2 b
# ======================================================================

def extract_raw_set_2_b(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 2 (Équipe a) aux coordonnées spécifiées."""

    COORDINATES_SET_2_G = [80, 460, 170, 590]
    #print(f"\n--- Début de l'extraction du tableau brut absolu : Set 2 b (Zone {COORDINATES_SET_2_G}) ---")

    tables = []
    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_2_G, lattice=True, multiple_tables=False, pandas_options={'header': None})
        print("✅ Extraction Set 2 b réussie.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction tabula pour Set 2 b. Détails: {e}")
        return None

    if not tables or tables[0].empty:
        print("❌ Échec de la récupération du tableau pour Set 2 b dans la zone spécifiée.")
        return None

    # Convertir toutes les colonnes en chaîne de caractères
    df_source = tables[0].fillna('').astype(str)
    # display_dataframe(df_source, "TABLEAU SOURCE (BRUT) ÉQUIPE b (SET 2)")
    return df_source

# ======================================================================
# FONCTIONS structure - SET 2 b
# ======================================================================

def process_and_structure_set_2_b(raw_df_s2_b: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 2 - Équipe b."""

    # 1. CRÉATION DU TABLEAU CIBLE VIDE
    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_2_b = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])
    #print(f"\n✅ Tableau Cible Vierge créé : {TARGET_ROWS} lignes x {TARGET_COLS} colonnes dans `FINAL_DATAFRAME_SET_2_b` (Set 2 Équipe b).")

    # --- DÉBUT DES TRANSFERTS SET 2 ÉQUIPE b ---

    # Définition des indices de colonne C1 à C6 (index Python 1:7)
    SOURCE_COL_START_C1_C6 = 0
    SOURCE_COL_END_C1_C6 = 6
    TARGET_ROW_START_INDEX = 0

    # Définition des indices pour les transferts par colonnes paires/impaires
    # Colonnes impaires C1, C3, C5, C7, C9, C11 (Indices Python 1, 3, 5, 7, 9, 11)
    SOURCE_COL_INDICES_ODD_C1_C11 = [1, 3, 5, 7, 9, 11]
    # Colonnes paires C2, C4, C6, C8, C10, C12 (Indices Python 2, 4, 6, 8, 10, 12)
    SOURCE_COL_INDICES_EVEN_C0_C10 = [0,2, 4, 6, 8, 10]

    # TRANSFERT 1 : Formation de Départ (R2 Source -> R0 Cible)
    SOURCE_ROW_INDEX = 2
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX:
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_START_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 1 (Formation de Départ) Set 2 G : R{SOURCE_ROW_INDEX} C1-C6 Source -> R0 Cible effectué.")

    # TRANSFERT 2 : Remplaçants (R3 Source -> R1 Cible)
    SOURCE_ROW_INDEX = 3
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX:
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_START_INDEX + 1, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 2 (Remplaçants) Set 2 G : R{SOURCE_ROW_INDEX} C1-C6 Source -> R1 Cible effectué.")

    # TRANSFERT 3 : Score (R4 Source -> R2 Cible)
    SOURCE_ROW_INDEX = 4
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX:
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_START_INDEX + 2, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 3 (Score) Set 2 G : R{SOURCE_ROW_INDEX} C1-C6 Source -> R2 Cible effectué.")

    # TRANSFERT 4 : Première Ligne d'Action (R5 Source -> R3 Cible)
    SOURCE_ROW_INDEX = 5
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX:
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_START_INDEX + 3, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 4 (Première Ligne d'Action) Set 2 G : R{SOURCE_ROW_INDEX} C1-C6 Source -> R3 Cible effectué.")


    # TRANSFERT 5 : Libero/Rot. L1 (R6 Source, Colonnes paires C0-C10 -> R4 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 4
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX and len(raw_df_s2_b.columns) > max(SOURCE_COL_INDICES_EVEN_C0_C10):
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C0_C10].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 5 (Libero/Rot. Ligne 1) Set 2 G : R{SOURCE_ROW_INDEX} C_paires C0-C10 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 6 : Libero/Rot. L2 (R7 Source, Colonnes paires C0-C10 -> R5 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 5
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX and len(raw_df_s2_b.columns) > max(SOURCE_COL_INDICES_EVEN_C0_C10):
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C0_C10].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 6 (Libero/Rot. Ligne 2) Set 2 G : R{SOURCE_ROW_INDEX} C_paires C0-C10 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 7 : Libero/Rot. L3 (R8 Source, Colonnes paires C0-C10 -> R6 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 6
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX and len(raw_df_s2_b.columns) > max(SOURCE_COL_INDICES_EVEN_C0_C10):
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C0_C10].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 7 (Libero/Rot. Ligne 3) Set 2 G : R{SOURCE_ROW_INDEX} C_paires C0-C10 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 8 : Libero/Rot. L4 (R9 Source, Colonnes paires C0-C10 -> R7 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 7
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX and len(raw_df_s2_b.columns) > max(SOURCE_COL_INDICES_EVEN_C0_C10):
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C0_C10].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 8 (Libero/Rot. Ligne 4) Set 2 G : R{SOURCE_ROW_INDEX} C_paires C0-C10 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 9 : Action L2 (R6 Source, Colonnes imPaires C1-C11 -> R8 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 8
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX and len(raw_df_s2_b.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 5 (Libero/Rot. Ligne 1) Set 2 G : R{SOURCE_ROW_INDEX} C_impaires C1-C11 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 10 : Action L3 (R7 Source, Colonnes imPaires C1-C11 -> R9 Cible)
    SOURCE_ROW_INDEX = 7 # R7
    TARGET_ROW_INDEX = 9 # R9
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX and len(raw_df_s2_b.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 5 (Libero/Rot. Ligne 1) Set 2 G : R{SOURCE_ROW_INDEX} C_impaires C1-C11 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 11 : Action L4 (R8 Source, Colonnes imPaires C1-C11 -> R10 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 10
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX and len(raw_df_s2_b.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 5 (Libero/Rot. Ligne 1) Set 2 G : R{SOURCE_ROW_INDEX} C_impaires C1-C11 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 12 : Action L5 (R9 Source, Colonnes imPaires C1-C11 -> R11 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 11
    if len(raw_df_s2_b) > SOURCE_ROW_INDEX and len(raw_df_s2_b.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s2_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 5 (Libero/Rot. Ligne 1) Set 2 G : R{SOURCE_ROW_INDEX} C_impaires C1-C11 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # --- FIN DES TRANSFERTS SET 2 ÉQUIPE b ---

    return FINAL_DATAFRAME_SET_2_b

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 2 a
# ======================================================================

def extract_raw_set_2_a(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 2 (Équipe a) aux coordonnées spécifiées."""

    COORDINATES_SET_2_D = [80, 590, 170, 850] # NOUVELLES COORDONNÉES
    #print(f"\n--- Début de l'extraction du tableau brut absolu : Set 2 a (Zone {COORDINATES_SET_2_D}) ---")

    tables = []
    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_2_D, lattice=True, multiple_tables=False, pandas_options={'header': None})
        print("✅ Extraction Set 2 a réussie.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction tabula pour Set 2 a. Détails: {e}")
        return None

    if not tables or tables[0].empty:
        print("❌ Échec de la récupération du tableau pour Set 2 a dans la zone spécifiée.")
        return None

    # Convertir toutes les colonnes en chaîne de caractères
    df_source = tables[0].fillna('').astype(str)
    # display_dataframe(df_source, "TABLEAU SOURCE (BRUT) ÉQUIPE a (SET 2)")
    return df_source

# ======================================================================
# FONCTIONS structure - SET 2 a
# ======================================================================

def process_and_structure_set_2_a(raw_df_s2_a: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 2 - Équipe a."""

    # 1. CRÉATION DU TABLEAU CIBLE VIDE
    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_2_a = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])
    #print(f"\n✅ Tableau Cible Vierge créé : {TARGET_ROWS} lignes x {TARGET_COLS} colonnes dans `FINAL_DATAFRAME_SET_2_a` (Set 2 Équipe a).")

    # --- DÉBUT DES TRANSFERTS SET 2 ÉQUIPE a ---

    # Définition des indices de colonne C1 à C6 (index Python 1:7)
    SOURCE_COL_START_C1_C6 = 1
    SOURCE_COL_END_C1_C6 = 7
    TARGET_ROW_START_INDEX = 0

    # Définition des indices pour les transferts par colonnes paires/impaires
    # Colonnes impaires C1, C3, C5, C7, C9, C11 (Indices Python 1, 3, 5, 7, 9, 11)
    SOURCE_COL_INDICES_ODD_C1_C11 = [1, 3, 5, 7, 9, 11]
    # Colonnes paires C2, C4, C6, C8, C10, C12 (Indices Python 2, 4, 6, 8, 10, 12)
    SOURCE_COL_INDICES_EVEN_C2_C12 = [2, 4, 6, 8, 10, 12]

    # TRANSFERT 1 : Formation de Départ (R2 Source -> R0 Cible)
    SOURCE_ROW_INDEX = 2
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX:
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_START_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 1 (Formation de Départ) Set 2 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R0 Cible effectué.")

    # TRANSFERT 2 : Remplaçants (R3 Source -> R1 Cible)
    SOURCE_ROW_INDEX = 3
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX:
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_START_INDEX + 1, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 2 (Remplaçants) Set 2 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R1 Cible effectué.")

    # TRANSFERT 3 : Score (R4 Source -> R2 Cible)
    SOURCE_ROW_INDEX = 4
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX:
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_START_INDEX + 2, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 3 (Score) Set 2 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R2 Cible effectué.")

    # TRANSFERT 4 : Première Ligne d'Action (R5 Source -> R3 Cible)
    SOURCE_ROW_INDEX = 5
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX:
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_START_INDEX + 3, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 4 (Première Ligne d'Action) Set 2 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R3 Cible effectué.")


    # TRANSFERT 5 : Libero/Rot. L1 (R6 Source, Colonnes Impaires C1-C11 -> R4 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 4
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX and len(raw_df_s2_a.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 5 (Libero/Rot. Ligne 1) Set 2 D : R{SOURCE_ROW_INDEX} C_impaires C1-C11 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 6 : Libero/Rot. L2 (R7 Source, Colonnes Impaires C1-C11 -> R5 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 5
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX and len(raw_df_s2_a.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 6 (Libero/Rot. Ligne 2) Set 2 D : R{SOURCE_ROW_INDEX} C_impaires C1-C11 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 7 : Libero/Rot. L3 (R8 Source, Colonnes Impaires C1-C11 -> R6 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 6
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX and len(raw_df_s2_a.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 7 (Libero/Rot. Ligne 3) Set 2 D : R{SOURCE_ROW_INDEX} C_impaires C1-C11 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 8 : Libero/Rot. L4 (R9 Source, Colonnes Impaires C1-C11 -> R7 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 7
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX and len(raw_df_s2_a.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 8 (Libero/Rot. Ligne 4) Set 2 D : R{SOURCE_ROW_INDEX} C_impaires C1-C11 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 9 : Action L2 (R6 Source, Colonnes Paires C2-C12 -> R8 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 8
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX and len(raw_df_s2_a.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 9 (Action Ligne 2) Set 2 D : R{SOURCE_ROW_INDEX} C_paires C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 10 : Action L3 (R7 Source, Colonnes Paires C2-C12 -> R9 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 9
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX and len(raw_df_s2_a.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 10 (Action Ligne 3) Set 2 D : R{SOURCE_ROW_INDEX} C_paires C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 11 : Action L4 (R8 Source, Colonnes Paires C2-C12 -> R10 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 10
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX and len(raw_df_s2_a.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 11 (Action Ligne 4) Set 2 D : R{SOURCE_ROW_INDEX} C_paires C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 12 : Action L5 (R9 Source, Colonnes Paires C2-C12 -> R11 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 11
    if len(raw_df_s2_a) > SOURCE_ROW_INDEX and len(raw_df_s2_a.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s2_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_2_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 12 (Action Ligne 5) Set 2 D : R{SOURCE_ROW_INDEX} C_paires C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # --- FIN DES TRANSFERTS SET 2 ÉQUIPE DROITE ---

    return FINAL_DATAFRAME_SET_2_a


# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 3 a
# ======================================================================

def extract_raw_set_3_a(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 3 (Équipe Gauache, Milieu-a) aux coordonnées spécifiées."""

    COORDINATES_SET_3_G = [170, 10, 260, 250]
    #print(f"\n--- Début de l'extraction du tableau brut absolu : Set 3 a (Zone {COORDINATES_SET_3_G}) ---")

    tables = []
    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_3_G, lattice=True, multiple_tables=False, pandas_options={'header': None})
        print("✅ Extraction Set 3 a réussie.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction tabula pour Set 3 a. Détails: {e}")
        return None

    if not tables or tables[0].empty:
        print("❌ Échec de la récupération du tableau pour Set 3 a dans la zone spécifiée.")
        return None

    df_source = tables[0].fillna('').astype(str)
    # display_dataframe(df_source, "TABLEAU SOURCE (BRUT) ÉQUIPE a (SET 3)")
    return df_source

# ======================================================================
# FONCTIONS structure - SET 3 a
# ======================================================================

def process_and_structure_set_3_a(raw_df_s3_a: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 3 - Équipe a."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_3_a = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])
    #print(f"\n✅ Tableau Cible Vierge créé : {TARGET_ROWS} lignes x {TARGET_COLS} colonnes dans `FINAL_DATAFRAME_SET_3_a` (Set 3 Équipe a).")

    # --- DÉBUT DES TRANSFERTS SET 3 ÉQUIPE a ---

    # Définition des constantes de colonnes (Réutilisées pour la clarté)
    SOURCE_COL_INDICES_ODD_R6 = [3, 5, 7, 9, 11, 13]  # Libero/Rot. L1 (R6)
    SOURCE_COL_INDICES_EVEN_R7_R9 = [2, 4, 6, 8, 10, 12]  # Libero/Rot. L2, L3, L4 (R7, R8, R9)
    SOURCE_COL_INDICES_EVEN_ACTION_R6 = [4, 6, 8, 10, 12, 14] # Action L2 (R6)
    SOURCE_COL_INDICES_ODD_ACTION_R7_R9 = [3, 5, 7, 9, 11, 13] # Action L3, L4, L5 (R7, R8, R9)

    # TRANSFERT 1 : Formation de Départ (R2 Source -> R0 Cible)
    SOURCE_ROW_INDEX = 2
    TARGET_ROW_INDEX = 0
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX:
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, 1:7].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 1 (Formation de Départ) Set 3 G : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 2 : Remplaçants (R3 Source -> R1 Cible)
    SOURCE_ROW_INDEX = 3
    TARGET_ROW_INDEX = 1
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX:
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, 2:8].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 2 (Remplaçants) Set 3 G : R{SOURCE_ROW_INDEX} C2-C7 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 3 : Score (R4 Source -> R2 Cible)
    SOURCE_ROW_INDEX = 4
    TARGET_ROW_INDEX = 2
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX:
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, 2:8].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 3 (Score) Set 3 G : R{SOURCE_ROW_INDEX} C2-C7 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 4 : Première Ligne d'Action (R5 Source -> R3 Cible)
    SOURCE_ROW_INDEX = 5
    TARGET_ROW_INDEX = 3
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX:
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, 3:9].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 4 (Première Ligne d'Action) Set 3 G : R{SOURCE_ROW_INDEX} C3-C8 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 5 : Libero/Rot. L1 (R6 Source, indices impairs -> R4 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 4
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX and len(raw_df_s3_a.columns) > max(SOURCE_COL_INDICES_ODD_R6):
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_R6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 5 (Libero/Rot. Ligne 1) Set 3 G : R{SOURCE_ROW_INDEX} C_impairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 6 : Libero/Rot. L2 (R7 Source, indices pairs -> R5 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 5
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX and len(raw_df_s3_a.columns) > max(SOURCE_COL_INDICES_EVEN_R7_R9):
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_R7_R9].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 6 (Libero/Rot. Ligne 2) Set 3 G : R{SOURCE_ROW_INDEX} C_pairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 7 : Libero/Rot. L3 (R8 Source, indices pairs -> R6 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 6
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX and len(raw_df_s3_a.columns) > max(SOURCE_COL_INDICES_EVEN_R7_R9):
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_R7_R9].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 7 (Libero/Rot. Ligne 3) Set 3 G : R{SOURCE_ROW_INDEX} C_pairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 8 : Libero/Rot. L4 (R9 Source, indices pairs -> R7 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 7
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX and len(raw_df_s3_a.columns) > max(SOURCE_COL_INDICES_EVEN_R7_R9):
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_R7_R9].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 8 (Libero/Rot. Ligne 4) Set 3 G : R{SOURCE_ROW_INDEX} C_pairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 9 : Action L2 (R6 Source, indices pairs -> R8 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 8
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX and len(raw_df_s3_a.columns) > max(SOURCE_COL_INDICES_EVEN_ACTION_R6):
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_ACTION_R6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 9 (Action Ligne 2) Set 3 G : R{SOURCE_ROW_INDEX} C_pairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 10 : Action L3 (R7 Source, indices impairs -> R9 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 9
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX and len(raw_df_s3_a.columns) > max(SOURCE_COL_INDICES_ODD_ACTION_R7_R9):
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_ACTION_R7_R9].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 10 (Action Ligne 3) Set 3 G : R{SOURCE_ROW_INDEX} C_impairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 11 : Action L4 (R8 Source, indices impairs -> R10 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 10
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX and len(raw_df_s3_a.columns) > max(SOURCE_COL_INDICES_ODD_ACTION_R7_R9):
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_ACTION_R7_R9].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 11 (Action Ligne 4) Set 3 G : R{SOURCE_ROW_INDEX} C_impairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 12 : Action L5 (R9 Source, indices impairs -> R11 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 11
    if len(raw_df_s3_a) > SOURCE_ROW_INDEX and len(raw_df_s3_a.columns) > max(SOURCE_COL_INDICES_ODD_ACTION_R7_R9):
        data = raw_df_s3_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_ACTION_R7_R9].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 12 (Action Ligne 5) Set 3 G : R{SOURCE_ROW_INDEX} C_impairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # --- FIN DES TRANSFERTS SET 3 ÉQUIPE GAUCHE ---
    #print(f"✅ Transferts COMPLETS pour le Set 3 Gauche terminés.")

    return FINAL_DATAFRAME_SET_3_a

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 3 b
# ======================================================================

def extract_raw_set_3_b(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 3 (Équipe b) aux coordonnées spécifiées."""

    COORDINATES_SET_3_D = [170, 240, 260, 470]
    #print(f"\n--- Début de l'extraction du tableau brut absolu : Set 3 b (Zone {COORDINATES_SET_3_D}) ---")

    tables = []
    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_3_D, lattice=True, multiple_tables=False, pandas_options={'header': None})
        print("✅ Extraction Set 3 b réussie.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction tabula pour Set 3 b. Détails: {e}")
        return None

    if not tables or tables[0].empty:
        print("❌ Échec de la récupération du tableau pour Set 3 b dans la zone spécifiée.")
        return None

    df_source = tables[0].fillna('').astype(str)
    # display_dataframe(df_source, "TABLEAU SOURCE (BRUT) ÉQUIPE b (SET 3)")
    return df_source

# ======================================================================
# FONCTIONS structure - SET 3 b
# ======================================================================

def process_and_structure_set_3_b(raw_df_s3_b: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 3 - Équipe Droite."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_3_b = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])
    #print(f"\n✅ Tableau Cible Vierge créé : {TARGET_ROWS} lignes x {TARGET_COLS} colonnes dans `FINAL_DATAFRAME_SET_3_b` (Set 3 Équipe Droite).")

    # --- DÉBUT DES TRANSFERTS SET 3 ÉQUIPE DROITE ---

    SOURCE_COL_START_C1_C6 = 1
    SOURCE_COL_END_C1_C6 = 7
    TARGET_ROW_START_INDEX = 0

    SOURCE_COL_INDICES_ODD_C1_C11 = [1, 3, 5, 7, 9, 11] # Indices impairs utilisés pour Rot. L1 et Rot. L4
    SOURCE_COL_INDICES_EVEN_C2_C12 = [2, 4, 6, 8, 10, 12] # Indices pairs utilisés pour Rot. L2, L3, Action L2, Action L5
    SOURCE_COL_INDICES_ODD_C3_C13 = [3, 5, 7, 9, 11, 13] # Indices impairs utilisés pour Action L3, L4

    # TRANSFERT 1 : Formation de Départ (R2 Source -> R0 Cible)
    SOURCE_ROW_INDEX = 2
    TARGET_ROW_INDEX = 0
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX:
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_START_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 1 (Formation de Départ) Set 3 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 2 : Remplaçants (R3 Source -> R1 Cible)
    SOURCE_ROW_INDEX = 3
    TARGET_ROW_INDEX = 1
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX:
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_START_INDEX + 1, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 2 (Remplaçants) Set 3 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 3 : Score (R4 Source -> R2 Cible)
    SOURCE_ROW_INDEX = 4
    TARGET_ROW_INDEX = 2
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX:
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_START_INDEX + 2, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 3 (Score) Set 3 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 4 : Première Ligne d'Action (R5 Source -> R3 Cible)
    SOURCE_ROW_INDEX = 5
    TARGET_ROW_INDEX = 3
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX:
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_START_INDEX + 3, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 4 (Première Ligne d'Action) Set 3 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 5 : Libero/Rot. L1 (R6 Source, Colonnes Impaires C1-C11 -> R4 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 4
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX and len(raw_df_s3_b.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 5 (Libero/Rot. Ligne 1) Set 3 D : R{SOURCE_ROW_INDEX} C_impairs C1-C11 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 6 : Libero/Rot. L2 (R7 Source, Colonnes Paires C2-C12 -> R5 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 5
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX and len(raw_df_s3_b.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 6 (Libero/Rot. Ligne 2) Set 3 D : R{SOURCE_ROW_INDEX} C_pairs C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 7 : Libero/Rot. L3 (R8 Source, Colonnes Paires C2-C12 -> R6 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 6
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX and len(raw_df_s3_b.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 7 (Libero/Rot. Ligne 3) Set 3 D : R{SOURCE_ROW_INDEX} C_pairs C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 8 : Libero/Rot. L4 (R9 Source, Colonnes Impaires C1-C11 -> R7 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 7
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX and len(raw_df_s3_b.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 8 (Libero/Rot. Ligne 4) Set 3 D : R{SOURCE_ROW_INDEX} C_impairs C1-C11 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 9 : Action L2 (R6 Source, Colonnes Paires C2-C12 -> R8 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 8
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX and len(raw_df_s3_b.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 9 (Action Ligne 2) Set 3 D : R{SOURCE_ROW_INDEX} C_pairs C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")


    # TRANSFERT 10 : Action L3 (R7 Source, Colonnes Impaires C3-C13 -> R9 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 9
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX and len(raw_df_s3_b.columns) > max(SOURCE_COL_INDICES_ODD_C3_C13):
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C3_C13].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 10 (Action Ligne 3) Set 3 D : R{SOURCE_ROW_INDEX} C_impairs C3-C13 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 11 : Action L4 (R8 Source, Colonnes Impaires C3-C13 -> R10 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 10
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX and len(raw_df_s3_b.columns) > max(SOURCE_COL_INDICES_ODD_C3_C13):
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C3_C13].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 11 (Action Ligne 4) Set 3 D : R{SOURCE_ROW_INDEX} C_impairs C3-C13 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 12 : Action L5 (R9 Source, Colonnes Paires C2-C12 -> R11 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 11
    if len(raw_df_s3_b) > SOURCE_ROW_INDEX and len(raw_df_s3_b.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s3_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_3_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 12 (Action Ligne 5) Set 3 D : R{SOURCE_ROW_INDEX} C_pairs C2-C12 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # --- FIN DES TRANSFERTS SET 3 ÉQUIPE DROITE ---
    #print(f"✅ Transferts COMPLETS pour l'Équipe Droite (SET 3) terminés.")

    return FINAL_DATAFRAME_SET_3_b

# Nécessite que 'extract_raw_set_3_b' soit défini (voir les réponses précédentes)

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 4 b
# ======================================================================

def extract_raw_set_4_b(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 4 (Équipe b) aux coordonnées spécifiées."""

    COORDINATES_SET_4_G = [170, 400, 260, 590]
    #print(f"\n--- Début de l'extraction du tableau brut absolu : Set 4 b (Zone {COORDINATES_SET_4_G}) ---")

    tables = []
    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_4_G, lattice=True, multiple_tables=False, pandas_options={'header': None})
        print("✅ Extraction Set 4 b réussie.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction tabula pour Set 4 b. Détails: {e}")
        return None

    if not tables or tables[0].empty:
        print("❌ Échec de la récupération du tableau pour Set 4 b dans la zone spécifiée.")
        return None

    df_source = tables[0].fillna('').astype(str)
    # display_dataframe(df_source, "TABLEAU SOURCE (BRUT) ÉQUIPE b (SET 4)")
    return df_source

# ======================================================================
# FONCTIONS structure - SET 4 b
# ======================================================================

def process_and_structure_set_4_b(raw_df_s4_b: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 4 - Équipe b."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_4_b = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])
    #print(f"\n✅ Tableau Cible Vierge créé : {TARGET_ROWS} lignes x {TARGET_COLS} colonnes dans `FINAL_DATAFRAME_SET_4_b` (Set 4 Équipe b).")

    # --- DÉBUT DES TRANSFERTS SET 4 ÉQUIPE b ---

    # Définition des constantes d'indices de colonnes pour la clarté
    SOURCE_COLS_R2_R5 = (1, 7) # C1 à C6 (index Python 1:7) pour les 4 premières lignes

    SOURCE_COL_INDICES_ODD_R6_R9 = [1, 3, 5, 7, 9, 11] # Libero/Rot. L1, L2, L3
    SOURCE_COL_INDICES_EVEN_R7_R8 = [2, 4, 6, 8, 10,12] # Libero/Rot. L4

    SOURCE_COL_INDICES_EVEN_ACTION_R6_R9 = [2, 4, 6, 8, 10, 12] # Action L2, L3, L4
    SOURCE_COL_INDICES_ODD_ACTION_R7_R8 = [3, 5, 7, 9, 11,13] # Action L5

    # TRANSFERT 1 : Formation de Départ (R2 Source -> R0 Cible)
    SOURCE_ROW_INDEX = 2
    TARGET_ROW_INDEX = 0
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX:
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COLS_R2_R5[0]:SOURCE_COLS_R2_R5[1]].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 1 (Formation de Départ) Set 4 G : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 2 : Remplaçants (R3 Source -> R1 Cible)
    SOURCE_ROW_INDEX = 3
    TARGET_ROW_INDEX = 1
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX:
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COLS_R2_R5[0]:SOURCE_COLS_R2_R5[1]].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 2 (Remplaçants) Set 4 G : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 3 : Score (R4 Source -> R2 Cible)
    SOURCE_ROW_INDEX = 4
    TARGET_ROW_INDEX = 2
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX:
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COLS_R2_R5[0]:SOURCE_COLS_R2_R5[1]].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 3 (Score) Set 4 G : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 4 : Première Ligne d'Action (R5 Source -> R3 Cible)
    SOURCE_ROW_INDEX = 5
    TARGET_ROW_INDEX = 3
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX:
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COLS_R2_R5[0]:SOURCE_COLS_R2_R5[1]].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 4 (Première Ligne d'Action) Set 4 G : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 5 : Libero/Rot. L1 (R6 Source, indices impairs -> R4 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 4
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX and len(raw_df_s4_b.columns) > max(SOURCE_COL_INDICES_ODD_R6_R9):
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_R6_R9].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 5 (Libero/Rot. Ligne 1) Set 4 G : R{SOURCE_ROW_INDEX} C_impairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 6 : Libero/Rot. L2 (R7 Source, indices impairs -> R5 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 5
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX and len(raw_df_s4_b.columns) > max(SOURCE_COL_INDICES_EVEN_R7_R8):
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_R7_R8].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 6 (Libero/Rot. Ligne 2) Set 4 G : R{SOURCE_ROW_INDEX} C_impairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 7 : Libero/Rot. L3 (R8 Source, indices impairs -> R6 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 6
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX and len(raw_df_s4_b.columns) > max(SOURCE_COL_INDICES_EVEN_R7_R8):
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_R7_R8].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 7 (Libero/Rot. Ligne 3) Set 4 G : R{SOURCE_ROW_INDEX} C_impairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 8 : Libero/Rot. L4 (R9 Source, indices pairs (commençant à 0) -> R7 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 7
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX and len(raw_df_s4_b.columns) > max(SOURCE_COL_INDICES_ODD_R6_R9):
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_R6_R9].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 8 (Libero/Rot. Ligne 4) Set 4 G : R{SOURCE_ROW_INDEX} C_pairs(0-10) Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 9 : Action L2 (R6 Source, indices pairs -> R8 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 8
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX and len(raw_df_s4_b.columns) > max(SOURCE_COL_INDICES_EVEN_ACTION_R6_R9):
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_ACTION_R6_R9].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 9 (Action Ligne 2) Set 4 G : R{SOURCE_ROW_INDEX} C_pairs(2-12) Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 10 : Action L3 (R7 Source, indices pairs -> R9 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 9
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX and len(raw_df_s4_b.columns) > max(SOURCE_COL_INDICES_ODD_ACTION_R7_R8):
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_ACTION_R7_R8].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 10 (Action Ligne 3) Set 4 G : R{SOURCE_ROW_INDEX} C_pairs(2-12) Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 11 : Action L4 (R8 Source, indices pairs -> R10 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 10
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX and len(raw_df_s4_b.columns) > max(SOURCE_COL_INDICES_ODD_ACTION_R7_R8):
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_ACTION_R7_R8].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 11 (Action Ligne 4) Set 4 G : R{SOURCE_ROW_INDEX} C_pairs(2-12) Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 12 : Action L5 (R9 Source, indices impairs -> R11 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 11
    if len(raw_df_s4_b) > SOURCE_ROW_INDEX and len(raw_df_s4_b.columns) > max(SOURCE_COL_INDICES_EVEN_ACTION_R6_R9):
        data = raw_df_s4_b.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_ACTION_R6_R9].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 12 (Action Ligne 5) Set 4 G : R{SOURCE_ROW_INDEX} C_impairs(1-11) Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # --- FIN DES TRANSFERTS SET 4 ÉQUIPE GAUCHE ---
    #print(f"✅ Transferts COMPLETS pour l'Équipe Gauche (SET 4) terminés.")

    return FINAL_DATAFRAME_SET_4_b

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 4 a
# ======================================================================

def extract_raw_set_4_a(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 4 (Équipe a) aux coordonnées spécifiées."""

    COORDINATES_SET_4_D = [170, 580, 260, 860]
    #print(f"\n--- Début de l'extraction du tableau brut absolu : Set 4 a (Zone {COORDINATES_SET_4_D}) ---")

    tables = []
    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_4_D, lattice=True, multiple_tables=False, pandas_options={'header': None})
        print("✅ Extraction Set 4 a réussie.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction tabula pour Set 4 a. Détails: {e}")
        return None

    if not tables or tables[0].empty:
        print("❌ Échec de la récupération du tableau pour Set 4 a dans la zone spécifiée.")
        return None

    df_source = tables[0].fillna('').astype(str)
    # display_dataframe(df_source, "TABLEAU SOURCE (BRUT) ÉQUIPE a (SET 4)")
    return df_source

# ======================================================================
# FONCTIONS structure - SET 4 a
# ======================================================================

def process_and_structure_set_4_a(raw_df_s4_a: pd.DataFrame) -> pd.DataFrame:
    """Crée le DataFrame Cible et y transfère les données brutes du Set 4 - Équipe a."""

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_4_a = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])
    #print(f"\n✅ Tableau Cible Vierge créé : {TARGET_ROWS} lignes x {TARGET_COLS} colonnes dans `FINAL_DATAFRAME_SET_4_a` (Set 4 Équipe a).")

    # --- DÉBUT DES TRANSFERTS SET 4 ÉQUIPE a ---

    SOURCE_COL_START_C1_C6 = 1
    SOURCE_COL_END_C1_C6 = 7
    TARGET_ROW_START_INDEX = 0

    # Définition des constantes d'indices de colonnes pour la clarté (Logique Set 3 a utilisée)
    SOURCE_COL_INDICES_ODD_C1_C11 = [1, 3, 5, 7, 9, 11] # Utilisés pour Rot. L1, L2, L3, L4 (R6, R7, R8, R9)
    SOURCE_COL_INDICES_EVEN_C2_C12 = [2, 4, 6, 8, 10, 12] # Utilisés pour Action L2, L3, L4, L5 (R6, R7, R8, R9)

    # NOTE: L'indice SOURCE_COL_INDICES_ODD_C3_C13 n'est plus utilisé ici (contrairement à Set 3 D)

    # TRANSFERT 1 : Formation de Départ (R2 Source -> R0 Cible)
    SOURCE_ROW_INDEX = 2
    TARGET_ROW_INDEX = 0
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX:
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_START_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 1 (Formation de Départ) Set 4 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 2 : Remplaçants (R3 Source -> R1 Cible)
    SOURCE_ROW_INDEX = 3
    TARGET_ROW_INDEX = 1
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX:
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_START_INDEX + 1, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 2 (Remplaçants) Set 4 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 3 : Score (R4 Source -> R2 Cible)
    SOURCE_ROW_INDEX = 4
    TARGET_ROW_INDEX = 2
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX:
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_START_INDEX + 2, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 3 (Score) Set 4 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 4 : Première Ligne d'Action (R5 Source -> R3 Cible)
    SOURCE_ROW_INDEX = 5
    TARGET_ROW_INDEX = 3
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX:
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_START_INDEX + 3, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 4 (Première Ligne d'Action) Set 4 D : R{SOURCE_ROW_INDEX} C1-C6 Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 5 : Libero/Rot. L1 (R6 Source, Colonnes Impaires C1-C11 -> R4 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 4
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX and len(raw_df_s4_a.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 5 (Libero/Rot. Ligne 1) Set 4 D : R{SOURCE_ROW_INDEX} C_impairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 6 : Libero/Rot. L2 (R7 Source, Colonnes Impaires C1-C11 -> R5 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 5
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX and len(raw_df_s4_a.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 6 (Libero/Rot. Ligne 2) Set 4 D : R{SOURCE_ROW_INDEX} C_impairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 7 : Libero/Rot. L3 (R8 Source, Colonnes Impaires C1-C11 -> R6 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 6
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX and len(raw_df_s4_a.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 7 (Libero/Rot. Ligne 3) Set 4 D : R{SOURCE_ROW_INDEX} C_impairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 8 : Libero/Rot. L4 (R9 Source, Colonnes Impaires C1-C11 -> R7 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 7
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX and len(raw_df_s4_a.columns) > max(SOURCE_COL_INDICES_ODD_C1_C11):
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 8 (Libero/Rot. Ligne 4) Set 4 D : R{SOURCE_ROW_INDEX} C_impairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 9 : Action L2 (R6 Source, Colonnes Paires C2-C12 -> R8 Cible)
    SOURCE_ROW_INDEX = 6
    TARGET_ROW_INDEX = 8
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX and len(raw_df_s4_a.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 9 (Action Ligne 2) Set 4 D : R{SOURCE_ROW_INDEX} C_pairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 10 : Action L3 (R7 Source, Colonnes Paires C2-C12 -> R9 Cible)
    SOURCE_ROW_INDEX = 7
    TARGET_ROW_INDEX = 9
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX and len(raw_df_s4_a.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 10 (Action Ligne 3) Set 4 D : R{SOURCE_ROW_INDEX} C_pairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 11 : Action L4 (R8 Source, Colonnes Paires C2-C12 -> R10 Cible)
    SOURCE_ROW_INDEX = 8
    TARGET_ROW_INDEX = 10
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX and len(raw_df_s4_a.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 11 (Action Ligne 4) Set 4 D : R{SOURCE_ROW_INDEX} C_pairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # TRANSFERT 12 : Action L5 (R9 Source, Colonnes Paires C2-C12 -> R11 Cible)
    SOURCE_ROW_INDEX = 9
    TARGET_ROW_INDEX = 11
    if len(raw_df_s4_a) > SOURCE_ROW_INDEX and len(raw_df_s4_a.columns) > max(SOURCE_COL_INDICES_EVEN_C2_C12):
        data = raw_df_s4_a.iloc[SOURCE_ROW_INDEX, SOURCE_COL_INDICES_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_4_a.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data
            #print(f"✅ Transfert 12 (Action Ligne 5) Set 4 D : R{SOURCE_ROW_INDEX} C_pairs Source -> R{TARGET_ROW_INDEX} Cible effectué.")

    # --- FIN DES TRANSFERTS SET 4 ÉQUIPE a ---
    #print(f"✅ Transferts COMPLETS pour l'Équipe a (SET 4) terminés.")

    return FINAL_DATAFRAME_SET_4_a

# ======================================================================
# FONCTIONS D'EXTRACTION BRUTE - SET 5 b
# ======================================================================

def extract_raw_set_5_b(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 5 aux coordonnées spécifiées. (Utilisé par l'équipe b)."""

    # Coordonnées spécifiques pour le Set 5 (central)
    COORDINATES_SET_5 = [280, 140, 360, 480]
    #print(f"\n--- Début de l'extraction du tableau brut absolu : Set 5 b (Zone {COORDINATES_SET_5}) ---")

    tables = []
    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_5, lattice=True, multiple_tables=False, pandas_options={'header': None})
        print("✅ Extraction Set 5 b réussie.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction tabula pour Set 5 b. Détails: {e}")
        return None

    if not tables or tables[0].empty:
        print("❌ Échec de la récupération du tableau pour Set 5 b dans la zone spécifiée.")
        return None

    df_source = tables[0].fillna('').astype(str)
    # Note: display_dataframe n'est pas inclus ici car non défini
    # display_dataframe(df_source, "TABLEAU SOURCE (BRUT) (SET 5)")
    return df_source

# ======================================================================
# FONCTIONS structure - SET 5 b
# ======================================================================

def process_and_structure_set_5_b(raw_df_s5_b: pd.DataFrame) -> pd.DataFrame:
    """
    Crée le DataFrame Cible et y transfère les données brutes du Set 5
    en utilisant la logique de l'Équipe b du Set 4 SANS utiliser d'OFFSET.

    NOTE : Cette fonction suppose que les colonnes de l'équipe b (C1-C6, C1-C11)
    commencent directement aux indices 1 ou 2 du tableau brut du Set 5 (raw_df_s5_b).
    """

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    FINAL_DATAFRAME_SET_5_b = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])
    #print(f"\n✅ Tableau Cible Vierge créé : {TARGET_ROWS} lignes x {TARGET_COLS} colonnes dans `FINAL_DATAFRAME_SET_5_b` (Set 5 Équipe b).")

    # --- DÉBUT DES TRANSFERTS SET 5 ÉQUIPE b (Logique copiée de Set 4 b sans OFFSET) ---

    # Indices Source (Basés sur le début du DF brut)
    SOURCE_COL_START_C1_C6 = 1
    SOURCE_COL_END_C1_C6 = 7
    TARGET_ROW_START_INDEX = 0

    # Indices complexes (Libero/Actions)
    S_ODD_C1_C11 = [1, 3, 5, 7, 9, 11] # Rot. L1 (Impairs)
    S_EVEN_C2_C12 = [2, 4, 6, 8, 10, 12] # Rot. L2, L3, L4, Action L2 (Pairs)
    S_EVEN_C3_C13 = [3, 5, 7, 9, 11, 13] # Action L3, L4, L5 (Pairs décalés)

    # Vérification de la taille des colonnes avant les transferts complexes
    max_odd_index = max(S_ODD_C1_C11)
    max_complex_index = max(S_EVEN_C3_C13)

    # TRANSFERTS LIGNES 0 à 3 (Formation, Remplaçants, Score, Action L1)
    for target_row, source_row in enumerate(range(1, 5)):
        if len(raw_df_s5_b) > source_row:
            data = raw_df_s5_b.iloc[source_row, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_SET_5_b.iloc[target_row, 0:TARGET_COLS_COUNT] = data
                # Ajout d'un log pour confirmer le transfert (optionnel)
                # print(f"✅ Transfert L{target_row} (R{source_row} Source) effectué.")


    # TRANSFERT 5 : Libero/Rot. L1 (R5 Source, Colonnes Impaires -> R4 Cible)
    SOURCE_ROW_INDEX = 5
    TARGET_ROW_INDEX = 4
    if len(raw_df_s5_b) > SOURCE_ROW_INDEX and len(raw_df_s5_b.columns) > max_odd_index:
        data = raw_df_s5_b.iloc[SOURCE_ROW_INDEX, S_ODD_C1_C11].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_5_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data

    # TRANSFERTS 6, 7, 8 (Libero/Rot. L2, L3, L4)
    # Logique : R6, R7, R8 Source utilisent les indices pairs C2-C12 -> R5, R6, R7 Cible
    for target_row, source_row in enumerate(range(6, 9), start=5):
        if len(raw_df_s5_b) > source_row and len(raw_df_s5_b.columns) > max(S_EVEN_C2_C12):
            data = raw_df_s5_b.iloc[source_row, S_EVEN_C2_C12].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_SET_5_b.iloc[target_row, 0:TARGET_COLS_COUNT] = data

    # TRANSFERT 9 : Action L2 (R5 Source, Colonnes Paires -> R8 Cible)
    SOURCE_ROW_INDEX = 5
    TARGET_ROW_INDEX = 8
    if len(raw_df_s5_b) > SOURCE_ROW_INDEX and len(raw_df_s5_b.columns) > max(S_EVEN_C2_C12):
        data = raw_df_s5_b.iloc[SOURCE_ROW_INDEX, S_EVEN_C2_C12].values
        if len(data) == TARGET_COLS_COUNT:
            FINAL_DATAFRAME_SET_5_b.iloc[TARGET_ROW_INDEX, 0:TARGET_COLS_COUNT] = data

    # TRANSFERTS 10, 11, 12 (Action L3, L4, L5)
    # Logique : R6, R7, R8 Source utilisent les indices pairs décalés C3-C13 -> R9, R10, R11 Cible
    for target_row, source_row in enumerate(range(6, 9), start=9):
        if len(raw_df_s5_b) > source_row and len(raw_df_s5_b.columns) > max_complex_index:
            data = raw_df_s5_b.iloc[source_row, S_EVEN_C3_C13].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_SET_5_b.iloc[target_row, 0:TARGET_COLS_COUNT] = data

    # --- FIN DES TRANSFERTS SET 5 ÉQUIPE DROITE ---
    #print(f"✅ Transferts COMPLETS pour l'Équipe Droite (SET 5) terminés. (Sans OFFSET).")

    return FINAL_DATAFRAME_SET_5_b

# ======================================================================
# FONCTIONS D'EXTRACTION - SET 5 a
# ======================================================================

def extract_raw_set_5_a(pdf_file_path: str) -> pd.DataFrame or None:
    """Extrait le tableau brut pour le SET 5 aux coordonnées spécifiées. (Utilisé par l'équipe a)."""

    # Coordonnées spécifiques pour le Set 5 (zone a)
    COORDINATES_SET_5 = [280, 0, 360, 200]
    #print(f"\n--- Début de l'extraction du tableau brut absolu : Set 5 a (Zone {COORDINATES_SET_5}) ---")

    tables = []
    try:
        tables = tabula.read_pdf(pdf_file_path, pages=1, area=COORDINATES_SET_5, lattice=True, multiple_tables=False, pandas_options={'header': None})
        #print("✅ Extraction Set 5 a réussie.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction tabula pour Set 5 a. Détails: {e}")
        return None

    if not tables or tables[0].empty:
        print("❌ Échec de la récupération du tableau pour Set 5 a dans la zone spécifiée.")
        return None

    df_source = tables[0].fillna('').astype(str)
    # Si 'display_dataframe' est défini dans le contexte global, vous pouvez décommenter :
    # display_dataframe(df_source, "TABLEAU SOURCE (BRUT) (SET 5)")
    return df_source

# ======================================================================
# FONCTIONS structure - SET 5 a
# ======================================================================

def process_and_structure_set_5_a(raw_df_s5_a: pd.DataFrame) -> pd.DataFrame:
    """
    Crée le DataFrame Cible et y transfère les données brutes de l'Équipe a du Set 5
    en utilisant la logique de l'Équipe a du Set 4 SANS utiliser d'OFFSET.
    """

    new_data = np.full((TARGET_ROWS, TARGET_COLS), '', dtype=object)
    # Le nom de la variable cible est correctement ajusté en _G
    FINAL_DATAFRAME_SET_5_a = pd.DataFrame(new_data, columns=[f'C{i}' for i in range(TARGET_COLS)])
    #print(f"\n✅ Tableau Cible Vierge créé : {TARGET_ROWS} lignes x {TARGET_COLS} colonnes dans `FINAL_DATAFRAME_SET_5_a` (Set 5 Équipe a).")

    # --- DÉBUT DES TRANSFERTS SET 5 ÉQUIPE a (Logique copiée de Set 4 a sans OFFSET) ---

    # Indices Source (standard pour l'Équipe a)
    SOURCE_COL_START_C1_C6 = 0 # Colonne 0 à 5 pour la Formation/Remplaçants/Score/Action 1
    SOURCE_COL_END_C1_C6 = 6
    TARGET_ROW_START_INDEX = 0

    # Indices complexes (Libero/Actions pour l'Équipe a)
    S_EVEN_C0_C10 = [0, 2, 4, 6, 8, 10] # Colonnes Paires (pour Rotations Libero L1 à L4)
    S_ODD_C1_C11 = [1, 3, 5, 7, 9, 11]  # Colonnes Impaires (pour Actions L2 à L5)

    # Vérification de la taille des colonnes (index max est 11)
    max_index_complex = max(S_ODD_C1_C11)

    # TRANSFERTS LIGNES 0 à 3 (Formation, Remplaçants, Score, Action L1)
    for target_row, source_row in enumerate(range(1, 5)):
        if len(raw_df_s5_a) > source_row:
            data = raw_df_s5_a.iloc[source_row, SOURCE_COL_START_C1_C6:SOURCE_COL_END_C1_C6].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_SET_5_a.iloc[target_row, 0:TARGET_COLS_COUNT] = data

    # TRANSFERTS 5, 6, 7, 8 (Libero/Rot. L1, L2, L3, L4)
    # Logique : R5, R6, R7, R8 Source utilisent les indices PAIRS C0-C10 -> R4, R5, R6, R7 Cible
    for target_row, source_row in enumerate(range(5, 9), start=4):
        if len(raw_df_s5_a) > source_row and len(raw_df_s5_a.columns) > max(S_EVEN_C0_C10):
            # Utilisation des indices PAIRS/Libero (S_EVEN_C0_C10)
            data = raw_df_s5_a.iloc[source_row, S_EVEN_C0_C10].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_SET_5_a.iloc[target_row, 0:TARGET_COLS_COUNT] = data

    # TRANSFERTS 9, 10, 11, 12 (Action L2, L3, L4, L5)
    # Logique : R5, R6, R7, R8 Source utilisent les indices IMPAIRS C1-C11 -> R8, R9, R10, R11 Cible
    for target_row, source_row in enumerate(range(5, 9), start=8):
        if len(raw_df_s5_a) > source_row and len(raw_df_s5_a.columns) > max_index_complex:
            # Utilisation des indices IMPAIRS/Action (S_ODD_C1_C11)
            data = raw_df_s5_a.iloc[source_row, S_ODD_C1_C11].values
            if len(data) == TARGET_COLS_COUNT:
                FINAL_DATAFRAME_SET_5_a.iloc[target_row, 0:TARGET_COLS_COUNT] = data

    # --- FIN DES TRANSFERTS SET 5 ÉQUIPE a ---
    #print(f"✅ Transferts COMPLETS pour l'Équipe a (SET 5) terminés.")

    return FINAL_DATAFRAME_SET_5_a


# ======================================================================
# FONCTIONS temps mort - SET 1
# ======================================================================

# NOTE: Ces fonctions appellent extract_raw_set_X_droite, qui doit être définie.

def extract_temps_mort_set_1(pdf_file_path: str) -> tuple:
    """Extrait les quatre temps morts (G1, G2, D1, D2) du SET 1."""

    # Assurez-vous que la fonction extract_raw_set_1_b est définie et importée
    RAW_DATAFRAME_SET_1_D = extract_raw_set_1_b(pdf_file_path)

    T_set_a1, T_set_a2, T_set_b1, T_set_b2 = None, None, None, None

    if RAW_DATAFRAME_SET_1_D is not None and not RAW_DATAFRAME_SET_1_D.empty:
        max_rows = len(RAW_DATAFRAME_SET_1_D)
        max_cols = len(RAW_DATAFRAME_SET_1_D.columns)

        # Indices de Ligne et Colonne (Base 0)
        ROW_INDEX_T1 = 8
        ROW_INDEX_T2 = 9
        COL_INDEX_GAUCHE = 1
        COL_INDEX_DROITE = 14

        if ROW_INDEX_T1 < max_rows and COL_INDEX_GAUCHE < max_cols:
            T_set_a1 = str(RAW_DATAFRAME_SET_1_D.iloc[ROW_INDEX_T1, COL_INDEX_GAUCHE]).strip()
        if ROW_INDEX_T2 < max_rows and COL_INDEX_GAUCHE < max_cols:
            T_set_a2 = str(RAW_DATAFRAME_SET_1_D.iloc[ROW_INDEX_T2, COL_INDEX_GAUCHE]).strip()
        if ROW_INDEX_T1 < max_rows and COL_INDEX_DROITE < max_cols:
            T_set_b1 = str(RAW_DATAFRAME_SET_1_D.iloc[ROW_INDEX_T1, COL_INDEX_DROITE]).strip()
        if ROW_INDEX_T2 < max_rows and COL_INDEX_DROITE < max_cols:
            T_set_b2 = str(RAW_DATAFRAME_SET_1_D.iloc[ROW_INDEX_T2, COL_INDEX_DROITE]).strip()

    return T_set_a1, T_set_a2, T_set_b1, T_set_b2


# ======================================================================
# FONCTIONS temps mort - SET 2
# ======================================================================

def extract_temps_mort_set_2(pdf_file_path: str) -> tuple:
    """Extrait les quatre temps morts (G1, G2, D1, D2) du SET 2."""

    RAW_DATAFRAME_SET_2_D = extract_raw_set_2_a(pdf_file_path)

    T_set_b1, T_set_b2, T_set_a1, T_set_a2 = None, None, None, None

    if RAW_DATAFRAME_SET_2_D is not None and not RAW_DATAFRAME_SET_2_D.empty:
        max_rows = len(RAW_DATAFRAME_SET_2_D)
        max_cols = len(RAW_DATAFRAME_SET_2_D.columns)

        ROW_INDEX_T1 = 8
        ROW_INDEX_T2 = 9
        COL_INDEX_GAUCHE = 0
        COL_INDEX_DROITE = 13

        if ROW_INDEX_T1 < max_rows and COL_INDEX_GAUCHE < max_cols:
            T_set_b1 = str(RAW_DATAFRAME_SET_2_D.iloc[ROW_INDEX_T1, COL_INDEX_GAUCHE]).strip()
        if ROW_INDEX_T2 < max_rows and COL_INDEX_GAUCHE < max_cols:
            T_set_b2 = str(RAW_DATAFRAME_SET_2_D.iloc[ROW_INDEX_T2, COL_INDEX_GAUCHE]).strip()
        if ROW_INDEX_T1 < max_rows and COL_INDEX_DROITE < max_cols:
            T_set_a1 = str(RAW_DATAFRAME_SET_2_D.iloc[ROW_INDEX_T1, COL_INDEX_DROITE]).strip()
        if ROW_INDEX_T2 < max_rows and COL_INDEX_DROITE < max_cols:
            T_set_a2 = str(RAW_DATAFRAME_SET_2_D.iloc[ROW_INDEX_T2, COL_INDEX_DROITE]).strip()

    return T_set_b1, T_set_b2, T_set_a1, T_set_a2

# ======================================================================
# FONCTIONS temps mort - SET 3
# ======================================================================

def extract_temps_mort_set_3(pdf_file_path: str) -> tuple:
    """Extrait les quatre temps morts (G1, G2, D1, D2) du SET 3."""

    RAW_DATAFRAME_SET_3_D = extract_raw_set_3_b(pdf_file_path)

    T_set_a1, T_set_a2, T_set_b1, T_set_b2 = None, None, None, None

    if RAW_DATAFRAME_SET_3_D is not None and not RAW_DATAFRAME_SET_3_D.empty:
        max_rows = len(RAW_DATAFRAME_SET_3_D)
        max_cols = len(RAW_DATAFRAME_SET_3_D.columns)

        ROW_INDEX_T1 = 8
        ROW_INDEX_T2 = 9
        COL_INDEX_GAUCHE_1 = 1
        COL_INDEX_GAUCHE_2 = 0
        COL_INDEX_DROITE_1 = 14
        COL_INDEX_DROITE_2 = 13

        if ROW_INDEX_T1 < max_rows and COL_INDEX_GAUCHE_1 < max_cols:
            T_set_a1 = str(RAW_DATAFRAME_SET_3_D.iloc[ROW_INDEX_T1, COL_INDEX_GAUCHE_1]).strip()
        if ROW_INDEX_T2 < max_rows and COL_INDEX_GAUCHE_2 < max_cols:
            T_set_a2 = str(RAW_DATAFRAME_SET_3_D.iloc[ROW_INDEX_T2, COL_INDEX_GAUCHE_2]).strip()
        if ROW_INDEX_T1 < max_rows and COL_INDEX_DROITE_1 < max_cols:
            T_set_b1 = str(RAW_DATAFRAME_SET_3_D.iloc[ROW_INDEX_T1, COL_INDEX_DROITE_1]).strip()
        if ROW_INDEX_T2 < max_rows and COL_INDEX_DROITE_2 < max_cols:
            T_set_b2 = str(RAW_DATAFRAME_SET_3_D.iloc[ROW_INDEX_T2, COL_INDEX_DROITE_2]).strip()

    return T_set_a1, T_set_a2, T_set_b1, T_set_b2

# ======================================================================
# FONCTIONS temps mort - SET 4
# ======================================================================

def extract_temps_mort_set_4(pdf_file_path: str) -> tuple:
    """Extrait les quatre temps morts (G1, G2, D1, D2) du SET 4."""

    RAW_DATAFRAME_SET_4_D = extract_raw_set_4_a(pdf_file_path)

    T_set_b1, T_set_b2, T_set_a1, T_set_a2 = None, None, None, None

    if RAW_DATAFRAME_SET_4_D is not None and not RAW_DATAFRAME_SET_4_D.empty:
        max_rows = len(RAW_DATAFRAME_SET_4_D)
        max_cols = len(RAW_DATAFRAME_SET_4_D.columns)

        ROW_INDEX_T1 = 8
        ROW_INDEX_T2 = 9
        COL_INDEX_GAUCHE = 0
        COL_INDEX_DROITE = 13

        if ROW_INDEX_T1 < max_rows and COL_INDEX_GAUCHE < max_cols:
            T_set_b1 = str(RAW_DATAFRAME_SET_4_D.iloc[ROW_INDEX_T1, COL_INDEX_GAUCHE]).strip()
        if ROW_INDEX_T2 < max_rows and COL_INDEX_GAUCHE < max_cols:
            T_set_b2 = str(RAW_DATAFRAME_SET_4_D.iloc[ROW_INDEX_T2, COL_INDEX_GAUCHE]).strip()
        if ROW_INDEX_T1 < max_rows and COL_INDEX_DROITE < max_cols:
            T_set_a1 = str(RAW_DATAFRAME_SET_4_D.iloc[ROW_INDEX_T1, COL_INDEX_DROITE]).strip()
        if ROW_INDEX_T2 < max_rows and COL_INDEX_DROITE < max_cols:
            T_set_a2 = str(RAW_DATAFRAME_SET_4_D.iloc[ROW_INDEX_T2, COL_INDEX_DROITE]).strip()

    return T_set_b1, T_set_b2, T_set_a1, T_set_a2


# ======================================================================
# FONCTIONS temps mort - SET 5
# ======================================================================

def extract_temps_mort_set_5(pdf_file_path: str) -> tuple:
    """Extrait les quatre temps morts (G1, G2, D1, D2) du SET 5, avec logique de secours pour l'équipe a."""

    RAW_DATAFRAME_SET_5_D = extract_raw_set_5_b(pdf_file_path)

    # Initialisation des variables de temps mort (résultat)
    T_set_a1, T_set_a2, T_set_b1, T_set_b2 = None, None, None, None

    # Variables de secours (bis) pour l'équipe a
    T_set_a1_bis, T_set_a2_bis = None, None

    if RAW_DATAFRAME_SET_5_D is not None and not RAW_DATAFRAME_SET_5_D.empty:
        max_rows = len(RAW_DATAFRAME_SET_5_D)
        max_cols = len(RAW_DATAFRAME_SET_5_D.columns)

        # --- Définition des Indices ---
        ROW_INDEX_T1 = 7
        ROW_INDEX_T2 = 8
        COL_INDEX_GAUCHE = 1
        COL_INDEX_DROITE = 14

        # Positions de secours
        ROW_INDEX_T1_bis = 16
        ROW_INDEX_T2_bis = 17
        COL_INDEX_GAUCHE_bis = 12

        # --- Extraction Primaire a (T_set_a1, T_set_a2) ---
        if ROW_INDEX_T1 < max_rows and COL_INDEX_GAUCHE < max_cols:
            T_set_a1 = str(RAW_DATAFRAME_SET_5_D.iloc[ROW_INDEX_T1, COL_INDEX_GAUCHE]).strip()
        if ROW_INDEX_T2 < max_rows and COL_INDEX_GAUCHE < max_cols:
            T_set_a2 = str(RAW_DATAFRAME_SET_5_D.iloc[ROW_INDEX_T2, COL_INDEX_GAUCHE]).strip()

        # --- Extraction de Secours a (T_set_a1_bis, T_set_a2_bis) ---
        if ROW_INDEX_T1_bis < max_rows and COL_INDEX_GAUCHE_bis < max_cols:
            T_set_a1_bis = str(RAW_DATAFRAME_SET_5_D.iloc[ROW_INDEX_T1_bis, COL_INDEX_GAUCHE_bis]).strip()
        if ROW_INDEX_T2_bis < max_rows and COL_INDEX_GAUCHE_bis < max_cols:
            T_set_a2_bis = str(RAW_DATAFRAME_SET_5_D.iloc[ROW_INDEX_T2_bis, COL_INDEX_GAUCHE_bis]).strip()

        # --- Extraction b (T_set_b1, T_set_b2) ---
        if ROW_INDEX_T1 < max_rows and COL_INDEX_DROITE < max_cols:
            T_set_b1 = str(RAW_DATAFRAME_SET_5_D.iloc[ROW_INDEX_T1, COL_INDEX_DROITE]).strip()
        if ROW_INDEX_T2 < max_rows and COL_INDEX_DROITE < max_cols:
            T_set_b2 = str(RAW_DATAFRAME_SET_5_D.iloc[ROW_INDEX_T2, COL_INDEX_DROITE]).strip()

        # ------------------------------------------------------------------
        ## 🧠 Logique de Substitution pour l'Équipe a
        # ------------------------------------------------------------------

        # Condition pour T1 a: Si T_set_a1 est vide ou None, utiliser T_set_a1_bis
        if not T_set_a1 or T_set_a1 == 'None':
            T_set_a1 = T_set_a1_bis

        # Condition pour T2 a: Si T_set_a2 est vide ou None, utiliser T_set_a2_bis
        if not T_set_a2 or T_set_a2 == 'None':
            T_set_a2 = T_set_a2_bis

    return T_set_a1, T_set_a2, T_set_b1, T_set_b2

# ======================================================================
# FONCTION Score
# ======================================================================

def analyze_data(pdf_file_path: str) -> pd.DataFrame or None:
    """
    Extrait le tableau brut pour les DONNÉES DE SCORE aux coordonnées spécifiées
    et retourne le DataFrame brut.
    """

    # Coordonnées de la zone des scores : [Haut, Gauche, Bas, Droite]
    COORD_SCORES = [300, 140, 842, 595]
    print(f"\n--- Début de l'extraction du tableau brut : DONNÉES (Zone {COORD_SCORES}) ---")

    tables = []
    try:
        tables = tabula.read_pdf(
            pdf_file_path,
            pages=1,
            area=COORD_SCORES,
            lattice=True,
            multiple_tables=False,
            pandas_options={'header': None}
        )
        print("✅ Extraction DONNÉES réussie.")
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction tabula pour DONNÉES. Détails: {e}")
        return None

    if not tables or tables[0].empty:
        print("❌ Échec de la récupération du tableau pour DONNÉES dans la zone spécifiée.")
        return None

    # Nettoyage : Remplir les NaN par des chaînes vides et s'assurer que tout est en string
    df_source = tables[0].fillna('').astype(str)
    return df_source

# ======================================================================
# FONCTION Structure
# ======================================================================

def process_and_structure_scores(raw_df_data: pd.DataFrame) -> pd.DataFrame:
    """
    Crée un DataFrame cible de 5 lignes et 2 colonnes (R5 x C2) pour les scores.
    Extrait les 10 résultats de sets en appliquant des conditions de vérification
    sur C2 pour les sets Gauche (1 à 5), sur C6 pour le Set 1 Droite, et sur C5
    pour les Sets 2, 3, 4 et 5 Droite.
    """

    # --- 1. INTRODUCTION ET INITIALISATION DES 10 VARIABLES DE RÉSULTATS (Locales) ---

    # Initialisation
    resultat_a_set_1 = None
    resultat_b_set_2 = None
    resultat_a_set_3 = None
    resultat_b_set_4 = None
    resultat_a_set_5 = None
    resultat_b_set_1 = None
    resultat_a_set_2 = None
    resultat_b_set_3 = None
    resultat_a_set_4 = None
    resultat_b_set_5 = None

    # ----------------------------------------------------------------------
    # 🛑 LOGIQUE : Affectation des résultats de Sets
    # ----------------------------------------------------------------------

    # Définition des lignes cibles (Index 0-basé)
    ROWS = {1: 28, 2: 29, 3: 30, 4: 31, 5: 32}

    # Colonnes cibles (Index 0-basé)
    COL_SCORE_GAUCHE = 3          # C3 pour le score Gauche
    COL_SCORE_DROITE_SET_1 = 5    # C5 pour Score Set 1 Droite
    COL_SCORE_DROITE_SET_2_5 = 4  # C4 pour Score Set 2, 3, 4 et 5 Droite
    COL_VERIF_GAUCHE = 2          # C2 pour la vérification Gauche (Sets 1-5)
    COL_VERIF_DROITE_SET_1 = 6    # C6 pour la vérification Set 1 Droite
    COL_VERIF_DROITE_SET_2_5 = 5  # C5 pour la vérification Set 2, 3, 4 et 5 Droite

    # --- A. AFFECTATION ÉQUIPE GAUCHE (COLONNE C3) ---
    for set_num, target_row in ROWS.items():

        # 1. Vérification de la taille minimale du DF
        if raw_df_data is None or len(raw_df_data) <= target_row or len(raw_df_data.columns) <= COL_SCORE_GAUCHE:
            if set_num == 1:
                 print(f"❌ Échec Gauche : DF brut trop petit pour R{target_row}.")
            continue

        # 2. Extraction du score
        result = None
        score_value = str(raw_df_data.iloc[target_row, COL_SCORE_GAUCHE]).strip()

        # 3. Application de la condition C2 pour tous les Sets Gauche
        if len(raw_df_data.columns) > COL_VERIF_GAUCHE:
            verif_value = str(raw_df_data.iloc[target_row, COL_VERIF_GAUCHE]).strip()

            if verif_value in ['0', '1']:
                result = score_value
            # Logique de debug commentée :
            # else:
            #     print(f"⚠️ resultat_gauche_set_{set_num} NON affecté. Condition C2='{verif_value}' non remplie (R{target_row}).")

        # 4. Affectation des variables locales
        if set_num == 1: resultat_a_set_1 = result
        elif set_num == 2: resultat_b_set_2 = result
        elif set_num == 3: resultat_a_set_3 = result
        elif set_num == 4: resultat_b_set_4 = result
        elif set_num == 5: resultat_a_set_5 = result

    # --- B. AFFECTATION ÉQUIPE DROITE ---

    # RÉSULTAT SET 1 DROITE (C5 R28 Score) - Conditionnel à C6 R28
    set_num = 1
    target_row = ROWS[set_num]
    score_col = COL_SCORE_DROITE_SET_1
    result = None

    if raw_df_data is not None and len(raw_df_data) > target_row and len(raw_df_data.columns) > max(score_col, COL_VERIF_DROITE_SET_1):
        score_value = str(raw_df_data.iloc[target_row, score_col]).strip()
        verif_value = str(raw_df_data.iloc[target_row, COL_VERIF_DROITE_SET_1]).strip()

        if verif_value in ['0', '1']:
            result = score_value
            # print(f"✅ resultat_b_set_1 affecté à : '{result}' (C{score_col} R{target_row}). Condition C6='{verif_value}' remplie.")
        # else:
            # print(f"⚠️ resultat_b_set_1 NON affecté. Condition C6='{verif_value}' non remplie (R{target_row}).")

        resultat_b_set_1 = result
    # else:
        # print(f"❌ Échec Droite Set 1 : DF brut trop petit pour R{target_row}.")

    # RÉSULTATS SETS 2, 3, 4 et 5 DROITE (C4 R29 à R32 Score) - Conditionnels à C5
    for set_num in [2, 3, 4, 5]:
        target_row = ROWS[set_num]
        score_col = COL_SCORE_DROITE_SET_2_5
        result = None

        # 1. Vérification de la taille du DF pour score (C4) et vérification (C5)
        if raw_df_data is not None and len(raw_df_data) > target_row and len(raw_df_data.columns) > COL_VERIF_DROITE_SET_2_5:
            score_value = str(raw_df_data.iloc[target_row, score_col]).strip()

            # 2. Application de la condition C5 (pour Sets 2, 3, 4 et 5)
            verif_value = str(raw_df_data.iloc[target_row, COL_VERIF_DROITE_SET_2_5]).strip()

            if verif_value in ['0', '1']:
                result = score_value
                # print(f"✅ resultat_droite_set_{set_num} affecté à : '{result}' (C{score_col} R{target_row}). Condition C5='{verif_value}' remplie.")
            # else:
                # print(f"⚠️ resultat_droite_set_{set_num} NON affecté. Condition C5='{verif_value}' non remplie (R{target_row}).")

            if set_num == 2: resultat_a_set_2 = result
            elif set_num == 3: resultat_b_set_3 = result
            elif set_num == 4: resultat_a_set_4 = result
            elif set_num == 5: resultat_b_set_5 = result
        # else:
            # print(f"❌ Échec Droite Set {set_num} : DF brut trop petit pour R{target_row}.")


    # ----------------------------------------------------------------------
    # 2. CRÉATION ET REMPLISSAGE DU DATAFRAME CIBLE 5x2
    # ----------------------------------------------------------------------

    # 2.1. Création des listes de scores à insérer
    scores_gauche = [
        resultat_a_set_1,
        resultat_b_set_2,
        resultat_a_set_3,
        resultat_b_set_4,
        resultat_a_set_5
    ]

    scores_droite = [
        resultat_b_set_1,
        resultat_a_set_2,
        resultat_b_set_3,
        resultat_a_set_4,
        resultat_b_set_5
    ]

    # 2.2. Création du DataFrame (5 lignes x 2 colonnes)
    data = {
        'Scores Gauche (C0)': scores_gauche,
        'Scores Droite (C1)': scores_droite
    }

    df_structured = pd.DataFrame(data, index=[f'Set {i}' for i in range(1, 6)])

    print(f"\n✅ Tableau Cible de 5x2 créé et rempli avec les scores.")

    return df_structured


# ======================================================================
# FONCTION Graph Set
# ======================================================================

def tracer_duel_equipes(df_g, df_d, titre="Duel", nom_g="Équipe A", nom_d="Équipe B"):
    if df_g is None or df_d is None:
        return

    fig, ax = plt.subplots(figsize=(22, 10))
    current_score_g, current_score_d = 0, 0
    x_labels, x_colors = [], []
    pos_x = 0

    color_g = '#3498db' # Bleu pour le DataFrame de gauche
    color_d = '#e67e22' # Orange pour le DataFrame de droite

    # Détection du premier serveur via le 'X'
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

    # Configuration finale
    ax.set_ylim(0, 35)
    ax.set_yticks(range(0, 36))
    ax.set_xticks(range(len(x_labels)))
    xtick_labels = ax.set_xticklabels(x_labels, fontsize=10, fontweight='bold')
    for i, text_label in enumerate(xtick_labels):
        text_label.set_color(x_colors[i])

    # Légende dynamique avec les vrais noms
    custom_lines = [plt.Line2D([0], [0], color=color_g, lw=4), plt.Line2D([0], [0], color=color_d, lw=4)]
    ax.legend(custom_lines, [nom_g, nom_d], loc='upper left', fontsize=12)
    ax.set_title(titre, fontsize=16, fontweight='bold', pad=25)
    plt.subplots_adjust(bottom=0.2)
    plt.show()

# ======================================================================
# FONCTION Check set
# ======================================================================

def check_set_exists(df_scores, row_idx):
    """Vérifie si un set a été joué via le tableau récapitulatif des scores."""
    try:
        if df_scores is None or row_idx >= len(df_scores):
            return False
        # On regarde la première colonne de la ligne concernée
        val = str(df_scores.iloc[row_idx, 0]).upper().strip()
        return val != 'NAN' and val != '' and val != 'NONE'
    except:
        return False

# ======================================================================
# FONCTION Extraction brute Nom équipe
# ======================================================================

def extract_raw_nom_equipe(pdf_path):
    """
    Extrait uniquement les tableaux situés dans le premier quart supérieur
    de toutes les pages du PDF.
    Format Area : [top, left, bottom, right]
    """
    # Zone : du haut (0) jusqu'à 25% de la page (210) sur toute la largeur (500+)
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
        print(f"❌ Erreur lors de l'extraction du quart supérieur : {e}")
        return None

# ======================================================================
# FONCTION Structure Nom équipe
# ======================================================================

def process_and_structure_noms_equipes(pdf_path):
    """
    Récupère et nettoie les noms des équipes A et B.
    Logique pour Équipe A : supprime les 2 premiers caractères
    et tout ce qui suit le mot 'Début'.
    """
    tables = extract_raw_nom_equipe(pdf_path)

    equipe_a = "Équipe A"
    equipe_b = "Équipe B"

    if tables:
        df = tables[0]
        try:
            # Récupération brute des cases R4 C1 et R4 C2
            raw_a = str(df.iloc[4, 1]).replace('\r', ' ').strip()
            raw_b = str(df.iloc[4, 2]).replace('\r', ' ').strip()

            # --- NETTOYAGE ÉQUIPE A ---
            # 1. Supprimer les 2 premiers caractères
            clean_a = raw_a[2:]
            clean_b = raw_b[2:]

            # 2. Supprimer à partir du mot "Début"
            if "Début" in clean_a:
                clean_a = clean_a.split("Début")[0]

            if "Début" in clean_b:
                clean_b = clean_b.split("Début")[0]

            equipe_a = clean_a.strip()
            equipe_b = clean_b.strip()

            # Sécurités si vide
            if not equipe_a or equipe_a.lower() == "nan": equipe_a = "Équipe A"
            if not equipe_b or equipe_b.lower() == "nan": equipe_b = "Équipe B"

        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage des noms : {e}")

    return equipe_a, equipe_b

def extraire_joueurs_df(pdf_path):
    motif = re.compile(r'(\d{2})\s+([A-ZÀ-ÿ\s\-]+?)\s+(\d{5,7})')
    joueurs_data = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texte = page.extract_text()
                if texte:
                    # On coupe avant LIBEROS
                    zone = texte.split("LIBEROS")[0] if "LIBEROS" in texte else texte
                    matches = motif.findall(zone)
                    for num, identite, licence in matches:
                        joueurs_data.append({"Numero": num, "Identite": identite.strip(), "Licence": licence})

        # Retourne un DataFrame directement
        return pd.DataFrame(joueurs_data).drop_duplicates(subset=['Licence'])
    except:
        return pd.DataFrame(columns=["Numero", "Identite", "Licence"])

def extraire_liberos_df(pdf_path):
    motif = re.compile(r'(\d{2})\s+([A-ZÀ-ÿ\s\-]+?)\s+(\d{5,7})')
    liberos_data = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texte = page.extract_text()
                if texte and "LIBEROS" in texte:
                    # On coupe entre LIBEROS et APPROBATION RESULTATS
                    apres = texte.split("LIBEROS")[1]
                    zone = apres.split("APPROBATION RESULTATS")[0] if "APPROBATION RESULTATS" in apres else apres

                    matches = motif.findall(zone)
                    for num, identite, licence in matches:
                        liberos_data.append({"Numero": num, "Identite": identite.strip(), "Licence": licence})

        return pd.DataFrame(liberos_data).drop_duplicates(subset=['Licence'])
    except:
        return pd.DataFrame(columns=["Numero", "Identite", "Licence"])

def extraire_staff_df(pdf_path):
    # Motif spécifique EA, EB, EC
    motif_staff = re.compile(r'(E[ABC])\s+([A-ZÀ-ÿ\s\-]+?)\s+(\d{5,7})')
    staff_data = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texte = page.extract_text()
                if texte and "APPROBATION RESULTATS" in texte:
                    # On coupe après APPROBATION RESULTATS
                    zone = texte.split("APPROBATION RESULTATS")[1]
                    matches = motif_staff.findall(zone)
                    for code, identite, licence in matches:
                        staff_data.append({"Code": code, "Identite": identite.strip(), "Licence": licence})

        return pd.DataFrame(staff_data).drop_duplicates(subset=['Licence'])
    except:
        return pd.DataFrame(columns=["Code", "Identite", "Licence"])

def diagnostic_extraction_brute(pdf_path):
    """
    Extrait et affiche le texte brut de chaque page pour comprendre
    comment les données sont structurées.
    """
    print(f"--- 🔍 DIAGNOSTIC TEXTE BRUT : {pdf_path} ---\n")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                texte_page = page.extract_text()
                print(f"--- PAGE {i+1} ---")
                if texte_page:
                    print(texte_page)
                else:
                    print("[Vide ou texte non détectable sur cette page]")
                print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"❌ Erreur lors de l'ouverture du PDF : {e}")

def preparer_positions(df):
    """Extrait les 6 positions depuis la première ligne du DataFrame"""
    if df is not None and not df.empty:
        ligne = df.iloc[0].values
        # Ordre standard des colonnes : I, II, III, IV, V, VI
        return {'I': ligne[0], 'II': ligne[1], 'III': ligne[2],
                'IV': ligne[3], 'V': ligne[4], 'VI': ligne[5]}
    return {}

def dessiner_terrain_phase(ax, nom_a, pos_a_brutes, nom_b, pos_b_brutes, serveur='B'):
    """Trace le terrain sur un axe spécifique (ax)"""
    # Dessin du terrain
    ax.add_patch(patches.Rectangle((0, 0), 18, 9, linewidth=2, edgecolor='black', facecolor='#fafafa'))
    ax.plot([9, 9], [0, 9], color='black', linewidth=3) # Filet
    ax.plot([6, 6], [0, 9], color='gray', linestyle='--', alpha=0.3) # 3m B
    ax.plot([12, 12], [0, 9], color='gray', linestyle='--', alpha=0.3) # 3m A

    # Coordonnées standard sur le terrain
    coords_b = {'IV': (7.5, 7.5), 'III': (7.5, 4.5), 'II': (7.5, 1.5),
                'V':  (3.0, 7.5), 'VI':  (3.0, 4.5), 'I':  (3.0, 1.5)}
    coords_a = {'II': (10.5, 7.5), 'III': (10.5, 4.5), 'IV': (10.5, 1.5),
                'I':  (15.0, 7.5), 'VI':  (15.0, 4.5), 'V':  (15.0, 1.5)}

    if serveur == 'B':
        # B sert : tout le monde sur le terrain. A reçoit : le I de A sort en BAS à droite.
        pos_b = pos_b_brutes
        pos_a = {k: v for k, v in pos_a_brutes.items() if k != 'I'}
        # Correction Y = 1.5 pour l'équipe A en bas
        ax.text(19.5, 1.5, str(pos_a_brutes['I']), fontsize=20, weight='bold', color='salmon', ha='center')
        ax.set_title(f"SERVICE : {nom_b} / RÉCEPTION : {nom_a}", fontsize=12, pad=10)
    else:
        # A sert : tout le monde sur le terrain. B reçoit : le I de B sort en HAUT à gauche.
        pos_a = pos_a_brutes
        pos_b = {k: v for k, v in pos_b_brutes.items() if k != 'I'}
        # On garde Y = 7.5 pour l'équipe B en haut
        ax.text(-1.5, 7.5, str(pos_b_brutes['I']), fontsize=20, weight='bold', color='royalblue', ha='center')
        ax.set_title(f"SERVICE : {nom_a} / RÉCEPTION : {nom_b}", fontsize=12, pad=10)

    # Affichage des joueurs sur le terrain
    for p, n in pos_b.items():
        ax.text(coords_b[p][0], coords_b[p][1], str(n), fontsize=20, weight='bold', color='royalblue', ha='center', va='center')
    for p, n in pos_a.items():
        ax.text(coords_a[p][0], coords_a[p][1], str(n), fontsize=20, weight='bold', color='salmon', ha='center', va='center')

    ax.set_xlim(-3, 21); ax.set_ylim(-1, 10); ax.set_aspect('equal'); ax.axis('off')

def afficher_les_deux_rotations(nom_a, df_a, nom_b, df_b):
    pos_a = preparer_positions(df_a)
    pos_b = preparer_positions(df_b)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))
    dessiner_terrain_phase(ax1, nom_a, pos_a, nom_b, pos_b, serveur='B')
    dessiner_terrain_phase(ax2, nom_a, pos_a, nom_b, pos_b, serveur='A')

    plt.tight_layout()
    plt.show()

# ======================================================================
# ÉTAPE 3 : Upload, Exécution et Définition des Variables Globales
# ======================================================================

print("\n3. Exécutez cette cellule et cliquez sur 'Choisir les fichiers' pour **UPLOADER** votre feuille de match PDF.")

# --- BLOC D'UPLOAD ---
try:
    from google.colab import files
    uploaded_files = files.upload()
    if uploaded_files:
        PDF_FILENAME = list(uploaded_files.keys())[0]
        print(f"\nFichier téléchargé : **{PDF_FILENAME}**")
    else:
        print("\n❌ Aucun fichier téléchargé. Veuillez relancer la cellule et uploader un PDF.")
        PDF_FILENAME = None

except Exception as e:
    print(f"\n❌ Échec de l'upload du fichier. Détails de l'erreur: {e}. Veuillez relancer la cellule.")
    PDF_FILENAME = None


if PDF_FILENAME:

    # ----------------------------------------------------------------------
    # 0. 🔍 IDENTIFICATION DES ÉQUIPES (QUART SUPÉRIEUR)
    # ----------------------------------------------------------------------

    # Récupération et nettoyage des noms EQUIPE_A et EQUIPE_B
    EQUIPE_A, EQUIPE_B = process_and_structure_noms_equipes(PDF_FILENAME)

    print("\n" + "═"*60)
    print(f" 🏐  MATCH : {EQUIPE_A}  🆚  {EQUIPE_B} ".center(60))
    print("═"*60 + "\n")

    diagnostic_extraction_brute(PDF_FILENAME)

    print("\n🔹 JOUEURS :")
    DF_JOUEURS = extraire_joueurs_df(PDF_FILENAME)
    display(DF_JOUEURS)
    print("\n🔹 LIBÉROS :")
    DF_LIBEROS = extraire_liberos_df(PDF_FILENAME)
    display(DF_LIBEROS)
    print("\n🔹 ENTRAINEUR :")
    DF_STAFF   = extraire_staff_df(PDF_FILENAME)
    display(DF_STAFF)

    # ----------------------------------------------------------------------
    # 1. ANALYSE DU TABLEAU DES SCORES (LE GUIDE D'AFFICHAGE)
    # ----------------------------------------------------------------------
    RAW_DATAFRAME_DATA = analyze_data(PDF_FILENAME)
    FINAL_DATAFRAME_SCORES = None

    if RAW_DATAFRAME_DATA is not None:
        FINAL_DATAFRAME_SCORES = process_and_structure_scores(RAW_DATAFRAME_DATA)
        if FINAL_DATAFRAME_SCORES is not None:
            display_dataframe(FINAL_DATAFRAME_SCORES, "TABLEAU RÉCAPITULATIF DES SCORES")

    # ----------------------------------------------------------------------
    # 2. ANALYSE ET AFFICHAGE CONDITIONNEL DES SETS
    # ----------------------------------------------------------------------

    # --- 🏐 ANALYSE SET 1 (Condition: Ligne R0) ---
    if check_set_exists(FINAL_DATAFRAME_SCORES, 0):
        score_a = FINAL_DATAFRAME_SCORES.iloc[0, 0]
        score_b = FINAL_DATAFRAME_SCORES.iloc[0, 1]

        print("\n" + "="*50 + f"\n🔥 ANALYSE DU SET 1 (Score final: {score_a} - {score_b})\n" + "="*50)

        RAW_DATAFRAME_SET_1_a = extract_raw_set_1_a(PDF_FILENAME)
        RAW_DATAFRAME_SET_1_b = extract_raw_set_1_b(PDF_FILENAME)
        TM = extract_temps_mort_set_1(PDF_FILENAME)

        print(f"⏱️ TEMPS MORTS")
        print(f"   • {EQUIPE_A} : {TM[0] if TM[0] else '—'} , {TM[1] if TM[1] else '—'}")
        print(f"   • {EQUIPE_B} : {TM[2] if TM[2] else '—'} , {TM[3] if TM[3] else '—'}")

        if RAW_DATAFRAME_SET_1_a is not None and RAW_DATAFRAME_SET_1_b is not None:
            FINAL_DATAFRAME_SET_1_a = process_and_structure_set_1_a(RAW_DATAFRAME_SET_1_a)
            FINAL_DATAFRAME_SET_1_b = process_and_structure_set_1_b(RAW_DATAFRAME_SET_1_b)

            display_dataframe(FINAL_DATAFRAME_SET_1_a, f"TABLEAU FINAL SET 1 - {EQUIPE_A}")
            display_dataframe(FINAL_DATAFRAME_SET_1_b, f"TABLEAU FINAL SET 1 - {EQUIPE_B}")

            tracer_duel_equipes(FINAL_DATAFRAME_SET_1_a,
                                FINAL_DATAFRAME_SET_1_b,
                                titre=f"Duel Set 1 : {EQUIPE_A} vs {EQUIPE_B}",
                                nom_g=EQUIPE_A,
                                nom_d=EQUIPE_B)
            afficher_les_deux_rotations("CNM CHARENTON", FINAL_DATAFRAME_SET_1_a,
                            "LESCAR PVB", FINAL_DATAFRAME_SET_1_b)

    # --- 🏐 ANALYSE SET 2 (Condition: Ligne R1) ---
    if check_set_exists(FINAL_DATAFRAME_SCORES, 1):
        score_a = FINAL_DATAFRAME_SCORES.iloc[1, 0]
        score_b = FINAL_DATAFRAME_SCORES.iloc[1, 1]
        print("\n" + "="*50 + f"\n🔥 ANALYSE DU SET 2 (Score final: {score_a} - {score_b})\n" + "="*50)

        # Note: Inversion B à gauche, A à droite pour le Set 2
        RAW_DATAFRAME_SET_2_b = extract_raw_set_2_b(PDF_FILENAME)
        RAW_DATAFRAME_SET_2_a = extract_raw_set_2_a(PDF_FILENAME)
        TM = extract_temps_mort_set_2(PDF_FILENAME)

        print(f"⏱️ TEMPS MORTS")
        print(f"   • {EQUIPE_A} : {TM[2] if TM[2] else '—'} , {TM[3] if TM[3] else '—'}")
        print(f"   • {EQUIPE_B} : {TM[0] if TM[0] else '—'} , {TM[1] if TM[1] else '—'}")

        if RAW_DATAFRAME_SET_2_b is not None and RAW_DATAFRAME_SET_2_a is not None:
            FINAL_DATAFRAME_SET_2_b = process_and_structure_set_2_b(RAW_DATAFRAME_SET_2_b)
            FINAL_DATAFRAME_SET_2_a = process_and_structure_set_2_a(RAW_DATAFRAME_SET_2_a)

            display_dataframe(FINAL_DATAFRAME_SET_2_b, f"TABLEAU FINAL SET 2 - {EQUIPE_B}")
            display_dataframe(FINAL_DATAFRAME_SET_2_a, f"TABLEAU FINAL SET 2 - {EQUIPE_A}")

            tracer_duel_equipes(FINAL_DATAFRAME_SET_2_b,
                                FINAL_DATAFRAME_SET_2_a,
                                titre=f"Duel Set 2 : {EQUIPE_B} vs {EQUIPE_A}",
                                nom_g=EQUIPE_B,
                                nom_d=EQUIPE_A)

    # --- 🏐 ANALYSE SET 3 (Condition: Ligne R2) ---
    if check_set_exists(FINAL_DATAFRAME_SCORES, 2):
        score_a = FINAL_DATAFRAME_SCORES.iloc[2, 0]
        score_b = FINAL_DATAFRAME_SCORES.iloc[2, 1]
        print("\n" + "="*50 + f"\n🔥 ANALYSE DU SET 3 (Score final: {score_a} - {score_b})\n" + "="*50)

        RAW_DATAFRAME_SET_3_a = extract_raw_set_3_a(PDF_FILENAME)
        RAW_DATAFRAME_SET_3_b = extract_raw_set_3_b(PDF_FILENAME)
        TM = extract_temps_mort_set_3(PDF_FILENAME)

        print(f"⏱️ TEMPS MORTS")
        print(f"   • {EQUIPE_A} : {TM[0] if TM[0] else '—'} , {TM[1] if TM[1] else '—'}")
        print(f"   • {EQUIPE_B} : {TM[2] if TM[2] else '—'} , {TM[3] if TM[3] else '—'}")

        if RAW_DATAFRAME_SET_3_a is not None and RAW_DATAFRAME_SET_3_b is not None:
            FINAL_DATAFRAME_SET_3_a = process_and_structure_set_3_a(RAW_DATAFRAME_SET_3_a)
            FINAL_DATAFRAME_SET_3_b = process_and_structure_set_3_b(RAW_DATAFRAME_SET_3_b)

            display_dataframe(FINAL_DATAFRAME_SET_3_a, f"TABLEAU FINAL SET 3 - {EQUIPE_A}")
            display_dataframe(FINAL_DATAFRAME_SET_3_b, f"TABLEAU FINAL SET 3 - {EQUIPE_B}")

            tracer_duel_equipes(FINAL_DATAFRAME_SET_3_a,
                                FINAL_DATAFRAME_SET_3_b,
                                titre=f"Duel Set 3 : {EQUIPE_A} vs {EQUIPE_B}",
                                nom_g=EQUIPE_A,
                                nom_d=EQUIPE_B)

    # --- 🏐 ANALYSE SET 4 (Condition: Ligne R3) ---
    if check_set_exists(FINAL_DATAFRAME_SCORES, 3):
        score_a = FINAL_DATAFRAME_SCORES.iloc[3, 0]
        score_b = FINAL_DATAFRAME_SCORES.iloc[3, 1]
        print("\n" + "="*50 + f"\n🔥 ANALYSE DU SET 4 (Score final: {score_a} - {score_b})\n" + "="*50)

        RAW_DATAFRAME_SET_4_b = extract_raw_set_4_b(PDF_FILENAME)
        RAW_DATAFRAME_SET_4_a = extract_raw_set_4_a(PDF_FILENAME)
        TM = extract_temps_mort_set_4(PDF_FILENAME)

        print(f"⏱️ TEMPS MORTS")
        print(f"   • {EQUIPE_A} : {TM[2] if TM[2] else '—'} , {TM[3] if TM[3] else '—'}")
        print(f"   • {EQUIPE_B} : {TM[0] if TM[0] else '—'} , {TM[1] if TM[1] else '—'}")

        if RAW_DATAFRAME_SET_4_b is not None and RAW_DATAFRAME_SET_4_a is not None:
            FINAL_DATAFRAME_SET_4_b = process_and_structure_set_4_b(RAW_DATAFRAME_SET_4_b)
            FINAL_DATAFRAME_SET_4_a = process_and_structure_set_4_a(RAW_DATAFRAME_SET_4_a)

            display_dataframe(FINAL_DATAFRAME_SET_4_b, f"TABLEAU FINAL SET 4 - {EQUIPE_B}")
            display_dataframe(FINAL_DATAFRAME_SET_4_a, f"TABLEAU FINAL SET 4 - {EQUIPE_A}")

            tracer_duel_equipes(FINAL_DATAFRAME_SET_4_b,
                                FINAL_DATAFRAME_SET_4_a,
                                titre=f"Duel Set 4 : {EQUIPE_B} vs {EQUIPE_A}",
                                nom_g=EQUIPE_B,
                                nom_d=EQUIPE_A)

    # --- 🏐 ANALYSE SET 5 (Condition: Ligne R4) ---
    if check_set_exists(FINAL_DATAFRAME_SCORES, 4):
        score_a = FINAL_DATAFRAME_SCORES.iloc[4, 0]
        score_b = FINAL_DATAFRAME_SCORES.iloc[4, 1]
        print("\n" + "="*50 + f"\n🔥 ANALYSE DU SET 5 (Score final: {score_a} - {score_b})\n" + "="*50)

        RAW_DATAFRAME_SET_5_a = extract_raw_set_5_a(PDF_FILENAME)
        RAW_DATAFRAME_SET_5_b = extract_raw_set_5_b(PDF_FILENAME)
        TM = extract_temps_mort_set_5(PDF_FILENAME)

        print(f"⏱️ TEMPS MORTS")
        print(f"   • {EQUIPE_A} : {TM[0] if TM[0] else '—'} , {TM[1] if TM[1] else '—'}")
        print(f"   • {EQUIPE_B} : {TM[2] if TM[2] else '—'} , {TM[3] if TM[3] else '—'}")

        if RAW_DATAFRAME_SET_5_a is not None and RAW_DATAFRAME_SET_5_b is not None:
            FINAL_DATAFRAME_SET_5_a = process_and_structure_set_5_a(RAW_DATAFRAME_SET_5_a)
            FINAL_DATAFRAME_SET_5_b = process_and_structure_set_5_b(RAW_DATAFRAME_SET_5_b)

            display_dataframe(FINAL_DATAFRAME_SET_5_a, f"TABLEAU FINAL SET 5 - {EQUIPE_A}")
            display_dataframe(FINAL_DATAFRAME_SET_5_b, f"TABLEAU FINAL SET 5 - {EQUIPE_B}")

            tracer_duel_equipes(FINAL_DATAFRAME_SET_5_a,
                                FINAL_DATAFRAME_SET_5_b,
                                titre=f"Duel Set 5 : {EQUIPE_A} vs {EQUIPE_B}",
                                nom_g=EQUIPE_A,
                                nom_d=EQUIPE_B)

else:
    print("\n⚠️ Veuillez uploader un fichier PDF pour lancer l'analyse.")
