import streamlit as st
import pandas as pd
import pdfplumber
import re
import tempfile
import os 
import gc

st.set_page_config(page_title="VolleyStats Rotations", page_icon="📊", layout="wide")

# ==========================================
# CONSTANTE : Nom de l'équipe analysée par défaut
# ==========================================
TEAM_ANALYSED_KEYWORD = "LESCAR PYRENEES VOLLEY" 

# ==========================================
# 0. DATA SOURCE (Les données de rotation codées en dur - MAINTENUES)
# ==========================================

def get_game_data():
    """Contient les données d'entrée codées en dur pour l'analyse de rotation (Home logique/Analysée)."""
    # Rally outcomes: 1 = Home Logique gagne, 0 = Away Logique gagne
    return {
        1: {
            # Formation Set 1 Merignac-Lescar (anciennement utilisée)
            'initial_formation': [5, 15, 9, 8, 7, 23],  
            'initial_service': 'B', # B = Home Logique (Analysée)
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

# Fonctions rotate_positions, apply_substitutions, analyze_set, generate_volleyball_analysis, get_reversed_analysis_df 
# (similaires à la version V5, mais avec la correction du bug de syntaxe)

def rotate_positions(positions):
    """Effectue une rotation horaire des joueurs."""
    return positions[-1:] + positions[:-1]

def apply_substitutions(positions, t_analysed_score, t_opponent_score, subs_data):
    """Applique les substitutions de joueurs de l'équipe analysée."""
    change_string = ""
    updated_positions = list(positions)
    
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

    header = [
        'Rallye', 
        f'{t_opponent} pts', 
        f'{t_analysed} pts', 
        f'Score {t_analysed[0]}', 
        f'Score {t_opponent[0]}', 
        'Pos I (RD)', 'Pos II (AD)', 'Pos III (AC)', 'Pos IV (AG)', 
        'Pos V (AR)', 'Pos VI (RC)', 
        'Service', 'Gagnant', 'Changement'
    ]

    start_row = [0, '', '', 0, 0, *current_positions, service_state, 'Début', '']
    results.append(start_row)

    for rally_idx, rally_outcome in enumerate(rally_outcomes):
        rally_num = rally_idx + 1
        
        should_rotate = (service_state == 'R' and rally_outcome == 1)
        if should_rotate:
            current_positions = rotate_positions(current_positions)
        
        prev_service_state = service_state
        current_change_string = ""
        
        if rally_outcome == 1:  # L'équipe analysée gagne le point
            t_analysed_pts += 1
            if prev_service_state == 'R': service_state = 'S' 
            current_positions, current_change_string = apply_substitutions(
                current_positions, t_analysed_pts, t_opponent_pts, substitutions_data
            )
            winner_name = t_analysed
        else:  # L'équipe adverse gagne le point
            t_opponent_pts += 1
            if prev_service_state == 'S': service_state = 'R' 
            current_positions, current_change_string = apply_substitutions(
                current_positions, t_analysed_pts, t_opponent_pts, substitutions_data
            ) 
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

    df_reversed.iloc[:, [1, 2]] = df_analysed.iloc[:, [2, 1]].values
    df_reversed.iloc[:, [3, 4]] = df_analysed.iloc[:, [4, 3]].values

    df_reversed['Gagnant'] = df_analysed['Gagnant'].replace({
        t_analysed: t_opponent,
        t_opponent: t_analysed,
        'Début': 'Début'
    })
    
    return df_reversed

# ==========================================
# 2. LOGIQUE D'EXTRACTION PDF (Améliorée et Simplifiée)
# ==========================================

def extract_match_info(file):
    """Tente d'extraire les noms d'équipe et les scores de set du PDF."""
    
    t_a, t_b, scores = "Équipe A", "Équipe B", []
    
    # Écrit le fichier temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(file.getvalue())
        tmp_path = tmp_file.name

    try:
        with pdfplumber.open(tmp_path) as pdf:
            text = pdf.pages[0].extract_text()
        
        lines = text.split('\n')
        
        # A. Détection des noms d'équipe (recherche tolérante)
        potential_names = []
        for line in lines:
            if "Début:" in line or "Fin:" in line or "EQUIPE" in line:
                  parts = re.split(r'Début:.*?(Fin:.*?)', line)
                  for part in parts:
                      # Nettoyage
                      clean_name = re.sub(r'[^A-Z\s]+', '', part.upper()).strip()
                      if len(clean_name) > 3 and not any(word in clean_name for word in ["IV", "V", "VI", "SET", "FIN", "DEBUT", "EQUIPE", "SA", "SB", "N", "NOM", "PRENOM"]):
                          potential_names.append(clean_name)
        
        unique_names = list(dict.fromkeys(potential_names))
        
        # Fallback pour s'assurer que Lescar est là si présent
        lescar_found = [n for n in unique_names if TEAM_ANALYSED_KEYWORD in n]
        other_names = [n for n in unique_names if n not in lescar_found]

        if lescar_found:
             t_a = lescar_found[0] # Lescar est en A (équipe analysée)
             t_b = other_names[0] if other_names else "Adversaire Inconnu"
        elif len(unique_names) >= 2:
             t_a = unique_names[0]
             t_b = unique_names[1]
        elif len(unique_names) == 1:
             t_a = unique_names[0]
             t_b = "Adversaire Inconnu"

        # B. Détection des scores
        results_match = re.search(r'RESULTATS(.+?)SIGNATURES', text, re.DOTALL)
        if results_match:
            results_text = results_match.group(1)
            set_scores_matches = re.findall(r'(\d{1,2})\s*\'*\s*\n\s*\d+\s*\'*\n\s*(\d{1,2})\s*\n', results_text)
            
            for score_a, score_b in set_scores_matches:
                 scores.append({'Home': int(score_a), 'Away': int(score_b)})

    except Exception as e:
        st.warning(f"Impossible d'extraire le texte du PDF : {e}. Utilisation des noms et scores par défaut.")
    finally:
        os.remove(tmp_path) 
        
    return t_a, t_b, scores

# ==========================================
# 3. MAIN APP STREAMLIT (Automatisé pour Lescar)
# ==========================================

def main():
    st.title("📊 Analyse Détaillée des Rotations et Substitutions")
    st.markdown("---")
    
    t_a_default = "LESCAR PYRENEES VOLLEY-BALL"
    t_b_default = "ADVERSAIRE (Simulé)"
    t_a, t_b, scores = t_a_default, t_b_default, []

    # --- Importation PDF dans la Sidebar ---
    with st.sidebar:
        uploaded_file = st.file_uploader("Upload PDF de Feuille de Match", type="pdf")
        st.markdown("---")

    if uploaded_file:
        with st.spinner("Lecture du PDF et identification des équipes..."):
            extracted_t_a, extracted_t_b, scores = extract_match_info(uploaded_file)
            
            # Détermination de l'équipe analysée (celle qui correspond aux données codées en dur)
            if TEAM_ANALYSED_KEYWORD in extracted_t_a:
                t_analysed = extracted_t_a
                t_opponent = extracted_t_b
            elif TEAM_ANALYSED_KEYWORD in extracted_t_b:
                t_analysed = extracted_t_b
                t_opponent = extracted_t_a
            else:
                 # Si Lescar n'est pas trouvé, on prend les noms extraits et on avertit
                t_analysed = extracted_t_a
                t_opponent = extracted_t_b
                st.error(
                    f"🚨 **Équipe non identifiée :** Le mot-clé '{TEAM_ANALYSED_KEYWORD}' n'a pas été trouvé. "
                    f"L'analyse des rotations sera effectuée pour '{t_analysed}' (Home Logique) par défaut. "
                    f"Vérifiez que les données codées en dur correspondent à '{t_analysed}'."
                )

        st.success(f"Analyse centrée sur **{t_analysed}** (vs {t_opponent}).")
    else:
        # Sans PDF, on utilise les noms par défaut
        t_analysed = t_a_default
        t_opponent = t_b_default
        st.info(f"Veuillez importer un fichier PDF pour extraire les noms d'équipe. Affichage des noms par défaut: **{t_analysed}** (vs {t_opponent}).")
        
    st.markdown("---")

    # --- AFFICHAGE DU SCOREBOARD ---
    h_wins = sum(1 for s in scores if s['Home'] > s['Away'])
    a_wins = sum(1 for s in scores if s['Away'] > s['Home'])
    
    c1, c2, c3 = st.columns([2, 1, 2])
    c1.metric(t_analysed, h_wins)
    c3.metric(t_opponent, a_wins)
    c2.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{h_wins} - {a_wins}</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # --- CONTENU D'ANALYSE ---
    with st.spinner(f"Génération des simulations de rotation pour {t_analysed}..."):
        df_by_set_analysed, df_global_analysed = generate_volleyball_analysis(t_analysed, t_opponent)
    
    df_by_set_opponent = {
        set_num: get_reversed_analysis_df(df, t_analysed, t_opponent)
        for set_num, df in df_by_set_analysed.items()
    }
    
    # Correction du bug de syntaxe : utilisation d'une f-string multiligne avec des triples guillemets
    tab_analysed, tab_opponent = st.tabs([f"🎯 Rotations {t_analysed}", f"⚔️ Rotations {t_opponent} (Simulé)"])

    # --- ONGLETS ÉQUIPE ANALYSÉE ---
    with tab_analysed:
        st.header(f"Rotations de l'Équipe Analysée : {t_analysed}")
        st.info(
            f"""
            Ce tableau montre la situation (position des joueurs, service) du point de vue de l'équipe **{t_analysed}** (Home logique de la simulation). 
            
                        
            - **Pos I à VI :** Numéro de joueur dans la position de rotation (I est le serveur).
            - **Service :** **S** ({t_analysed} sert) ou **R** ({t_opponent} sert/{t_analysed} reçoit).
            - **Changement :** Substitution effectuée au score du rallye (Entrant/Sortant).
            """
        )
        
        for set_num, df in df_by_set_analysed.items():
            st.subheader(f"Set {set_num}")
            st.dataframe(df, use_container_width=True)
            
        st.markdown("---")
        csv_file = df_global_analysed.to_csv(index=False).encode('utf-8')

        st.download_button(
            label=f"⬇️ Télécharger TOUTES les Données d'Analyse {t_analysed} (CSV)",
            data=csv_file,
            file_name=f'analyse_rotations_{t_analysed}_vs_{t_opponent}.csv',
            mime='text/csv',
        )

    # --- ONGLETS ADVERSAIRE ---
    with tab_opponent:
        st.header(f"Rotations de l'Adversaire : {t_opponent} (Simulées)")
        st.warning(
            f"""
            ⚠️ **Attention :** Ce tableau est une **inversion** de l'analyse de {t_analysed}. 
            Les scores et le gagnant sont inversés, mais les colonnes de position (Pos I-VI) et de service reflètent **TOUJOURS** la situation du côté **{t_analysed}**, car les données de rotation réelles de {t_opponent} sont inconnues.
            """
        )
        
        for set_num, df in df_by_set_opponent.items():
            st.subheader(f"Set {set_num}")
            st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
