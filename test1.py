import streamlit as st
import pandas as pd
import pdfplumber
import re
import tempfile
import os

st.set_page_config(page_title="VolleyStats Rotations", page_icon="📊", layout="wide")

# ==========================================
# CONSTANTE : Nom exact de l'équipe Lescar
# ==========================================
TEAM_LESCAR_FULL = "LESCAR PYRENEES VOLLEY-BALL"

# ==========================================
# 0. DATA SOURCE ET LOGIQUE DE BASE (Inchangée)
# ==========================================

def get_game_data():
    """Contient les données d'entrée codées en dur pour l'analyse de rotation."""
    # Rally outcomes: 1 = Home Logique (l'équipe analysée) gagne, 0 = Away Logique (l'adversaire) gagne
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
        # ... (Autres sets inchangés)
    }

def rotate_positions(positions):
    return positions[-1:] + positions[:-1]

def apply_substitutions(positions, home_score, away_score, subs_data):
    change_string = ""
    updated_positions = list(positions)
    # Logique de substitution inchangée
    if away_score in subs_data and home_score in subs_data[away_score]:
        substitutions = subs_data[away_score][home_score]
        
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

def analyze_set(set_num, initial_formation, initial_service, substitutions_data, rally_outcomes, t_home, t_away):
    """Simule un set rallye par rallye et génère le tableau d'analyse."""
    
    home_pts = 0 
    away_pts = 0 
    service_state = 'S' if initial_service == 'B' else 'R'  
    current_positions = list(initial_formation)
    results = []

    header = [
        'Rallye', 
        f'{t_away} pts',    
        f'{t_home} pts',    
        f'Score {t_home[0]}', 
        f'Score {t_away[0]}', 
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
        
        if rally_outcome == 1:  # Home Logique (t_home) gagne
            home_pts += 1
            if prev_service_state == 'R': service_state = 'S' 
            current_positions, current_change_string = apply_substitutions(current_positions, home_pts, away_pts, substitutions_data)
            winner_name = t_home
        else:  # Away Logique (t_away) gagne
            away_pts += 1
            if prev_service_state == 'S': service_state = 'R' 
            current_positions, current_change_string = apply_substitutions(current_positions, home_pts, away_pts, substitutions_data)
            winner_name = t_away
        
        new_row = [
            rally_num,
            away_pts if rally_outcome == 0 else '',
            home_pts if rally_outcome == 1 else '',  
            home_pts,  
            away_pts,
            *current_positions,
            service_state,  
            winner_name,  
            current_change_string
        ]
        results.append(new_row)
        
        if (home_pts >= 25 and home_pts - away_pts >= 2) or \
           (away_pts >= 25 and away_pts - home_pts >= 2) or \
           (set_num == 5 and (home_pts >= 15 or away_pts >= 15) and abs(home_pts - away_pts) >= 2):
            break
            
    return header, results

def generate_volleyball_analysis(t_home, t_away):
    """Génère l'analyse complète (t_home est l'équipe analysée)."""
    game_data = get_game_data()

    df_by_set = {}
    df_global = pd.DataFrame() 

    for set_num, data in game_data.items():
        header, results = analyze_set(
            set_num, data['initial_formation'], data['initial_service'],
            data['substitutions'], data['rally_outcomes'], t_home, t_away
        )
        df_set = pd.DataFrame(results, columns=header)
        df_by_set[set_num] = df_set
    
    all_results_global = []
    global_header = ['Set'] + header
    for set_num, df in df_by_set.items():
        for _, row in df.iterrows():
            all_results_global.append([set_num] + row.tolist())
    df_global = pd.DataFrame(all_results_global, columns=global_header)
    
    return df_by_set, df_global

def get_reversed_analysis_df(df_analysed, t_analysed, t_adverse):
    """Crée une version du DataFrame d'analyse vue de l'équipe adverse."""
    df_reversed = df_analysed.copy()

    # Inverse les noms des colonnes pour refléter la vue adverse
    old_headers = df_analysed.columns.tolist()
    new_headers = [
        h.replace(f'{t_analysed} pts', 'TEMP_ADVERSE_PTS')
         .replace(f'{t_adverse} pts', f'{t_analysed} pts')
         .replace('TEMP_ADVERSE_PTS', f'{t_adverse} pts')
         .replace(f'Score {t_analysed[0]}', 'TEMP_SCORE_ADVERSE')
         .replace(f'Score {t_adverse[0]}', f'Score {t_analysed[0]}')
         .replace('TEMP_SCORE_ADVERSE', f'Score {t_adverse[0]}')
        for h in old_headers
    ]
    df_reversed.columns = new_headers

    # Inversion des points marqués (colonnes 1 et 2 dans le DF original)
    df_reversed[[f'{t_adverse} pts', f'{t_analysed} pts']] = df_analysed.iloc[:, [2, 1]] 

    # Inversion des scores cumulés (colonnes 3 et 4 dans le DF original)
    df_reversed[[f'Score {t_adverse[0]}', f'Score {t_analysed[0]}']] = df_analysed.iloc[:, [4, 3]] 

    # Inversion de la colonne 'Gagnant'
    df_reversed['Gagnant'] = df_analysed['Gagnant'].replace({
        t_analysed: t_adverse,
        t_adverse: t_analysed
    })
    
    return df_reversed

# ==========================================
# 2. LOGIQUE D'EXTRACTION PDF
# ==========================================

def extract_match_info(file):
    """
    Extracts Team Names. Returns: name1, name2, scores (les deux noms extraits du PDF, l'ordre n'est pas important ici)
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name
        
        with pdfplumber.open(tmp_path) as pdf:
            text = pdf.pages[0].extract_text()
        
        os.remove(tmp_path)
            
    except Exception:
        return TEAM_LESCAR_FULL, "ADVERSAIRE INCONNU", [] 
        
    lines = text.split('\n')
    
    potential_names = []
    for line in lines:
        if "Début:" in line:
              parts = re.split(r'Début:.*?(Fin:.*?)', line)
              for part in parts:
                  clean_name = re.sub(r'[^A-Z\s]+', '', part).strip()
                  if len(clean_name) > 3: potential_names.append(clean_name)
                  
    unique_names = list(dict.fromkeys(potential_names))
    
    if len(unique_names) >= 2:
        return unique_names[0], unique_names[1], [] 
    elif len(unique_names) == 1:
        return unique_names[0], "ADVERSAIRE INCONNU", []
    
    return TEAM_LESCAR_FULL, "ADVERSAIRE INCONNU", []

# ==========================================
# 3. MAIN APP STREAMLIT (avec Sélection Manuelle)
# ==========================================

def main():
    st.title("📊 Analyse Détaillée des Rotations et Substitutions")
    st.markdown("---")
    
    st.subheader("Importez votre Feuille de Match (PDF) pour lancer l'analyse")
    uploaded_file = st.file_uploader("Upload PDF de Feuille de Match", type="pdf", label_visibility="collapsed")
    st.markdown("---")
    
    if uploaded_file:
        
        # 1. Extraction des noms depuis le PDF
        with st.spinner("Lecture du PDF et identification des équipes..."):
            name_a, name_b, scores = extract_match_info(uploaded_file)
            
        # --- LOGIQUE D'IDENTIFICATION DE LESCAR ---
        
        t_lescar = ""
        t_adverse = ""
        
        # On vérifie quel nom correspond à Lescar pour les identifier clairement
        team_lescar_upper = TEAM_LESCAR_FULL.upper()
        
        if team_lescar_upper in name_a.upper():
            t_lescar = name_a
            t_adverse = name_b
        elif team_lescar_upper in name_b.upper():
            t_lescar = name_b
            t_adverse = name_a
        else:
            st.error(
                f"🚨 **Équipe non identifiée :** L'équipe Lescar ('{TEAM_LESCAR_FULL}') n'a pas été trouvée dans les noms extraits du PDF ('{name_a}' et '{name_b}')."
            )
            return 
        
        st.success(f"Noms identifiés : **{t_lescar}** vs **{t_adverse}**")
        st.markdown("---")
        
        # 2. SÉLECTION MANUELLE DE LA PERSPECTIVE D'ANALYSE
        st.subheader("Définir la perspective de l'analyse")
        st.warning(
            f"**Information cruciale :** Les données de rotation du code concernent une seule équipe (l'équipe 'Home logique'). "
            f"Veuillez indiquer quelle équipe correspond à cette analyse pour ce match précis :"
        )
        
        perspective_choice = st.radio(
            "Quelle équipe correspond aux rotations enregistrées dans le code ?",
            [t_lescar, t_adverse]
        )
        
        # Définition des rôles dans la simulation
        if perspective_choice == t_lescar:
            t_analysed = t_lescar    # Équipe dont la rotation est suivie
            t_opponent = t_adverse   # L'autre équipe
        else:
            t_analysed = t_adverse   # L'adversaire est l'équipe dont la rotation est suivie
            t_opponent = t_lescar    # Lescar est l'adversaire de l'équipe analysée
            
        st.markdown("---")
        
        # 3. Génération et affichage des tableaux
        
        with st.spinner(f"Génération de l'analyse pour {t_analysed} (équipe analysée)..."):
            # L'équipe analysée est toujours t_home logique, l'autre est t_away logique
            df_by_set_analysed, df_global_analysed = generate_volleyball_analysis(t_analysed, t_opponent)
        
        # Génération de l'analyse adverse par inversion
        df_by_set_opponent = {
            set_num: get_reversed_analysis_df(df, t_analysed, t_opponent)
            for set_num, df in df_by_set_analysed.items()
        }
        
        # 4. Affichage via les onglets
        tab_analysed, tab_opponent = st.tabs([f"🎯 {t_analysed} (Analyse)", f"⚔️ {t_opponent} (Adversaire)"])
        
        
        # --- ONGLETS ÉQUIPE ANALYSÉE ---
        with tab_analysed:
            st.header(f"Rotations de l'Équipe Analysée : {t_analysed}")
            st.info(
                f"Ce tableau montre la situation (position des joueurs, service) du point de vue de l'équipe **{t_analysed}** (L'équipe Home logique de la simulation). 

[Image of volleyball court positions and rotation]
"
            )
            
            # Affichage des tableaux par Set
            for set_num, df in df_by_set_analysed.items():
                st.subheader(f"Set {set_num}")
                st.dataframe(df, use_container_width=True)
                
            # Bouton de téléchargement global
            st.markdown("---")
            csv_file = df_global_analysed.to_csv(index=False).encode('utf-8')

            st.download_button(
                label=f"⬇️ Télécharger toutes les données d'analyse (CSV)",
                data=csv_file,
                file_name=f'analyse_rotations_{t_analysed}_vs_{t_opponent}.csv',
                mime='text/csv',
            )


        # --- ONGLETS ADVERSAIRE ---
        with tab_opponent:
            st.header(f"Rotations de l'Adversaire : {t_opponent}")
            st.warning(
                f"⚠️ **Attention :** Ce tableau inverse les scores et le gagnant. Les colonnes de position (Pos I-VI) et de service reflètent **TOUJOURS** la situation du côté **{t_analysed}**, car les données de rotation de {t_opponent} sont inconnues."
            )
            
            # Affichage des tableaux par Set
            for set_num, df in df_by_set_opponent.items():
                st.subheader(f"Set {set_num}")
                st.dataframe(df, use_container_width=True)

    else:
        st.info(f"Veuillez importer un fichier PDF de feuille de match. L'analyse demandera ensuite quelle équipe correspond aux rotations enregistrées.")

if __name__ == "__main__":
    main()
