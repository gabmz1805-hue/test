import streamlit as st
import pandas as pd
# Bibliothèques nécessaires pour le PDF
import pdfplumber
import re
import gc
from PIL import Image, ImageDraw 
import pypdfium2 as pdfium 
import tempfile
import os

st.set_page_config(page_title="VolleyStats Rotations", page_icon="📊", layout="wide")

# Définition de l'équipe analysée que nous recherchons
TEAM_TO_ANALYZE = "LESCAR"

# ==========================================
# 0. DATA SOURCE (Les données de rotation codées en dur - CONSERVEES)
# ==========================================

def get_game_data():
    """Contient les données d'entrée codées en dur pour l'analyse de rotation."""
    return {
        1: {
            'initial_formation': [5, 15, 9, 8, 7, 23],  
            'initial_service': 'B', # B = Home Logique (l'équipe analysée, Lescar)
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
            'initial_service': 'R',  # R = Away Logique (l'équipe adverse)
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
# 1. LOGIQUE DE ROTATION ET ANALYSE (Utilise t_home=t_analysed et t_away=t_adverse)
# ==========================================

def rotate_positions(positions):
    return positions[-1:] + positions[:-1]

def apply_substitutions(positions, home_score, away_score, subs_data):
    change_string = ""
    updated_positions = list(positions)
    
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
    
    home_pts = 0 # Points de l'équipe analysée
    away_pts = 0 # Points de l'équipe adverse
    service_state = 'S' if initial_service == 'B' else 'R'  
    current_positions = list(initial_formation)
    results = []

    # Les en-têtes utilisent les noms d'équipes dynamiques
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
        
        # Rotation se produit uniquement si Home (équipe analysée) gagne le rallye ALORS qu'elle était en réception (R)
        should_rotate = (service_state == 'R' and rally_outcome == 1)
        if should_rotate:
            current_positions = rotate_positions(current_positions)
        
        prev_service_state = service_state
        current_change_string = ""
        
        if rally_outcome == 1:  # Home (équipe analysée) gagne le rallye
            home_pts += 1
            if prev_service_state == 'R': 
                service_state = 'S' 
            current_positions, current_change_string = apply_substitutions(
                current_positions, home_pts, away_pts, substitutions_data
            )
            winner_name = t_home
        else:  # Away (équipe adverse) gagne le rallye
            away_pts += 1
            if prev_service_state == 'S': 
                service_state = 'R' 
            current_positions, current_change_string = apply_substitutions(
                current_positions, home_pts, away_pts, substitutions_data
            )
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
        
        # Vérification de la fin du set
        if (home_pts >= 25 and home_pts - away_pts >= 2) or \
           (away_pts >= 25 and away_pts - home_pts >= 2) or \
           (set_num == 5 and (home_pts >= 15 or away_pts >= 15) and abs(home_pts - away_pts) >= 2):
            break
            
    return header, results

def generate_volleyball_analysis(t_home, t_away):
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
            data['rally_outcomes'],
            t_home, # L'équipe analysée est passée en t_home logique
            t_away # L'équipe adverse est passée en t_away logique
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
# 2. LOGIQUE D'EXTRACTION PDF
# ==========================================

def extract_match_info(file):
    """
    Extracts Team Names and Set Scores.
    Returns: t_home (PDF Home Name), t_away (PDF Away Name), scores
    """
    # Utilisation de TEAM_TO_ANALYZE pour initialiser t_home si l'extraction échoue
    t_home, t_away, scores = TEAM_TO_ANALYZE, "ADVERSAIRE INCONNU", [] 
    
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name
        
        with pdfplumber.open(tmp_path) as pdf:
            text = pdf.pages[0].extract_text()
        
        os.remove(tmp_path)
            
    except Exception as e:
        st.warning(f"Impossible d'extraire le texte du PDF : {e}. Utilisation des noms par défaut.")
        return t_home, t_away, scores 
        
    lines = text.split('\n')
    
    potential_names = []
    for line in lines:
        if "Début:" in line:
              parts = re.split(r'Début:.*?(Fin:.*?)', line)
              for part in parts:
                  # Nettoyage et capitalisation pour faciliter la recherche (Lescar vs LESCAR)
                  clean_name = re.sub(r'[^A-Z\s]+', '', part).strip()
                  if len(clean_name) > 3: potential_names.append(clean_name)
                  
    unique_names = list(dict.fromkeys(potential_names))
    
    # Si deux noms sont trouvés, on les retourne (le mapping Home/Away du PDF n'a plus d'importance ici)
    if len(unique_names) >= 2:
        return unique_names[1], unique_names[0], scores # Retourne les deux noms extraits (PDF Domicile, PDF Extérieur)
    elif len(unique_names) == 1:
        # Si un seul nom est trouvé, c'est peut-être Lescar, l'autre reste inconnu
        if unique_names[0] == TEAM_TO_ANALYZE:
             return unique_names[0], "ADVERSAIRE INCONNU", scores
        else:
            return TEAM_TO_ANALYZE, unique_names[0], scores

    return TEAM_TO_ANALYZE, "ADVERSAIRE INCONNU", scores

# ==========================================
# 3. MAIN APP STREAMLIT (Identification automatique de Lescar)
# ==========================================

def main():
    st.title("📊 Analyse Détaillée des Rotations et Substitutions")
    st.markdown("---")
    
    # --- Affichage du sélecteur de fichier ---
    st.subheader("Importez votre Feuille de Match (PDF) pour lancer l'analyse")
    uploaded_file = st.file_uploader("Upload PDF de Feuille de Match", type="pdf", label_visibility="collapsed")
    st.markdown("---")
    
    # --- DÉCLENCHEUR ---
    if uploaded_file:
        
        # 1. Extraction des noms depuis le PDF (récupère les noms du PDF sans se soucier du statut Domicile/Extérieur)
        with st.spinner("Lecture du PDF pour les noms d'équipe..."):
            name1, name2, scores = extract_match_info(uploaded_file)
            
        # --- LOGIQUE D'IDENTIFICATION DE LESCAR ---
        
        # Vérifie quel nom est Lescar pour définir t_analysed et t_adverse
        
        # On compare les noms trouvés (name1 et name2) avec l'équipe que nous voulons analyser (TEAM_TO_ANALYZE)
        if name1 == TEAM_TO_ANALYZE:
            t_analysed = name1
            t_adverse = name2
        elif name2 == TEAM_TO_ANALYZE:
            t_analysed = name2
            t_adverse = name1
        else:
            # Si "Lescar" n'est pas trouvé (erreur dans le PDF ou nom différent)
            st.error(
                f"🚨 **Erreur d'identification :** L'équipe '{TEAM_TO_ANALYZE}' n'a pas été trouvée dans le PDF. "
                f"Vérifiez le PDF ou mettez à jour la constante `TEAM_TO_ANALYZE` dans le code."
            )
            return 
        
        # --- FIN DE LA LOGIQUE D'IDENTIFICATION ---
        
        # 2. Scoreboard (Utilise les noms définis)
        # Note : Le calcul h_wins/a_wins est basé sur le mapping du PDF, ce qui peut être incorrect 
        # si le PDF ne contient pas de données de score. On simplifie en affichant les noms.
        h_wins = sum(1 for s in scores if isinstance(s, dict) and s.get('Home', 0) > s.get('Away', 0))
        a_wins = sum(1 for s in scores if isinstance(s, dict) and s.get('Away', 0) > s.get('Home', 0))
        
        c1, c2, c3 = st.columns([2, 1, 2])
        c1.metric(t_analysed, h_wins)
        c3.metric(t_adverse, a_wins)
        c2.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{h_wins} - {a_wins}</h1>", unsafe_allow_html=True)
        st.markdown("---")

        # 3. Génération et affichage des tableaux d'analyse
        
        # L'équipe analysée (Lescar) est toujours t_home logique, l'adversaire est t_away logique
        df_by_set, df_global = generate_volleyball_analysis(t_analysed, t_adverse)
        
        st.subheader(f"Simulations des Rotations et Substitutions ({t_analysed} vs {t_adverse})")
        
        st.info(
f"""
**Explications (Équipe analysée : {t_analysed}) :**

- **Pos I à VI :** Numéro de joueur dans la position de rotation pour l'équipe {t_analysed} (I est le serveur).


[Image of volleyball court positions and rotation]

- **Service :** **S** ({t_analysed} sert) ou **R** ({t_adverse} sert / {t_analysed} reçoit).
- **Changement :** Substitution effectuée au score du rallye (Entrant/Sortant).
"""
        )
        
        # Affichage des tableaux par Set
        set_keys = sorted(list(df_by_set.keys()))
        
        for set_num in set_keys:
            st.header(f"Set {set_num}")
            st.dataframe(df_by_set[set_num], use_container_width=True)
            st.markdown("---")  

        # 4. Bouton de téléchargement CSV
        st.header("Téléchargement des Données")

        csv_file = df_global.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="⬇️ Télécharger TOUTES les Données d'Analyse (CSV)",
            data=csv_file,
            file_name=f'analyse_rotations_{t_analysed}_vs_{t_adverse}.csv',
            mime='text/csv',
        )

    else:
        # Contenu affiché si AUCUN fichier n'est encore uploadé
        st.info(f"Veuillez importer un fichier PDF de feuille de match. L'analyse des rotations sera automatiquement focalisée sur l'équipe **{TEAM_TO_ANALYZE}**.")

if __name__ == "__main__":
    main()
