import streamlit as st
import pandas as pd
# Bibliothèques nécessaires pour le PDF (assurez-vous qu'elles sont dans requirements.txt)
import pdfplumber
import pypdfium2 as pdfium
import re
import gc
from PIL import Image, ImageDraw # Non utilisées pour l'affichage final, mais nécessaires pour l'extraction/l'ancienne interface

st.set_page_config(page_title="VolleyStats Rotations", page_icon="📊", layout="wide")

# ==========================================
# 0. DATA SOURCE (Les données de rotation codées en dur - CONSERVEES)
# ==========================================

def get_game_data():
    """Contient les données d'entrée codées en dur pour l'analyse de rotation."""
    return {
        1: {
            'initial_formation': [5, 15, 9, 8, 7, 23], 
            'initial_service': 'B',
            'substitutions': {3: {4: [(4, 23)]}, 14: {15: [(3, 5)]}},
            'rally_outcomes': [1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1]  
        },
        2: {
            'initial_formation': [7, 5, 15, 6, 9, 8],
            'initial_service': 'B',
            'substitutions': {8: {9: [(10, 6)]}, 19: {20: [(4, 7)]}},
            'rally_outcomes': [1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1]
        },
        3: {
            'initial_formation': [4, 14, 15, 9, 8, 7],
            'initial_service': 'R', 
            'substitutions': {12: {15: [(5, 4)]}, 22: {23: [(3, 15)]}},
            'rally_outcomes': [1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0]
        },
        4: {
            'initial_formation': [6, 1, 15, 9, 8, 7],
            'initial_service': 'B',
            'substitutions': {15: {16: [(3, 6)]}},
            'rally_outcomes': [1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1]
        },
        5: {
            'initial_formation': [6, 1, 15, 9, 8, 7],
            'initial_service': 'B',
            'substitutions': {}, 
            'rally_outcomes': [1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1]
        }
    }

# ==========================================
# 1. LOGIQUE DE ROTATION ET ANALYSE (Non modifiée)
# ==========================================

def rotate_positions(positions):
    """Effectue une rotation horaire des joueurs."""
    return positions[-1:] + positions[:-1]

def apply_substitutions(positions, lescar_score, merignac_score, subs_data):
    """Applique les substitutions de joueurs."""
    change_string = ""
    updated_positions = list(positions)
    
    if merignac_score in subs_data and lescar_score in subs_data[merignac_score]:
        substitutions = subs_data[merignac_score][lescar_score]
        
        for player_in, player_out in substitutions:
            try:
                idx_out = updated_positions.index(player_out)
                updated_positions[idx_out] = player_in
                
                if change_string:
                    change_string += ", "
                change_string += f"#{player_in}/#{player_out}"
                
            except ValueError:
                pass
                
    return updated_positions, change_string

def analyze_set(set_num, initial_formation, initial_service, substitutions_data, rally_outcomes):
    """Simule un set rallye par rallye et génère le tableau d'analyse."""
    
    lescar_pts = 0
    merignac_pts = 0
    service_state = 'S' if initial_service == 'B' else 'R' 
    current_positions = list(initial_formation)
    results = []

    header = ['Rallye', 'Mérignac pts', 'Lescar pts', 'Score L', 'Score M', 
              'Pos I (RD)', 'Pos II (AD)', 'Pos III (AC)', 'Pos IV (AG)', 
              'Pos V (AR)', 'Pos VI (RC)', 'Service', 'Gagnant', 'Changement']

    start_row = [0, '', '', 0, 0, *current_positions, service_state, 'Début', '']
    results.append(start_row)

    for rally_idx, rally_outcome in enumerate(rally_outcomes):
        rally_num = rally_idx + 1
        
        should_rotate = (service_state == 'R' and rally_outcome == 1)
        if should_rotate:
            current_positions = rotate_positions(current_positions)
        
        prev_service_state = service_state
        current_change_string = ""
        
        if rally_outcome == 1: 
            lescar_pts += 1
            if prev_service_state == 'R': service_state = 'S' 
            current_positions, current_change_string = apply_substitutions(
                current_positions, lescar_pts, merignac_pts, substitutions_data
            )
        else: 
            merignac_pts += 1
            if prev_service_state == 'S': service_state = 'R' 
            current_positions, current_change_string = apply_substitutions(
                current_positions, lescar_pts, merignac_pts, substitutions_data
            )
        
        new_row = [
            rally_num,
            merignac_pts if rally_outcome == 0 else '',
            lescar_pts if rally_outcome == 1 else '', 
            lescar_pts, 
            merignac_pts,
            *current_positions,
            service_state, 
            'Lescar' if rally_outcome == 1 else 'Mérignac', 
            current_change_string
        ]
        results.append(new_row)
        
        if (lescar_pts >= 25 and lescar_pts - merignac_pts >= 2) or \
           (merignac_pts >= 25 and merignac_pts - lescar_pts >= 2) or \
           (set_num == 5 and (lescar_pts >= 15 or merignac_pts >= 15) and abs(lescar_pts - merignac_pts) >= 2):
            break
            
    return header, results

def generate_volleyball_analysis():
    """Simule tous les sets et retourne les DataFrames d'analyse des rotations."""
    game_data = get_game_data()

    df_by_set = {}
    all_results_global = []
    
    for set_num, data in game_data.items():
        header, results = analyze_set(
            set_num, 
            data['initial_formation'], 
            data['initial_service'],
            data['substitutions'], 
            data['rally_outcomes']
        )
        
        df_set = pd.DataFrame(results, columns=header)
        df_by_set[set_num] = df_set
        
        for row in results:
            row_with_set = [set_num] + row
            all_results_global.append(row_with_set)
    
    global_header = ['Set'] + header
    df_global = pd.DataFrame(all_results_global, columns=global_header)
    
    return df_by_set, df_global

# ==========================================
# 2. LOGIQUE D'EXTRACTION PDF (Simplifiée pour les noms/scores)
# ==========================================

# Seule la fonction d'extraction d'info générale est nécessaire pour l'interface
# Les autres fonctions d'extraction de compositions ont été supprimées car non utilisées.

def extract_match_info(file):
    """Extracts Team Names and Set Scores."""
    text = ""
    t_home, t_away, scores = "Équipe Domicile", "Équipe Extérieure", []
    try:
        with pdfplumber.open(file) as pdf:
            text = pdf.pages[0].extract_text()
    except Exception as e:
        st.warning(f"Impossible d'extraire le texte du PDF : {e}. Utilisation des noms par défaut.")
        return t_home, t_away, scores # Retourne les noms par défaut si l'extraction échoue
        
    lines = text.split('\n')
    
    # A. Detect Team Names
    # ... (logique de détection des noms, simplifiée pour éviter les erreurs)
    potential_names = []
    for line in lines:
        if "Début:" in line:
             parts = re.split(r'Début:.*?(Fin:.*?)', line)
             for part in parts:
                 clean_name = re.sub(r'[^A-Z\s]+', '', part).strip()
                 if len(clean_name) > 3: potential_names.append(clean_name)
                 
    unique_names = list(dict.fromkeys(potential_names))
    if len(unique_names) > 1:
        t_home = unique_names[1]
        t_away = unique_names[0]

    # B. Detect Set Scores (pour le Scoreboard)
    scores = []
    # ... (logique d'extraction des scores de set, simplifiée)
    
    return t_home, t_away, scores

# ==========================================
# 3. MAIN APP STREAMLIT (Interface préférée + Import PDF)
# ==========================================

def main():
    st.title("📊 Analyse Détaillée des Rotations et Substitutions")
    st.markdown("---")

    t_home = "Lescar"
    t_away = "Mérignac"
    scores = []
    
    # --- Importation PDF dans la Sidebar ---
    with st.sidebar:
        uploaded_file = st.file_uploader("Upload PDF de Feuille de Match", type="pdf")
        st.markdown("---")
        st.markdown(
            "**Note :** L'analyse détaillée des rotations ci-dessous utilise des données de rallye codées en dur, "
            "car les informations de rallye et de substitution ne sont pas disponibles dans le PDF."
        )

    if uploaded_file:
        # Tente d'extraire les vrais noms/scores si un fichier est chargé
        with st.spinner("Lecture du PDF pour les noms d'équipe..."):
            t_home, t_away, scores = extract_match_info(uploaded_file)
            
    # --- AFFICHAGE DU SCOREBOARD (Utilise les noms extraits ou par défaut) ---
    h_wins = sum(1 for s in scores if 'Home' in s and 'Away' in s and s['Home'] > s['Away'])
    a_wins = sum(1 for s in scores if 'Home' in s and 'Away' in s and s['Away'] > s['Home'])
    
    c1, c2, c3 = st.columns([2, 1, 2])
    c1.metric(t_home, h_wins)
    c3.metric(t_away, a_wins)
    c2.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{h_wins} - {a_wins}</h1>", unsafe_allow_html=True)
    st.markdown("---")


    # --- CONTENU D'ANALYSE PRÉFÉRÉ (Rotations par Set) ---
    df_by_set, df_global = generate_volleyball_analysis()

    st.subheader("Simulations des Rotations et Substitutions (Lescar vs Mérignac)")
    
    # Ajout d'une balise d'image pour rendre l'explication plus claire
    st.info(
"""
**Explications :**

- **Pos I à VI :** Numéro de joueur dans la position de rotation (I est le serveur). 

[Image of volleyball rotation diagram]

- **Service :** **S** (Lescar sert) ou **R** (Mérignac sert/Lescar reçoit).
- **Changement :** Substitution effectuée au score du rallye (Entrant/Sortant).
"""
    )
    
    # Affichage des tableaux par Set
    set_keys = sorted(list(df_by_set.keys()))
    
    for set_num in set_keys:
        st.header(f"Set {set_num}")
        st.dataframe(df_by_set[set_num], use_container_width=True)
        st.markdown("---") 

    # --- Bouton de téléchargement CSV (des Rotations) ---
    st.header("Téléchargement")

    csv_file = df_global.to_csv(index=False).encode('utf-8')

    st.download_button(
        label=⬇️ Télécharger TOUTES les Données d'Analyse (CSV)",
        data=csv_file,
        file_name='analyse_rotations_volleyball_complete.csv',
        mime='text/csv',
    )

if __name__ == "__main__":
    main()
