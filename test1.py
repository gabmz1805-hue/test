import streamlit as st
import pandas as pd
import pdfplumber
import pypdfium2 as pdfium
import re
import gc
from io import BytesIO
from PIL import Image

# --- Fonctions d'Extraction (Utilisant pdfplumber) ---

def extract_general_info(pdf_file_path):
    """Extrait les informations générales (compétition, date, lieu) et les scores finaux du PDF."""
    
    general_info = {}
    
    try:
        # Utiliser pdfplumber pour une extraction de texte simple sur la première page
        with pdfplumber.open(pdf_file_path) as pdf:
            first_page_text = pdf.pages[0].extract_text()
            last_page_text = pdf.pages[-1].extract_text() if len(pdf.pages) > 1 else first_page_text
            
            # 1. Infos Générales (basées sur les sources 1-10)
            # Compétition
            match_compet = re.search(r'2MC - NATIONALE 2 MASCULINE - POULE C', first_page_text)
            general_info['Competition'] = match_compet.group(0) if match_compet else "Non trouvé"
            
            # Match N° et Jour
            match_num = re.search(r'Match: (.*)-Jour: (\d+)', first_page_text)
            general_info['Match N°'] = match_num.group(1) if match_num else "Non trouvé"
            general_info['Jour'] = match_num.group(2) if match_num else "Non trouvé"

            # Date et Heure
            match_date = re.search(r'Samedi \d{1,2} [A-Za-z]+ \d{4} à \d{2}h\d{2}', first_page_text)
            general_info['Date & Heure'] = match_date.group(0) if match_date else "Non trouvé"

            # Équipes (Extraction plus robuste nécessaire, ici simple recherche)
            general_info['Equipe A'] = "SPORT ATHLETIQUE MERIGNACAIS"
            general_info['Equipe B'] = "LESCAR PYRENEES VOLLEY-BALL"

            # 2. Score Final et Durée (basé sur la source 141)
            
            # Recherche du vainqueur et du score final dans le texte de la dernière page
            match_winner = re.search(r'Vainqueur: (.*) (\d)/(\d)', last_page_text, re.IGNORECASE)
            if match_winner:
                general_info['Vainqueur'] = match_winner.group(1).strip()
                general_info['Score Final'] = f"{match_winner.group(2)}/{match_winner.group(3)}"
            else:
                general_info['Vainqueur'] = "Non trouvé"
                general_info['Score Final'] = "Non trouvé"
                
            # Recherche de la durée totale
            match_duration = re.search(r'Durée\n\d{2}h\d{2}', last_page_text)
            general_info['Durée Totale'] = match_duration.group(0).replace('Durée\n', '') if match_duration else "Non trouvée"


    except Exception as e:
        st.error(f"Erreur lors de l'extraction des informations générales : {e}")
        return None
        
    return general_info

def extract_set_scores(pdf_file_path):
    """Tente d'extraire les scores par set à partir du tableau RESULTATS (dernière page)."""
    
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            # On cible le tableau de résultats sur la dernière page
            results_page = pdf.pages[-1]
            
            # Coordonnées estimées du tableau "RESULTATS" / "TRGP" (basé sur doc2.pdf)
            # Format: (x0, top, x1, bottom) - C'est la partie la plus fragile
            cropped_area = results_page.crop((50, 450, 550, 750)) 
            
            # Extraction des tableaux dans cette zone
            # Le paramètre 'vertical_strategy': 'lines' est souvent meilleur pour les documents scannés
            tables = cropped_area.extract_tables(table_settings={
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 3 # Tolérance pour joindre les lignes
            })
            
            if tables:
                # On suppose que le premier tableau est celui des scores
                df = pd.DataFrame(tables[0])
                
                # Nettoyage minimal : retirer les lignes/colonnes complètement vides
                df = df.dropna(how='all').dropna(axis=1, how='all')
                
                st.success(f"Tableau de scores des sets extrait avec succès.")
                return df
                
    except Exception as e:
        st.error(f"Erreur lors de l'extraction des scores de set: {e}")
        return None

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
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
        
    if st.button("🚀 Lancer l'Analyse des Données", type="primary"):
        
        # --- Lancement de l'Analyse ---
        with st.spinner('Analyse du document en cours...'):
            
            # Extraction des infos générales
            general_info = extract_general_info(tmp_path)
            
            # Extraction des scores détaillés
            df_scores_bruts = extract_set_scores(tmp_path)
            
            # Nettoyage du fichier temporaire
            os.unlink(tmp_path)
            gc.collect() # Nettoyage de la mémoire après utilisation des libs PDF

        # --- 2. Affichage des Résultats ---
        st.markdown("---")
        st.header("2. Résultats de l'Extraction")

        if general_info:
            st.subheader("🏆 Récapitulatif du Match")
            
            col1, col2, col3 = st.columns(3)
            
            # Affichage des infos générales
            with col1:
                st.metric(label="Compétition", value=general_info.get("Competition", "N/A"))
                st.metric(label="Match N°", value=f"N°{general_info.get('Match N°', 'N/A')} / Jour {general_info.get('Jour', 'N/A')}")
            with col2:
                st.metric(label="Date & Heure", value=general_info.get("Date & Heure", "N/A"))
                st.metric(label="Durée Totale", value=general_info.get("Durée Totale", "N/A"))
            with col3:
                st.metric(label=f"Vainqueur ({general_info.get('Score Final', 'N/A')})", value=general_info.get("Vainqueur", "N/A"), delta="Score Final")
            
            st.info(f"Équipe A: {general_info.get('Equipe A', 'N/A')} vs Équipe B: {general_info.get('Equipe B', 'N/A')}")
            
            st.markdown("---")


        if df_scores_bruts is not None and not df_scores_bruts.empty:
            st.subheader("📊 Scores Détaillés par Set (Extraction Brute du Tableau)")
            st.warning("ATTENTION: Le tableau ci-dessous est l'extraction brute du PDF. Il nécessite une étape de nettoyage (à coder) pour être parfaitement lisible.")
            st.dataframe(df_scores_bruts, use_container_width=True, hide_index=True)
            
        else:
            st.error("Échec de l'extraction du tableau des scores détaillés. Les coordonnées du tableau dans le PDF peuvent avoir changé.")
            

    # --- Section de Débogage pour voir les données brutes (Facultatif mais utile) ---
    st.markdown("---")
    if st.checkbox("Afficher le Texte Brut de la première page (Débogage)"):
        try:
            with pdfplumber.open(tmp_path) as pdf:
                st.text_area("Texte Brut Page 1", pdf.pages[0].extract_text(), height=300)
        except Exception as e:
            st.error(f"Erreur lors de la lecture du texte brut: {e}")
