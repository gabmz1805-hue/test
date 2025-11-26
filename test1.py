import streamlit as st
import pandas as pd
import camelot
import tempfile
import os

# --- Fonctions d'Extraction (Utilisant Camelot) ---
def extract_data_from_pdf(pdf_path):
    """
    Tente d'extraire les informations clés des tableaux d'une feuille de match FFvolley.
    
    Les zones (pages et coordonnées) sont basées sur l'analyse de la structure du document fourni.
    ATTENTION : Les coordonnées peuvent varier légèrement entre les documents.
    """
    
    st.info("Tentative d'extraction des tableaux de scores, joueurs et officiels...")
    
    # Dictionnaire pour stocker les DataFrames extraits
    extracted_data = {}
    
    # 1. Extraction du Tableau des RÉSULTATS (Set par Set) - Page 1 dans votre exemple
    # Nous assumons qu'il s'agit du dernier tableau de la feuille de match standard.
    try:
        # Tente d'extraire le tableau des résultats (le dernier tableau de la feuille)
        # La table cible est le tableau RESULTATS/TRGP [cite: 141]
        tables_results = camelot.read_pdf(pdf_path, pages='all', flavor='stream', table_areas=['40,300,550,150'])
        
        if tables_results.n > 0:
            df_results = tables_results[0].df
            extracted_data['results'] = df_results
            st.success(f"Tableau de résultats (Set Scores) extrait : {len(df_results)} lignes")
        else:
            st.warning("Échec de l'extraction du tableau de résultats.")
            
    except Exception as e:
        st.error(f"Erreur lors de l'extraction des résultats : {e}")

    # 2. Extraction du Tableau des JOUEURS - Page 1
    # La table cible est le tableau A / B N Nom Prénom Licence [cite: 129]
    try:
        tables_players = camelot.read_pdf(pdf_path, pages='all', flavor='stream', table_areas=['30,700,550,300'])
        
        if tables_players.n > 0:
            df_players = tables_players[0].df
            extracted_data['players'] = df_players
            st.success(f"Tableau des joueurs (Licences) extrait : {len(df_players)} lignes")
        else:
            st.warning("Échec de l'extraction du tableau des joueurs.")
            
    except Exception as e:
        st.error(f"Erreur lors de l'extraction des joueurs : {e}")
        
    return extracted_data


# --- Application Streamlit ---

st.set_page_config(
    page_title="Analyse Automatique de Feuille de Match",
    layout="wide"
)

st.title("🏐 Analyse Automatique de Feuille de Match Volley-Ball")
st.markdown("---")

# --- 1. Importer la Feuille de Match (PDF) ---
st.header("1. Importer la Feuille de Match (PDF)")
uploaded_file = st.file_uploader(
    "Veuillez choisir un fichier PDF de feuille de match FFvolley.",
    type="pdf",
    accept_multiple_files=False
)

# --- 2. Lancement de l'Analyse ---
if uploaded_file is not None:
    st.success(f"Fichier téléchargé : **{uploaded_file.name}**")
    
    if st.button("🚀 Lancer l'Analyse des Données", type="primary"):
        
        # Enregistrer le fichier temporairement pour Camelot
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
            
        with st.spinner('Extraction des données des tableaux...'):
            extracted_data = extract_data_from_pdf(tmp_path)
        
        # Nettoyer le fichier temporaire
        os.unlink(tmp_path)
            
        # --- 3. Affichage des Résultats ---
        st.markdown("---")
        st.header("2. Résultats de l'Extraction")

        if 'results' in extracted_data:
            st.subheader("📊 Scores et Durées par Set (Extraction Brute)")
            st.dataframe(extracted_data['results'], use_container_width=True)
            st.caption("Ce tableau brut contient les informations de la section RESULTATS de la feuille[cite: 141].")

        if 'players' in extracted_data:
            st.subheader("👥 Joueurs et Licences (Extraction Brute)")
            st.dataframe(extracted_data['players'], use_container_width=True)
            st.caption("Ce tableau brut contient les informations de la section Joueurs/Licence de la feuille[cite: 129].")
        
        if not extracted_data:
            st.error("Aucune donnée n'a pu être extraite. Vérifiez que `camelot-py` et `ghostscript` sont correctement installés et que le format du PDF est clair.")
        
        st.markdown("---")
        st.info("PROCHAINE ÉTAPE: Le nettoyage et la mise en forme de ces DataFrames bruts pour afficher un récapitulatif clair (comme le vainqueur, le score final, etc.).")
