import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="VolleyStats Rotations", page_icon="📊", layout="wide")

# ==========================================
# 1. LOGIQUE DE ROTATION ET DE SUBSTITUTION (Vos fonctions - Aucune modification)
# ==========================================

def rotate_positions(positions):
    """
    Effectue une rotation horaire des joueurs pour l'équipe (Lescar dans cet exemple).
    [I, II, III, IV, V, VI] -> [VI, I, II, III, IV, V] (sens horaire)
    """
    return positions[-1:] + positions[:-1]

def apply_substitutions(positions, lescar_score, merignac_score, subs_data):
    """
    Applique les substitutions de joueurs à la formation au score donné.
    """
    change_string = ""
    updated_positions = list(positions)
    
    # Le format des substitutions est: {score_merignac: {score_lescar: [(entré, sorti), ...]}}
    if merignac_score in subs_data and lescar_score in subs_data[merignac_score]:
        substitutions = subs_data[merignac_score][lescar_score]
        
        for player_in, player_out in substitutions:
            try:
                # 1. Trouver l'index de la position du joueur sortant
                idx_out = updated_positions.index(player_out)
                
                # 2. Remplacer le joueur sortant par le joueur entrant
                updated_positions[idx_out] = player_in
                
                # 3. Mettre à jour la chaîne de changement (gère les substitutions multiples)
                if change_string:
                    change_string += ", "
                change_string += f"#{player_in}/#{player_out}"
                
            except ValueError:
                pass
                
    return updated_positions, change_string

def analyze_set(set_num, initial_formation, initial_service, substitutions_data, rally_outcomes):
    """
    Simule un set rallye par rallye et génère le tableau d'analyse.
    """
    
    lescar_pts = 0
    merignac_pts = 0
    service_state = 'S' if initial_service == 'B' else 'R' # 'S' pour Lescar (Serve), 'R' pour Récéption (Mérignac sert)
    current_positions = list(initial_formation)
    results = []

    # En-têtes du tableau
    header = ['Rallye', 'Merignac pts', 'Lescar pts', 'Score L', 'Score M', 
              'Pos I (RD)', 'Pos II (AD)', 'Pos III (AC)', 'Pos IV (AG)', 
              'Pos V (AR)', 'Pos VI (RC)', 'Service', 'Gagnant', 'Changement']

    # Ligne de départ (score 0-0)
    start_row = [
        0, '', '', 0, 0, # Scores
        *current_positions, # Positions I à VI
        service_state, 'Début', '' # S/R, Success, Changement
    ]
    results.append(start_row)

    # Simulation des rallyes
    for rally_idx, rally_outcome in enumerate(rally_outcomes):
        rally_num = rally_idx + 1
        
        # 1. LOGIQUE DE ROTATION : Lescar tourne SEULEMENT si R -> S
        should_rotate = (service_state == 'R' and rally_outcome == 1)
        if should_rotate:
            current_positions = rotate_positions(current_positions)
        
        prev_service_state = service_state
        current_change_string = ""
        
        if rally_outcome == 1: # Lescar gagne le rallye
            lescar_pts += 1
            if prev_service_state == 'R':
                service_state = 'S' # Changement de service: R -> S (Lescar prend le service)
            
            # Application des substitutions
            current_positions, current_change_string = apply_substitutions(
                current_positions, lescar_pts, merignac_pts, substitutions_data
            )
            
        else: # Mérignac gagne le rallye (rally_outcome == 0)
            merignac_pts += 1
            if prev_service_state == 'S':
                service_state = 'R' # Changement de service: S -> R (Mérignac prend le service)
            
            # Application des substitutions (même si c'est le score adverse qui a bougé)
            current_positions, current_change_string = apply_substitutions(
                current_positions, lescar_pts, merignac_pts, substitutions_data
            )
        
        # 2. Enregistrement de la ligne de résultat
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
        
        # 3. Condition d'arrêt du set
        if (lescar_pts >= 25 and lescar_pts - merignac_pts >= 2) or \
           (merignac_pts >= 25 and merignac_pts - lescar_pts >= 2) or \
           (set_num == 5 and (lescar_pts >= 15 or merignac_pts >= 15) and abs(lescar_pts - merignac_pts) >= 2):
            break
            
    return header, results

def generate_volleyball_analysis():
    """
    Simule tous les sets, crée un DataFrame par set, et retourne une liste de ces DataFrames, 
    ainsi que le DataFrame global pour l'exportation.
    """
    game_data = {
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
        
        # Préparer le DataFrame global pour l'exportation
        for row in results:
            row_with_set = [set_num] + row
            all_results_global.append(row_with_set)
    
    global_header = ['Set'] + header
    df_global = pd.DataFrame(all_results_global, columns=global_header)
    
    return df_by_set, df_global

# ==========================================
# 2. MAIN APP STREAMLIT (Interface) - Modifiée pour boucler
# ==========================================

def main():
    st.title("📊 Analyse Détaillée des Rotations et Substitutions")
    st.markdown("---")

    # Générer les tableaux de données
    df_by_set, df_global = generate_volleyball_analysis()

    st.subheader("Simulations des Rotations et Substitutions (Lescar)")
    st.info("**Explications :**\n\n- **Pos I à VI :** Numéro de joueur dans la position de rotation (I est le serveur). 

[Image of volleyball rotation diagram]
\n- **Service :** **S** (Lescar sert) ou **R** (Mérignac sert/Lescar reçoit).\n- **Changement :** Substitution effectuée au score du rallye (Entrant/Sortant).")
    
    # --- Affichage d'un tableau pour chaque Set ---
    set_keys = list(df_by_set.keys())
    
    for set_num in set_keys:
        st.header(f"Set {set_num}")
        st.dataframe(df_by_set[set_num], use_container_width=True)
        st.markdown("---") # Séparateur entre les sets

    # --- Bouton de téléchargement (utilise le DataFrame global) ---
    st.header("Téléchargement")

    # Conversion du DataFrame global en CSV pour le bouton de téléchargement
    csv_file = df_global.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="⬇️ Télécharger TOUTES les Données d'Analyse (CSV)",
        data=csv_file,
        file_name='analyse_rotations_volleyball_complete.csv',
        mime='text/csv',
    )

if __name__ == "__main__":
    main()
