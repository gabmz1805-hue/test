import streamlit as st
import pandas as pd
import pdfplumber
import re
import tempfile
import os 
# Ajout de tempfile et os pour la gestion des fichiers temporaires,
# car pdfplumber ne peut pas lire directement un objet Streamlit UploadedFile

st.set_page_config(page_title="VolleyStats Rotations", page_icon="📊", layout="wide")

# ==========================================
# 0. DATA SOURCE (Les données de rotation codées en dur - MAINTENUES)
# ==========================================

def get_game_data():
    """Contient les données d'entrée codées en dur pour l'analyse de rotation (Home logique)."""
    # Rally outcomes: 1 = Home Logique gagne, 0 = Away Logique gagne
    return {
        1: {
            'initial_formation': [5, 15, 9, 8, 7, 23],  
            'initial_service': 'B', # B = Home Logique 
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
# 1. LOGIQUE DE ROTATION ET ANALYSE (Généralisée)
# ==========================================

def rotate_positions(positions):
    """Effectue une rotation horaire des joueurs."""
    return positions[-1:] + positions[:-1]

def apply_substitutions(positions, t_analysed_score, t_opponent_score, subs_data):
    """Applique les substitutions de joueurs de l'équipe analysée."""
    change_string = ""
    updated_positions = list(positions)
    
    # La substitution est indexée par: Score Adverse (clef principale) puis Score Analysé
    if t_opponent_score in subs_data and t_analysed_score in subs_data[t_opponent_score]:
        substitutions = subs_data[t_opponent_score][t_analysed_score]
        
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

def analyze_set(set_num, initial_formation, initial_service, substitutions_data, rally_outcomes, t_analysed, t_opponent):
    """Simule un set rallye par rallye et génère le tableau d'analyse."""
    
    t_analysed_pts = 0
    t_opponent_pts = 0
    service_state = 'S' if initial_service == 'B' else 'R'  # 'B' pour Home Logique (Analysée), 'R' pour Away Logique (Opponent)
    current_positions = list(initial_formation)
    results = []

    # Les en-têtes sont générés dynamiquement
    header = [
        'Rallye', 
        f'{t_opponent} pts', 
        f'{t_analysed} pts', 
        f'Score {t_analysed[0]}', # Ex: Score L
        f'Score {t_opponent[0]}', # Ex: Score M
        'Pos I (RD)', 'Pos II (AD)', 'Pos III (AC)', 'Pos IV (AG)', 
        'Pos V (AR)', 'Pos VI (RC)', 
        'Service', 'Gagnant', 'Changement'
    ]

    start_row = [0, '', '', 0, 0, *current_positions, service_state, 'Début', '']
    results.append(start_row)

    for rally_idx, rally_outcome in enumerate(rally_outcomes):
        rally_num = rally_idx + 1
        
        # Rotation de l'équipe analysée si c'était la réception et elle gagne le point
        should_rotate = (service_state == 'R' and rally_outcome == 1)
        if should_rotate:
            current_positions = rotate_positions(current_positions)
        
        prev_service_state = service_state
        current_change_string = ""
        
        if rally_outcome == 1:  # L'équipe analysée gagne le point
            t_analysed_pts += 1
            if prev_service_state == 'R': service_state = 'S' # Change de service
            current_positions, current_change_string = apply_substitutions(
                current_positions, t_analysed_pts, t_opponent_pts, substitutions_data
            )
            winner_name = t_analysed
        else:  # L'équipe adverse gagne le point
            t_opponent_pts += 1
            if prev_service_state == 'S': service_state = 'R' # Change de service
            current_positions, current_change_string = apply_substitutions(
                current_positions, t_analysed_pts, t_opponent_pts, substitutions_data
            ) # Les substitutions sont toujours appliquées à l'équipe analysée
            winner_name = t_opponent
        
        new_row = [
            rally_num,
            t_opponent_pts if rally_outcome == 0 else '',
            t_analysed_pts if rally_outcome == 1 else '',  
            t_analysed_pts,  
            t_opponent_pts,
            *current_positions,
            service_state,  
            winner_name,  
            current_change_string
        ]
        results.append(new_row)
        
        # Condition de fin de set
        if (t_analysed_pts >= 25 and t_analysed_pts - t_opponent_pts >= 2) or \
           (t_opponent_pts >= 25 and t_opponent_pts - t_analysed_pts >= 2) or \
           (set_num == 5 and (t_analysed_pts >= 15 or t_opponent_pts >= 15) and abs(t_analysed_pts - t_opponent_pts) >= 2):
            break
            
    return header, results

def generate_volleyball_analysis(t_analysed, t_opponent):
    """Simule tous les sets avec les noms dynamiques."""
    game_data = get_game_data()

    df_by_set = {}
    all_results_global = []
    
    for set_num, data in game_data.items():
        header, results = analyze_set(
            set_num, data['initial_formation'], data['initial_service'],
            data['substitutions'], data['rally_outcomes'], t_analysed, t_opponent
        )
        
        df_set = pd.DataFrame(results, columns=header)
        df_by_set[set_num] = df_set
        
        for row in results:
            row_with_set = [set_num] + row
            all_results_global.append(row_with_set)
    
    global_header = ['Set'] + header
    df_global = pd.DataFrame(all_results_global, columns=global_header)
    
    return df_by_set, df_global

def get_reversed_analysis_df(df_analysed, t_analysed, t_opponent):
    """Génère le tableau de l'adversaire en inversant les colonnes de score/gagnant."""
    df_reversed = df_analysed.copy()

    # Logique d'inversion des noms dans les en-têtes
    old_headers = df_analysed.columns.tolist()
    new_headers = [
        h.replace(f'{t_analysed} pts', 'TEMP_OPPONENT_PTS')
         .replace(f'{t_opponent} pts', f'{t_analysed} pts')
         .replace('TEMP_OPPONENT_PTS', f'{t_opponent} pts')
         .replace(f'Score {t_analysed[0]}', 'TEMP_SCORE_OPPONENT')
         .replace(f'Score {t_opponent[0]}', f'Score {t_analysed[0]}')
         .replace('TEMP_SCORE_OPPONENT', f'Score {t_opponent[0]}')
        for h in old_headers
    ]
    df_reversed.columns = new_headers

    # Inversion des valeurs dans les colonnes de score (pts individuels et totaux)
    # colonnes index 1, 2 = pts individuels; 3, 4 = scores totaux
    df_reversed.iloc[:, [1, 2]] = df_analysed.iloc[:, [2, 1]].values
    df_reversed.iloc[:, [3, 4]] = df_analysed.iloc[:, [4, 3]].values

    # Inversion de la colonne Gagnant
    df_reversed['Gagnant'] = df_analysed['Gagnant'].replace({
        t_analysed: t_opponent,
        t_opponent: t_analysed,
        'Début': 'Début'
    })
    
    return df_reversed

# ==========================================
# 2. LOGIQUE D'EXTRACTION PDF (Améliorée)
# ==========================================

def extract_match_info(file):
    """Tente d'extraire les noms d'équipe et les scores de set du PDF."""
    
    t_home, t_away, scores = "Équipe A", "Équipe B", []
    
    # Écrit le fichier temporaire car pdfplumber ne peut pas lire directement un objet Streamlit UploadedFile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(file.getvalue())
        tmp_path = tmp_file.name

    try:
        with pdfplumber.open(tmp_path) as pdf:
            text = pdf.pages[0].extract_text()
        
        lines = text.split('\n')
        
        # A. Détection des noms d'équipe (recherche plus tolérante)
        potential_names = []
        for line in lines:
            # Cherche les noms entre 'Début:' et 'Fin:'
            if "Début:" in line:
                  parts = re.split(r'Début:.*?(Fin:.*?)', line)
                  for part in parts:
                      # Nettoyage : suppression des caractères non alphabétiques/espaces (sauf le 'VB' final)
                      clean_name = re.sub(r'[^A-Z\s]+', '', part.upper()).strip()
                      # Supprime les entêtes de colonnes (IV, V, VI...) qui peuvent être extraites
                      if len(clean_name) > 3 and not any(word in clean_name for word in ["IV", "V", "VI", "SET", "FIN", "DEBUT"]):
                          potential_names.append(clean_name)
        
        # Supprime les doublons
        unique_names = list(dict.fromkeys(potential_names))
        
        if len(unique_names) >= 2:
            # Souvent, le nom de l'équipe B (Home Logique) est en premier dans l'extraction
            t_home = unique_names[0]
            t_away = unique_names[1] 
        elif len(unique_names) == 1:
             t_home = unique_names[0]
             t_away = "Adversaire Inconnu"

        # B. Détection des scores (à partir du bloc RESULTATS)
        # Tente de trouver le bloc RESULTATS
        results_match = re.search(r'RESULTATS(.+?)SIGNATURES', text, re.DOTALL)
        if results_match:
            results_text = results_match.group(1)
            # Regex pour trouver les scores de set (ex: 25, 18)
            set_scores_matches = re.findall(r'(\d{1,2})\s*\'*\s*\n\s*\d+\s*\'*\n\s*(\d{1,2})\s*\n', results_text)
            
            for score_a, score_b in set_scores_matches:
                 scores.append({'Home': int(score_a), 'Away': int(score_b)})

    except Exception as e:
        st.warning(f"Impossible d'extraire le texte du PDF : {e}. Utilisation des noms et scores par défaut.")
    finally:
        os.remove(tmp_path) # Nettoie le fichier temporaire
        
    return t_home, t_away, scores

# ==========================================
# 3. MAIN APP STREAMLIT (Interface généralisée)
# ==========================================

def main():
    st.title("📊 Analyse Détaillée des Rotations et Substitutions")
    st.markdown("---")
    
    # --- Initialisation des noms ---
    t_a_default = "Équipe A"
    t_b_default = "Équipe B"
    t_a, t_b, scores = t_a_default, t_b_default, []

    # --- Importation PDF dans la Sidebar ---
    with st.sidebar:
        uploaded_file = st.file_uploader("Upload PDF de Feuille de Match", type="pdf")
        st.markdown("---")

    if uploaded_file:
        # Tente d'extraire les vrais noms/scores si un fichier est chargé
        with st.spinner("Lecture du PDF pour les noms d'équipe et les scores..."):
            t_a, t_b, scores = extract_match_info(uploaded_file)
            
        st.success(f"Noms d'équipe extraits : **{t_a}** et **{t_b}**")
    
    # --- DÉFINITION DE LA PERSPECTIVE D'ANALYSE (Question généralisée) ---
    
    st.subheader("Définir la perspective de l'analyse")
    st.warning(
        f"""
        **Étape Cruciale :** Les données de rotation codées en dur concernent une seule équipe (l'équipe "Home logique"). 
        Veuillez indiquer **quelle équipe correspond aux rotations (formations, substitutions)** enregistrées dans le code pour ce match :
        """
    )
    
    # Utilise les noms extraits ou les noms par défaut
    perspective_choice = st.radio(
        "Quelle équipe analyser ?",
        [t_a, t_b]
    )
    
    # Définition des rôles
    t_analysed = perspective_choice
    t_opponent = t_b if perspective_choice == t_a else t_a
    
    st.markdown(f"**Équipe Analysée :** **{t_analysed}** (Home logique). **Adversaire :** **{t_opponent}** (Away logique).")
    st.markdown("---")

    # --- AFFICHAGE DU SCOREBOARD (Utilise les noms extraits ou par défaut) ---
    h_wins = sum(1 for s in scores if s['Home'] > s['Away'])
    a_wins = sum(1 for s in scores if s['Away'] > s['Home'])
    
    c1, c2, c3 = st.columns([2, 1, 2])
    c1.metric(t_analysed, h_wins)
    c3.metric(t_opponent, a_wins)
    c2.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{h_wins} - {a_wins}</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # --- CONTENU D'ANALYSE PRÉFÉRÉ (Rotations par Set) ---
    
    with st.spinner(f"Génération des simulations de rotation pour {t_analysed}..."):
        df_by_set_analysed, df_global_analysed = generate_volleyball_analysis(t_analysed, t_opponent)
    
    # Génération de l'analyse adverse par inversion
    df_by_set_opponent = {
        set_num: get_reversed_analysis_df(df, t_analysed, t_opponent)
        for set_num, df in df_by_set_analysed.items()
    }
    
    tab_analysed, tab_opponent = st.tabs([f"🎯 Rotations {t_analysed}", f"⚔️ Rotations {t_opponent}"])

    # --- ONGLETS ÉQUIPE ANALYSÉE ---
    with tab_analysed:
        st.header(f"Rotations de l'Équipe Analysée : {t_analysed}")
        st.info(
            f"Ce tableau montre la situation (position des joueurs, service) du point de vue de l'équipe **{t_analysed}** (Home logique). "
        )
        
        for set_num, df in df_by_set_analysed.items():
            st.subheader(f"Set {set_num}")
            st.dataframe(df, use_container_width=True)
            
        st.markdown("---")
        csv_file = df_global_analysed.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="⬇️ Télécharger TOUTES les Données d'Analyse (CSV)",
            data=csv_file,
            file_name=f'analyse_rotations_{t_analysed}_vs_{t_opponent}.csv',
            mime='text/csv',
        )

    # --- ONGLETS ADVERSAIRE ---
    with tab_opponent:
        st.header(f"Rotations de l'Adversaire : {t_opponent}")
        st.warning(
            f"""
            ⚠️ **Attention :** Ce tableau inverse les scores et le gagnant. Les colonnes de position (Pos I-VI) et de service reflètent **TOUJOURS** la situation du côté **{t_analysed}**, car les données de rotation de {t_opponent} sont inconnues.
            """
        )
        
        for set_num, df in df_by_set_opponent.items():
            st.subheader(f"Set {set_num}")
            st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
