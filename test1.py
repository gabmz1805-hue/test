import streamlit as st
import camelot
import pandas as pd
import re
import tempfile
import os

# --- Fonctions d'extraction robustes ---

def clean_text(text):
    """Nettoie le texte en retirant les sauts de ligne et l'espace excessif."""
    if pd.isna(text):
        return ""
    # Remplacement des multiples espaces par un seul et suppression des retours à la ligne
    text = str(text).replace('\n', ' ').strip()
    return re.sub(r'\s+', ' ', text)

def find_and_clean_table(tables, content_keyword, content_keyword_2=None):
    """
    Recherche un DataFrame contenant un ou deux mots-clés spécifiques.
    
    Args:
        tables (list): Liste des objets Table de Camelot.
        content_keyword (str): Premier mot-clé pour identifier le tableau (ex: 'Vainqueur').
        content_keyword_2 (str, optional): Second mot-clé pour affiner.

    Returns:
        pd.DataFrame: Le DataFrame nettoyé ou un DataFrame vide.
    """
    for table in tables:
        df = table.df
        df_string = df.to_string()
        
        # Condition 1: Le premier mot-clé est présent
        if content_keyword in df_string:
            # Condition 2: Si un second mot-clé est fourni, il doit aussi être présent
            if content_keyword_2 is None or content_keyword_2 in df_string:
                # Appliquer la fonction de nettoyage à toutes les cellules
                df = df.applymap(clean_text)
                return df
            
    return pd.DataFrame() # Retourne vide si non trouvé


def extract_results_summary(tables):
    """Extrait le tableau des RESULTATS et les données de score/durée."""
    results_df_raw = find_and_clean_table(tables, 'Vainqueur')
    
    final_result, start_time, end_time, total_duration, sets_data = "Non trouvé", "Non trouvé", "Non trouvé", "Non trouvé", []
    
    if results_df_raw.empty:
        return final_result, start_time, end_time, total_duration, pd.DataFrame(sets_data)

    try:
        # Tenter d'extraire les infos de la dernière ligne (Vainqueur)
        winner_row = results_df_raw[results_df_raw.iloc[:, -1].str.contains('Vainqueur', na=False, case=False)]
        if not winner_row.empty:
             # On prend la dernière colonne (ou l'avant-dernière) et on nettoie pour le score final
            final_result = clean_text(winner_row.iloc[0, -2] + winner_row.iloc[0, -1])
            final_result = final_result.replace("Vainqueur:", "").strip()

        # Tenter d'extraire les heures (en bas du tableau RESULTATS)
        time_row = results_df_raw[results_df_raw.iloc[:, 0].str.contains('Debut', na=False, case=False)]
        if not time_row.empty:
            row = time_row.iloc[0]
            # Assumer les colonnes 0, 1, 2 contiennent Début, Fin, Durée
            start_time = row.iloc[0].replace('Debut', '').strip()
            end_time = row.iloc[1].replace('Fin', '').strip()
            total_duration = row.iloc[2].replace('Durée', '').strip()
        
        # Tenter d'extraire les scores par set
        # On cherche le tableau des résultats détaillés par set (colonnes TRGP, Durée, PGRT)
        
        # Filtrer les lignes qui contiennent 'TRGP' (Tours Reçus Gagnés Perdus) pour définir le haut du tableau
        start_index = results_df_raw[results_df_raw.iloc[:, 0].str.contains('TRGP', na=False)].index.max()
        
        if start_index is not None:
            # Les lignes de scores sont juste après
            score_rows = results_df_raw.iloc[start_index+1:]
            
            for i, row in score_rows.iterrows():
                # Le tableau est généralement structuré comme: Col A (Points), Col B (Score A, Durée, Set), Col C (Points B)
                try:
                    set_num = None
                    duration = None
                    score_a = None
                    score_b = None
                    
                    # On cherche le numéro de set et la durée dans la colonne centrale (index 1)
                    col_b_parts = row.iloc[1].split()
                    for part in col_b_parts:
                        if "'" in part:
                            duration = part
                        if part.isdigit() and len(part) < 2 and int(part) in [1, 2, 3, 4, 5]:
                            set_num = int(part)
                            
                    # Si on a le numéro de set et la durée, on peut essayer d'extraire les scores
                    if set_num and duration:
                        # Le score A est la valeur numérique la plus claire dans la colonne A
                        match_a = re.search(r'\d+', row.iloc[0])
                        if match_a: score_a = int(match_a.group(0))

                        # Le score B est la valeur numérique la plus claire dans la colonne C
                        match_b = re.search(r'\d+', row.iloc[2])
                        if match_b: score_b = int(match_b.group(0))
                        
                        if score_a is not None and score_b is not None:
                             sets_data.append({
                                'Set': set_num, 
                                'Score': f"{score_a}-{score_b}", 
                                'Durée': duration
                            })
                            
                except IndexError:
                    # Fin du tableau
                    continue
        
    except Exception as e:
        st.warning(f"Avertissement lors de l'extraction des résultats : {e}")

    sets_df = pd.DataFrame(sets_data).sort_values('Set').reset_index(drop=True)
    return final_result, start_time, end_time, total_duration, sets_df


def extract_players_data(tables):
    """Extrait le tableau des joueurs (Nom, Prénom, Licence, Numéro)."""
    # Recherche du tableau qui contient les mots-clés 'Nom Prénom' et 'Licence' (partie basse du PDF)
    players_df_raw = find_and_clean_table(tables, 'Nom Prénom', 'Licence')
    players_df_clean = pd.DataFrame()
    
    if players_df_raw.empty:
        return players_df_clean

    try:
        # La structure est typiquement: Col 0(N° A), Col 1(Nom Prénom A), Col 2(Licence A), Col 3(N° B), Col 4(Nom Prénom B), Col 5(Licence B)
        # On va chercher les colonnes clés (index 0 à 5)
        raw_data = players_df_raw.iloc[1:].iloc[:, 0:6].reset_index(drop=True)
        players_data = []
        
        # Extraire les noms des équipes de la ligne d'en-tête (une ligne au-dessus des joueurs)
        team_a_name = clean_text(players_df_raw.iloc[0, 1]) if players_df_raw.shape[1] > 1 else "Équipe A"
        team_b_name = clean_text(players_df_raw.iloc[0, 4]) if players_df_raw.shape[1] > 4 else "Équipe B"
        
        for index, row in raw_data.iterrows():
            # Équipe A (vérifier si le numéro de joueur est présent)
            if row.iloc[0].strip():
                players_data.append({
                    'Équipe': team_a_name,
                    'N°': row.iloc[0],
                    'Nom Prénom': row.iloc[1],
                    'Licence': row.iloc[2]
                })
            # Équipe B
            if row.iloc[3].strip():
                players_data.append({
                    'Équipe': team_b_name,
                    'N°': row.iloc[3],
                    'Nom Prénom': row.iloc[4],
                    'Licence': row.iloc[5]
                })
                
        # On enlève les lignes vides ou de 'LIBEROS'
        players_df_clean = pd.DataFrame(players_data)
        players_df_clean = players_df_clean[~players_df_clean['Nom Prénom'].str.contains('LIBEROS', na=False)]
        players_df_clean = players_df_clean[players_df_clean['Nom Prénom'] != '']
        
    except Exception as e:
        st.warning(f"Avertissement lors du nettoyage des joueurs : {e}")
        
    return players_df_clean


def extract_officials_data(tables):
    """Extrait le tableau des officiels (Arbitres, Marqueur, etc.)."""
    # Recherche du tableau qui contient les mots-clés 'Arbitres' et 'Signature'
    officials_df_raw = find_and_clean_table(tables, 'Arbitres', 'Signature')
    officials_df_clean = pd.DataFrame()
    
    if officials_df_raw.empty:
        return officials_df_clean
    
    try:
        # On cherche le bloc Officiels dans les premières colonnes (Fonction / Nom Prénom / Licence)
        
        # Identification des lignes pertinentes (Arbitres, Marqueur, R.Salle)
        relevant_rows = officials_df_raw[officials_df_raw.iloc[:, 0].str.contains('Arbitres|Marqueur|R.Salle', na=False)].iloc[:, 0:3]
        
        if not relevant_rows.empty:
            officials_data = []
            for i, row in relevant_rows.iterrows():
                # La colonne 0 est la fonction (Ter, 2ème, Marqueur)
                function = row.iloc[0]
                # La colonne 1 est le nom/prénom
                name = row.iloc[1]
                # La colonne 2 est la Ligue/Licence
                license_info = row.iloc[2]
                
                # Nettoyage des libellés de fonction/nom
                function = function.replace('Arbitres', '').strip()
                
                officials_data.append({
                    'Fonction': function,
                    'Nom Prénom': name,
                    'Licence': license_info
                })
            
            officials_df_clean = pd.DataFrame(officials_data)
            officials_df_clean = officials_df_clean[officials_df_clean['Nom Prénom'] != '']
            
    except Exception as e:
        st.warning(f"Avertissement lors de l'extraction des officiels : {e}")

    return officials_df_clean


def extract_match_data(file_path):
    """Fonction principale pour lire le PDF et extraire tous les blocs."""
    
    st.info("Démarrage de l'extraction des tableaux (peut prendre quelques secondes)...")
    
    # 1. Lecture de tous les tableaux (méthode STREAM pour les tableaux complexes)
    try:
        tables = camelot.read_pdf(
            file_path, 
            pages='all',
            flavor='stream', 
            edge_tol=500, # Tolérance d'alignement pour aider à la reconnaissance
            row_tol=10
        )
        if not tables:
            st.error("Aucun tableau n'a été détecté par Camelot. Le PDF est peut-être scanné ou dans un format inconnu.")
            return None
            
        st.success(f"{len(tables)} tableaux détectés sur le document.")
            
    except Exception as e:
        st.error(f"Erreur critique lors de la lecture du PDF : {e}")
        return None

    # 2. Extraction des différents blocs
    final_result, start_time, end_time, total_duration, sets_df = extract_results_summary(tables)
    players_df = extract_players_data(tables)
    officials_df = extract_officials_data(tables)
    
    return {
        'resultat_final': final_result,
        'heure_debut': start_time,
        'heure_fin': end_time,
        'duree_totale': total_duration,
        'sets': sets_df,
        'joueurs': players_df,
        'officiels': officials_df,
    }

# --- Application Streamlit ---

st.set_page_config(
    page_title="Extracteur de Feuilles de Match Volley (FFvolley)", 
    layout="wide"
)

st.title("🏐 Extracteur de Données FFvolley")
st.markdown("Téléversez une feuille de match FFvolley (PDF) pour extraire automatiquement les résultats, la liste des joueurs et les officiels.")

# Zone de téléversement
uploaded_file = st.file_uploader(
    "Veuillez choisir votre fichier PDF de feuille de match.", 
    type=["pdf"]
)

if uploaded_file is not None:
    # 1. Sauvegarder le fichier temporairement
    # Streamlit gère le fichier en mémoire. Camelot a besoin d'un chemin sur le disque.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # 2. Exécuter l'extraction
        data = extract_match_data(tmp_path)

        if data:
            st.header("✅ Données Extraites avec Succès")
            
            # Affichage des Résultats
            st.subheader("1. Résumé du Match")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Vainqueur / Score", data['resultat_final'])
            col2.metric("Début du match", data['heure_debut'])
            col3.metric("Fin du match", data['heure_fin'])
            col4.metric("Durée Totale", data['duree_totale'])

            # Affichage des Sets
            if not data['sets'].empty:
                st.subheader("2. Scores Détaillés par Set")
                st.dataframe(data['sets'], use_container_width=True, hide_index=True)
            else:
                st.warning("Avertissement : Les scores détaillés par set n'ont pas pu être extraits.")
            
            # Affichage des Joueurs
            if not data['joueurs'].empty:
                st.subheader("3. Liste des Joueurs")
                st.dataframe(data['joueurs'], use_container_width=True, hide_index=True)
                
                # Offrir l'option de téléchargement
                csv_data = data['joueurs'].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Télécharger la liste des joueurs (CSV)",
                    data=csv_data,
                    file_name='joueurs_volley_match.csv',
                    mime='text/csv',
                    key='download_players'
                )
            else:
                st.warning("Avertissement : La liste des joueurs n'a pas pu être extraite.")

            # Affichage des Officiels
            if not data['officiels'].empty:
                st.subheader("4. Officiels du Match")
                st.dataframe(data['officiels'], use_container_width=True, hide_index=True)
            else:
                st.warning("Avertissement : La liste des officiels n'a pas pu être extraite.")
            
    finally:
        # 3. Suppression du fichier temporaire après utilisation
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

st.sidebar.info("Application créée avec Python, Streamlit et la librairie Camelot (pour l'extraction PDF).")
