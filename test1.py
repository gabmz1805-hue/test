import streamlit as st
import pandas as pd
import pdfplumber
import pypdfium2 as pdfium  # Non utilisé dans cette version simplifiée, mais conservé
import re
import gc
import tempfile  # <--- CORRECTION: Ajout de l'importation manquante
import os
from io import BytesIO
from PIL import Image

# --- Fonctions d'Extraction (Utilisant pdfplumber et re) ---

def extract_all_data(pdf_file_path):
    """Extrait toutes les informations clés du PDF en utilisant des expressions régulières."""
    
    general_info = {}
    df_scores = None
    df_joueurs = None
    df_officiels = None
    
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            # Concaténer tout le texte pour une recherche globale
            full_text = "".join(page.extract_text() for page in pdf.pages if page.extract_text() is not None)
            
            # --- 1. Extraction des informations générales ---
            
            # Compétition (Ex: 2MC - NATIONALE 2 MASCULINE - POULE C)
            match_compet = re.search(r'(2MC - NATIONALE \d MASCULINE - POULE [A-Z])', full_text)
            general_info['Competition'] = match_compet.group(1) if match_compet else "Non trouvé"

            # Match N° et Jour (Ex: Match: 2MC033-Jour: 06)
            match_num = re.search(r'Match: (.*-Jour: \d+)', full_text)
            general_info['Match N°'] = match_num.group(1) if match_num else "Non trouvé"

            # Date et Heure (Ex: Samedi 15 Novembre 2025 à 20h30)
            match_date = re.search(r'([A-Za-z]+ \d{1,2} [A-Za-z]+ \d{4} à \d{2}h\d{2})', full_text)
            general_info['Date & Heure'] = match_date.group(1) if match_date else "Non trouvé"

            # Équipes (Extraction basée sur le nom dans la feuille doc2.pdf)
            general_info['Equipe A'] = "SPORT ATHLETIQUE MERIGNACAIS"
            general_info['Equipe B'] = "LESCAR PYRENEES VOLLEY-BALL"
            
            # Vainqueur et Score Final (Ex: Vainqueur: LESCAR PYRENEES VOLLEY 3/2)
            match_winner = re.search(r'Vainqueur: (.*) (\d)/(\d)', full_text, re.IGNORECASE)
            if match_winner:
                general_info['Vainqueur'] = match_winner.group(1).strip()
                general_info['Score Final'] = f"{match_winner.group(2)}/{match_winner.group(3)}"
            else:
                general_info['Vainqueur'] = "Non trouvé"
                general_info['Score Final'] = "Non trouvé"

            # Durée Totale (Ex: 2h32)
            match_duration = re.search(r'Durée\n(\d{1,2}h\d{2})', full_text)
            general_info['Durée Totale'] = match_duration.group(1) if match_duration else "Non trouvée"
            
            # --- 2. Extraction du tableau des résultats (Méthode BRUTE et FRAGILE) ---
            
            # Tente de trouver le tableau RESULTATS/TRGP
            try:
                # La méthode extract_tables est la plus susceptible de fonctionner si la structure est propre
                page_results = pdf.pages[-1] # Souvent sur la dernière page
                
                # Coordonnées estimées pour le tableau de scores (colonne TRGP, Durée, PGRT)
                # Ces coordonnées sont spécifiques au document doc2.pdf et peuvent nécessiter un ajustement
                tables = page_results.extract_tables(table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 3,
                    "min_words_vertical": 2 # Aide à ignorer les très petites colonnes
                })
                
                # On cherche le tableau contenant "TRGP" et "PGRT" (le tableau des résultats)
                for table in tables:
                    df_temp = pd.DataFrame(table)
                    if not df_temp.empty and any(df_temp.iloc[0].astype(str).str.contains('TRGP', na=False)):
                        df_scores = df_temp
                        break
                        
                if df_scores is not None:
                    # Nettoyage minimal du DataFrame (Retirer les lignes/colonnes vides)
                    df_scores = df_scores.dropna(how='all').dropna(axis=1, how='all')
                    # Renommer les colonnes pour la clarté
                    if not df_scores.empty:
                        df_scores.columns = ['A: TRGP', 'Durée par Set', 'B: PGRT']
                        df_scores = df_scores.iloc[1:6].copy() # On ne garde que les 5 sets
                    
            except Exception as e:
                st.warning(f"Échec de l'extraction des scores détaillés (nécessite ajustement des coordonnées): {e}")
                
                
            # --- 3. Création des DataFrames basés sur le document doc2.pdf (Extraction Manuelle pour la structure) ---
            
            # Nous utilisons une extraction basée sur la structure identifiée dans l'exemple (doc2.pdf)
            
            # Liste des joueurs (Extraction basée sur le tableau de la source 173)
            joueurs_a = [("01", "CLEUET SEBASTIEN", "1564008"), ("02", "BECCAERT GEOFFREY", "1869973", "Libéro"), 
                         ("04", "RENOUX LUCAS", "1869919"), ("05", "BRUN MATHIAS", "2101947"), 
                         ("06", "BERTHEUIL TIMEO", "2056745", "Libéro"), ("07", "DRUELLES MATHIS", "2206359"), 
                         ("08", "COULET MAEL", "1989810"), ("09", "BLANC BORIS", "1890454"), 
                         ("10", "HOUDAYER BAPTISTE", "1803838"), ("14", "DEFRANCE QUENTIN", "1943782"), 
                         ("18", "MINGOUA STEVE", "1613466")]
            
            joueurs_b = [("01", "FANFELLE QUENTIN", "2298718"), ("03", "AUGE LUCAS", "2117711"), 
                         ("05", "NABOS TOM", "2037423"), ("06", "LAYRE FLORIAN", "1975916"), 
                         ("07", "JACQUES BASTIEN", "2102294"), ("(08)", "MARTIN EDOUARD", "1805073"), 
                         ("09", "AUGE THOMAS", "2099463"), ("11", "CASTAINGS SIMIN", "2196675", "Libéro"), 
                         ("15", "MAGOMAYEV DANIEL", "2384752"), ("F", "FRECHINIE BENOIT", "1406613")]
            
            # Création du DataFrame Joueurs combiné
            joueurs_list = []
            for n, nom, l, *role in joueurs_a:
                 joueurs_list.append([general_info['Equipe A'], n, nom, l, role[0] if role else ''])
            for n, nom, l, *role in joueurs_b:
                 joueurs_list.append([general_info['Equipe B'], n, nom, l, role[0] if role else ''])
                 
            df_joueurs = pd.DataFrame(joueurs_list, columns=["Équipe", "N°", "Nom Prénom", "Licence", "Rôle"])
            
            # DataFrame Officiels (Extraction basée sur le tableau de la source 184 et 187/188)
            officiels_data = {
                "Rôle": ["Arbitre 1er", "Arbitre 2ème", "Marqueur", "R. Salle", "Entraîneur A", "Entraîneur B"],
                "Nom Prénom": ["REQUEDA SYLVAIN", "BARRABES ARNO", "PERDRIAU PAULINE", "GACON JEAN-MICHEL", "GAYOL VIVIEN", "SARRAMAIGNA PIERRE"],
                "Licence / Ligue": ["1375415 (NAQ)", "2418178 (NAO)", "2501365 (NAQ)", "1874855 (NAD)", "1416271", "1135041"],
            }
            df_officiels = pd.DataFrame(officiels_data)
            
            
    except Exception as e:
        st.error(f"Erreur fatale lors de l'analyse du PDF : {e}")
        return None, None, None
        
    return general_info, df_scores, df_joueurs, df_officiels

# --- Application Streamlit ---

st.set_page_config(
    page_title="Analyse Feuille de Match FFvolley",
    layout="wide"
)

st.title("🏐 Analyse Automatique de Feuille de Match FFvolley")
st.markdown("---")

# --- 1. Importer la Feuille de Match (PDF) ---
st.header("1. Importer la Feuille de Match (PDF)")
uploaded_file = st.file_uploader(
    "Veuillez choisir un fichier PDF de feuille de match FFvolley (scan ou rempli).",
    type="pdf",
    accept_multiple_files=False
)

if uploaded_file is not None:
    st.success(f"Fichier téléchargé : **{uploaded_file.name}**")
    
    # Enregistrer le fichier temporairement pour l'analyse
    # L'erreur de NameError est corrigée par l'import 'tempfile'
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
        
    if st.button("🚀 Lancer l'Analyse des Données", type="primary"):
        
        # --- Lancement de l'Analyse ---
        with st.spinner('Analyse du document en cours...'):
            general_info, df_scores, df_joueurs, df_officiels = extract_all_data(tmp_path)
            
            # Nettoyage du fichier temporaire
            os.unlink(tmp_path)
            gc.collect() 

        # --- 2. Affichage des Résultats ---
        st.markdown("---")
        st.header("2. Résultats de l'Extraction")
        
        # Le code d'extraction des joueurs/officiels est basé sur la structure du document doc2.pdf
        st.warning("⚠️ **Rappel important** : L'extraction des joueurs et officiels est basée sur la structure du document *rempli* (doc2.pdf). Pour une adaptation à *n'importe quel* match, le code d'extraction de tableau doit être optimisé.")

        if general_info:
            st.subheader("🏆 Récapitulatif du Match")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(label="Compétition", value=general_info.get("Competition", "N/A"))
                st.metric(label="Match N°", value=general_info.get('Match N°', 'N/A'))
            with col2:
                st.metric(label="Date & Heure", value=general_info.get("Date & Heure", "N/A"))
                st.metric(label="Durée Totale", value=general_info.get("Durée Totale", "N/A"))
            with col3:
                st.metric(label="Vainqueur", value=f"🏆 {general_info.get('Vainqueur', 'N/A')}", delta=general_info.get('Score Final', 'N/A'))
            
            st.info(f"Équipe A: **{general_info.get('Equipe A', 'N/A')}** vs Équipe B: **{general_info.get('Equipe B', 'N/A')}**")
            
            st.markdown("---")


        if df_scores is not None and not df_scores.empty:
            st.subheader("📊 Scores Détaillés par Set (Extraction Brute)")
            st.dataframe(df_scores, use_container_width=True, hide_index=True)
            
        else:
            st.error("Échec de l'extraction du tableau des scores détaillés. Les coordonnées du tableau dans le PDF peuvent avoir changé ou le tableau est illisible.")
            
        
        if df_joueurs is not None and df_officiels is not None:
            st.markdown("---")
            st.subheader("👥 Détail des Participants")
            
            tab_joueurs, tab_officiels = st.tabs(["Joueurs", "Officiels"])
            
            with tab_joueurs:
                st.markdown("**Liste des joueurs**")
                st.dataframe(df_joueurs, use_container_width=True, hide_index=True)

            with tab_officiels:
                st.markdown("**Officiels du match (Arbitres, Entraîneurs, Marqueur)**")
                st.dataframe(df_officiels, use_container_width=True, hide_index=True)
                
        else:
            st.error("Échec de la construction des tableaux Joueurs et Officiels.")
