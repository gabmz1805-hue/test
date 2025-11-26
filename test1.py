import streamlit as st
import pandas as pd
from io import BytesIO

# --- IMPORTANT : Fonction de SIMULATION pour l'analyse PDF ---
# Cette fonction simule l'extraction de données. Dans un projet réel,
# elle serait remplacée par un moteur OCR/NLP complexe.
def simulate_match_analysis(uploaded_file):
    """Simule l'analyse de la feuille de match et retourne les données structurées."""
    
    # --- Données SIMULÉES (issues de l'exemple précédent) ---
    match_data = {
        "competition": "Simulé: NATIONALE 2 MASCULINE - POULE C",
        "match_n": "Simulé: 2MC033-Jour: 06",
        "vainqueur": "Simulé: LESCAR PYRENEES VOLLEY",
        "score_final": "3/2",
        "duree_totale": "2h32",
        "heure_debut": "20:31",
        "heure_fin": "23:03"
    }

    equipe_a_nom = "Simulé: SPORT ATHLETIQUE MERIGNACAIS"
    equipe_b_nom = "Simulé: LESCAR PYRENEES VOLLEY-BALL"

    sets_data = [
        {"Set": 1, equipe_a_nom: 25, equipe_b_nom: 22, "Durée": "36'"},
        {"Set": 2, equipe_a_nom: 19, equipe_b_nom: 25, "Durée": "28'"},
        {"Set": 3, equipe_a_nom: 26, equipe_b_nom: 28, "Durée": "38'"},
        {"Set": 4, equipe_a_nom: 23, equipe_b_nom: 25, "Durée": "23'"},
        {"Set": 5, equipe_a_nom: 10, equipe_b_nom: 15, "Durée": "18'"},
    ]
    df_sets = pd.DataFrame(sets_data)

    joueurs_data = {
        "Équipe": [equipe_a_nom] * 2 + [equipe_b_nom] * 2,
        "N°": ["01", "02", "01", "11"],
        "Nom Prénom": ["J. Smith", "M. Dupont", "F. Garcia", "A. Liu"],
        "Rôle": ["Attaquant", "Libéro", "Passeur", "Libéro"]
    }
    df_joueurs = pd.DataFrame(joueurs_data)

    officiels_data = {
        "Rôle": ["Arbitre 1er", "Entraîneur A", "Entraîneur B"],
        "Nom Prénom": ["A. Rbitre", "E. Entraineur", "S. Sarra"]
    }
    df_officiels = pd.DataFrame(officiels_data)

    return match_data, df_sets, df_joueurs, df_officiels, equipe_a_nom, equipe_b_nom

# --- Configuration de la Page Streamlit ---

st.set_page_config(
    page_title="Analyse Automatique de Feuille de Match",
    layout="wide"
)

st.title("🏐 Analyse de la Feuille de Match de Volley-Ball")
st.markdown("---")

# --- 1. Téléchargement du Fichier ---
st.header("1. Importer la Feuille de Match (PDF)")
uploaded_file = st.file_uploader(
    "Veuillez choisir un fichier PDF de feuille de match FFvolley.",
    type="pdf",
    accept_multiple_files=False  # Un seul fichier à la fois
)

# --- 2. Lancement de l'Analyse ---
if uploaded_file is not None:
    st.success(f"Fichier téléchargé : **{uploaded_file.name}**")
    
    # Créez le bouton pour lancer l'analyse
    if st.button("🚀 Lancer l'Analyse des Données", type="primary"):
        
        # Lancement de l'analyse (simulée)
        with st.spinner('Analyse du PDF en cours... (Simulation)...'):
            match_data, df_sets, df_joueurs, df_officiels, equipe_a_nom, equipe_b_nom = simulate_match_analysis(uploaded_file)
        
        # --- 3. Affichage des Résultats ---
        st.markdown("---")
        st.header("2. Résultats de l'Analyse (Simulée)")
        st.warning("⚠️ **Rappel important** : Les données affichées sont simulées. Pour une analyse réelle de PDFs variés, le code doit être complété par un outil OCR avancé.")

        # --- Section Récapitulatif ---
        st.subheader("🏆 Récapitulatif du Match")
        
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label="Compétition", value=match_data["competition"])
            st.metric(label="Match N°", value=match_data["match_n"])

        with col2:
            st.metric(label="Début/Fin", value=f"{match_data['heure_debut']} - {match_data['heure_fin']}")
            st.metric(label="Durée Totale", value=match_data["duree_totale"])

        with col3:
            st.metric(label="Vainqueur", value=f"🏆 {match_data['vainqueur']}", delta=match_data["score_final"])

        st.markdown("---")

        # --- Section Scores par Set ---
        st.subheader("📊 Scores par Set")
        # Colonnes pour l'affichage de la surbrillance
        set_cols = [col for col in df_sets.columns if col not in ['Set', 'Durée']]
        
        st.dataframe(
            df_sets.style.highlight_max(axis=1, subset=set_cols, color='#4CAF50'), 
            use_container_width=True
        )

        st.markdown("---")

        # --- Section Détail des Joueurs/Officiels ---
        st.subheader("👥 Détail des Participants")
        
        tab_joueurs, tab_officiels = st.tabs(["Joueurs", "Officiels"])

        with tab_joueurs:
            st.markdown(f"**Liste des joueurs pour {equipe_a_nom} et {equipe_b_nom}**")
            st.dataframe(df_joueurs, use_container_width=True, hide_index=True)

        with tab_officiels:
            st.markdown("**Officiels du match (Arbitres, Entraîneurs)**")
            st.dataframe(df_officiels, use_container_width=True, hide_index=True)
