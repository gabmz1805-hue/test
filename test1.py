import streamlit as st
import pandas as pd

st.set_page_config(page_title="VolleyStats Rotations", page_icon="📊", layout="wide")

# ==========================================
# 0. DATA SOURCE
# ==========================================

def get_game_data():
    """Contient toutes les données d'entrée du match (formations, services, rallyes, subs)."""
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
# 1. LOGIQUE DE ROTATION ET DE SUBSTITUTION (Non modifiée)
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

    start_row = [
        0, '', '', 0, 0, 
        *current_positions, 
        service_state, 'Début', '' 
    ]
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
            if prev_service_state == 'R':
                service_state = 'S' 
            current_positions, current_change_string = apply_substitutions(
                current_positions, lescar_pts, merignac_pts, substitutions_data
            )
            
        else: 
            merignac_pts += 1
            if prev_service_state == 'S':
                service_state = 'R' 
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
    """Simule tous les sets et retourne les DataFrames."""
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
# 2. MAIN APP STREAMLIT (Interface)
# ==========================================

def main():
    st.title("📊 Analyse Détaillée des Rotations et Substitutions")
    
    # --- Barre latérale pour l'affichage des données d'entrée ---
    with st.sidebar:
        st.header("⚙️ Données d'Entrée")
        st.markdown(
            "Ces données sont codées en dur dans le script. "
            "Vous pouvez les vérifier ou les copier pour les modifier dans le code."
        )
        game_data = get_game_data()
        
        for set_num, data in game_data.items():
            with st.expander(f"Set {set_num}"):
                st.markdown(f"**Formation Initiale:** {data['initial_formation']}")
                st.markdown(f"**Service Initial:** {data['initial_service']}")
                st.markdown(f"**Substitutions:** `{data['substitutions']}`")
                st.markdown(f"**Rallyes (1=Lescar):** `{data['rally_outcomes']}`")
        
    st.markdown("---")

    df_by_set, df_global = generate_volleyball_analysis()

    st.subheader("Simulations des Rotations et Substitutions (Lescar)")
    st.info(
"""
**Explications :**

- **Pos I à VI :** Numéro de joueur dans la position de rotation (I est le serveur). 

[Image of volleyball rotation diagram]

- **Service :** **S** (Lescar sert) ou **R** (Mérignac sert/Lescar reçoit).
- **Changement :** Substitution effectuée au score du rallye (Entrant/Sortant).
"""
    )
    
    # --- Affichage d'un tableau pour chaque Set ---
    set_keys = sorted(list(df_by_set.keys()))
    
    for set_num in set_keys:
        st.header(f"Set {set_num}")
        st.dataframe(df_by_set[set_num], use_container_width=True)
        st.markdown("---") 

    # --- Bouton de téléchargement CSV ---
    st.header("Téléchargement")

    csv_file = df_global.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="⬇️ Télécharger TOUTES les Données d'Analyse (CSV)",
        data=csv_file,
        file_name='analyse_rotations_volleyball_complete.csv',
        mime='text/csv',
    )

if __name__ == "__main__":
    main()
