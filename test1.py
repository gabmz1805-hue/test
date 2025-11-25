import streamlit as st
import pdfplumber
import pandas as pd
import pypdfium2 as pdfium
import re
import gc
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image, ImageDraw

st.set_page_config(page_title="🏐 VolleyStats Pro", page_icon="🏐", layout="wide")

# ==========================================
# 1. ENGINE (Reading Data)
# ==========================================

@st.cache_data(show_spinner=False)
def get_page_image(file_bytes):
    """Renders PDF page to image using C++ engine (Fast & Low RAM)."""
    try:
        pdf = pdfium.PdfDocument(file_bytes)
        page = pdf[0]
        scale = 1.0 # 72 DPI
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()
        page.close()
        pdf.close()
        gc.collect()
        return pil_image, scale
    except Exception as e:
        st.error(f"Erreur lors du rendu de l'image PDF : {e}")
        return None, 1.0

def extract_match_info(file):
    """Extracts Team Names and Set Scores."""
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            text = pdf.pages[0].extract_text()
    except Exception as e:
        st.error(f"Erreur lors de l'ouverture du PDF : {e}")
        return "Home Team", "Away Team", []
        
    lines = text.split('\n')
    
    # A. Detect Team Names
    potential_names = []
    for line in lines:
        if "Début:" in line:
            parts = line.split("Début:")
            for part in parts[:-1]:
                if "Fin:" in part: part = part.split("Fin:")[-1]
                part = re.sub(r'\d{2}:\d{2}\s*R?', '', part)
                clean_name = re.sub(r'\b(SA|SB|S|R)\b', '', part)
                clean_name = re.sub(r'^[^A-Z]+|[^A-Z]+$', '', clean_name).strip()
                if len(clean_name) > 3: potential_names.append(clean_name)

    unique_names = list(dict.fromkeys(potential_names))
    t_home = unique_names[1] if len(unique_names) > 1 else "Home Team"
    t_away = unique_names[0] if len(unique_names) > 0 else "Away Team"
    
    # B. Detect Set Scores
    scores = []
    duration_pattern = re.compile(r"(\d{1,3})\s*['’′`]")
    found_table = False
    
    for line in lines:
        if "RESULTATS" in line: found_table = True
        if "Vainqueur" in line: found_table = False
        
        if found_table:
            match = duration_pattern.search(line)
            if match:
                duration_val = int(match.group(1))
                if duration_val < 60: # Filter out Total Duration
                    parts = line.split(match.group(0))
                    if len(parts) >= 2:
                        left = re.findall(r'\d+', parts[0])
                        right = re.findall(r'\d+', parts[1])
                        if len(left) >= 2 and len(right) >= 1:
                            try:
                                scores.append({"Home": int(left[-2]), "Away": int(right[0]), "Duration": duration_val})
                            except: pass
    return t_home, t_away, scores

class VolleySheetExtractor:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file

    def extract_full_match(self, base_x, base_y, w, h, offset_x, offset_y, p_height):
        match_data = []
        try:
            with pdfplumber.open(self.pdf_file) as pdf:
                page = pdf.pages[0]
                for set_num in range(1, 6): 
                    current_y = base_y + ((set_num - 1) * offset_y)
                    if current_y + h < p_height:
                        # Left
                        row_l = self._extract_row(page, current_y, base_x, w, h)
                        if row_l: match_data.append({"Set": set_num, "Team": "Home", "Starters": row_l})
                        # Right
                        row_r = self._extract_row(page, current_y, base_x + offset_x, w, h)
                        if row_r: match_data.append({"Set": set_num, "Team": "Away", "Starters": row_r})
        except Exception as e:
            st.error(f"Erreur d'extraction de la page : {e}")
            
        gc.collect()
        return match_data

    def _extract_row(self, page, top_y, start_x, w, h):
        row_data = []
        for i in range(6):
            drift = i * 0.3
            px_x = start_x + (i * w) + drift
            # Box: +3px width, Top 80% height
            bbox = (px_x - 3, top_y, px_x + w + 3, top_y + (h * 0.8))
            try:
                # La capture de texte est la partie la plus critique et dépend de pdfplumber
                text = page.crop(bbox).extract_text() 
                val = "?"
                if text:
                    for token in text.split():
                        clean = re.sub(r'[^0-9]', '', token)
                        if clean.isdigit() and len(clean) <= 2:
                            val = clean; break
                row_data.append(val)
            except: 
                row_data.append("?")
                
        if all(x == "?" for x in row_data): return None
        return row_data

# ==========================================
# 2. ANALYTICS (Math)
# ==========================================

def calculate_player_stats(df, scores):
    """Calculates Win % for starters."""
    stats = {}
    set_winners = {i+1: ("Home" if s['Home'] > s['Away'] else "Away") for i, s in enumerate(scores)}

    for _, row in df.iterrows():
        team = row['Team']
        set_n = row['Set']
        if set_n in set_winners:
            won = (team == set_winners[set_n])
            for p in row['Starters']:
                if p.isdigit():
                    if p not in stats: stats[p] = {'team': team, 'played': 0, 'won': 0}
                    stats[p]['played'] += 1
                    if won: stats[p]['won'] += 1
    
    data = []
    for p, s in stats.items():
        pct = (s['won']/s['played'])*100 if s['played'] > 0 else 0
        data.append({"Player": f"#{p}", "Team": s['team'], "Sets": s['played'], "Win %": round(pct, 1)})
    
    if not data: return pd.DataFrame()
    return pd.DataFrame(data).sort_values(['Team', 'Win %'], ascending=[True, False])

def analyze_money_time(scores, t_home, t_away):
    """Analyzes close sets."""
    analysis = []
    clutch_stats = {t_home: 0, t_away: 0}
    
    for i, s in enumerate(scores):
        diff = abs(s['Home'] - s['Away'])
        winner = t_home if s['Home'] > s['Away'] else t_away
        
        if max(s['Home'], s['Away']) >= 20 and diff <= 3:
            clutch_stats[winner] += 1
            analysis.append(f"✅ Set {i+1} ({s['Home']}-{s['Away']}) : Won by **{winner}** (Clutch).")
        elif diff > 5:
            analysis.append(f"⚠️ Set {i+1} ({s['Home']}-{s['Away']}) : Comfortable win for {winner}.")
        else:
            analysis.append(f"ℹ️ Set {i+1} ({s['Home']}-{s['Away']}) : Standard win for {winner}.")
            
    return analysis, clutch_stats

# ==========================================
# 3. VISUALS (Drawings)
# ==========================================

def draw_court_view(starters):
    safe = [s if s != "?" else "-" for s in starters]
    while len(safe) < 6: safe.append("-")
    # Grid: Front(4,3,2) Back(5,6,1)
    grid = [[safe[3], safe[2], safe[1]], [safe[4], safe[5], safe[0]]]
    
    fig = px.imshow(grid, text_auto=True, color_continuous_scale='Blues',
                      x=['Left', 'Center', 'Right'], y=['Front Row', 'Back Row'])
    fig.update_layout(coloraxis_showscale=False, height=300, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_traces(textfont_size=24)
    return fig

def draw_grid(base_img, bx, by, w, h, off_x, off_y):
    """Dessine des carrés de calibration sur l'image pour vérifier l'extraction."""
    if base_img is None:
        return None
        
    img = base_img.copy()
    draw = ImageDraw.Draw(img)
    
    # Dessine des carrés pour les 4 premiers sets (pour vérification)
    for s in range(4): 
        y = by + (s * off_y)
        for i in range(6):
            d = i * 0.3
            # Équipe Home (gauche)
            draw.rectangle([bx+(i*w)+d, y, bx+(i*w)+d+w, y+h], outline="red", width=2)
            # Équipe Away (droite)
            draw.rectangle([bx+off_x+(i*w)+d, y, bx+off_x+(i*w)+d+w, y+h], outline="blue", width=2)
    return img

# ==========================================
# 4. MAIN APP
# ==========================================

def main():
    st.title("🏐 VolleyStats Pro")

    with st.sidebar:
        # C'EST ICI QUE LE BOUTON D'IMPORTATION PDF EST CRÉÉ
        uploaded_file = st.file_uploader("Upload PDF", type="pdf")
        with st.expander("⚙️ Calibration"):
            # Ces valeurs sont essentielles pour le bon fonctionnement de l'extraction
            base_x = st.number_input("X Start", 123) 
            base_y = st.number_input("Y Start", 88)
            w = st.number_input("Width", 23)
            h = st.number_input("Height", 20)
            off_x = st.number_input("Right Offset", 492)
            off_y = st.number_input("Down Offset", 151)

    if not uploaded_file:
        st.info("Veuillez charger un fichier PDF de feuille de match pour commencer l'analyse.")
        # Ajout d'une section d'aide pour le déploiement
        st.markdown("""
        ---
        ### 🚨 Erreur `ModuleNotFoundError` ?
        Si l'application ne se charge pas après l'importation PDF, vous devez créer un fichier `requirements.txt` 
        et y ajouter les dépendances suivantes :
        * `streamlit`
        * `pandas`
        * `pdfplumber`
        * `pypdfium2`
        * `plotly`
        * `Pillow` (souvent inclus dans Streamlit, mais par sécurité)
        """)
        return

    # Logique d'extraction
    extractor = VolleySheetExtractor(uploaded_file)
    t_home, t_away, scores = extract_match_info(uploaded_file)
    
    with st.spinner("Extraction des données en cours..."):
        lineups = extractor.extract_full_match(base_x, base_y, w, h, off_x, off_y, 842)
        df = pd.DataFrame(lineups)

    if df.empty:
        st.error("Échec de l'extraction des compositions d'équipe. Veuillez vérifier les paramètres de Calibration.")
        return

    # --- AFFICHAGE PRINCIPAL ---

    # Scoreboard
    h_wins = sum(1 for s in scores if s['Home'] > s['Away'])
    a_wins = sum(1 for s in scores if s['Away'] > s['Home'])
    
    c1, c2, c3 = st.columns([2, 1, 2])
    c1.metric(t_home, h_wins)
    c3.metric(t_away, a_wins)
    c2.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{h_wins} - {a_wins}</h1>", unsafe_allow_html=True)

    # Analytics Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["1. Money Time", "2. Joueurs", "3. Rotations", "4. Durée", "5. Export"])

    with tab1:
        if scores:
            analysis, clutch = analyze_money_time(scores, t_home, t_away)
            c_mt1, c_mt2 = st.columns(2)
            c_mt1.metric(f"Victoires Clutch ({t_home})", clutch.get(t_home, 0))
            c_mt2.metric(f"Victoires Clutch ({t_away})", clutch.get(t_away, 0))
            for item in analysis: st.write(item)
        else: st.warning("Aucune donnée de score trouvée.")

    with tab2:
        if scores:
            stats = calculate_player_stats(df, scores)
            if not stats.empty:
                ca, cb = st.columns(2)
                with ca: 
                    st.subheader(f"Statistiques {t_home}")
                    st.dataframe(stats[stats['Team']=="Home"], use_container_width=True)
                with cb: 
                    st.subheader(f"Statistiques {t_away}")
                    st.dataframe(stats[stats['Team']=="Away"], use_container_width=True)

    with tab3:
        st.markdown("Visualisation de la composition de l'équipe pour une rotation spécifique. ")
        c_s, c_t = st.columns(2)
        sel_set = c_s.selectbox("Set", df['Set'].unique())
        sel_team = c_t.selectbox("Équipe", [t_home, t_away])
        
        # Mappage pour retrouver l'équipe dans le DataFrame (Home/Away)
        team_df_name = "Home" if sel_team == t_home else "Away"
        
        row = df[(df['Set'] == sel_set) & (df['Team'] == team_df_name)]
        
        if not row.empty:
            st.plotly_chart(draw_court_view(row.iloc[0]['Starters']), use_container_width=False)
        else:
            st.warning("Aucune donnée de formation trouvée pour ce set/cette équipe.")


    with tab4:
        if scores:
            durations = [s['Duration'] for s in scores if 'Duration' in s]
            if durations:
                st.metric("Durée Totale du Match", f"{sum(durations)} minutes")
                st.bar_chart(pd.DataFrame({"Set": range(1, len(durations)+1), "Minutes": durations}).set_index("Set"))
            else: st.warning("Aucune donnée de durée de set trouvée.")

    with tab5:
        st.subheader("Vérification de l'Extraction & Export CSV")
        st.warning("Utilisez l'onglet 'Export' pour vérifier si les carrés rouges/bleus correspondent aux numéros de joueurs sur votre PDF.")
        
        # Affichage de l'image de calibration
        try:
            f_bytes = uploaded_file.getvalue()
            img, _ = get_page_image(f_bytes)
            if img:
                st.image(draw_grid(img, base_x, base_y, w, h, off_x, off_y), caption="Grille de Calibration")
            else:
                st.error("Impossible de générer l'image de vérification.")
        except Exception as e: 
            st.warning(f"Impossible de charger/afficher l'image PDF : {e}")
            
        st.markdown("---")
        
        # Préparation du DataFrame pour l'exportation
        export = df.copy()
        cols = pd.DataFrame(export['Starters'].tolist(), columns=[f'Position_{i+1}' for i in range(6)])
        final = pd.concat([export[['Set', 'Team']], cols], axis=1)
        
        st.dataframe(final)
        
        st.download_button(
            "⬇️ Télécharger les Compositions (CSV)", 
            final.to_csv(index=False).encode('utf-8'), 
            "match_compositions.csv", 
            "text/csv"
        )

if __name__ == "__main__":
    main()
