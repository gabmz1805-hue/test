# ==========================================
# 4. MAIN APP
# (Section modifiée pour ajouter le nouvel onglet)
# ==========================================

def main():
    st.title("🏐 VolleyStats Pro")

    with st.sidebar:
        uploaded_file = st.file_uploader("Upload PDF", type="pdf")
        with st.expander("⚙️ Calibration"):
            base_x = st.number_input("X Start", 123); base_y = st.number_input("Y Start", 88)
            w = st.number_input("Width", 23); h = st.number_input("Height", 20)
            off_x = st.number_input("Right Offset", 492)
            off_y = st.number_input("Down Offset", 151)

    if not uploaded_file:
        st.info("Please upload a file.")
        return

    extractor = VolleySheetExtractor(uploaded_file)
    t_home, t_away, scores = extract_match_info(uploaded_file)
    
    with st.spinner("Extracting Data..."):
        lineups = extractor.extract_full_match(base_x, base_y, w, h, off_x, off_y, 842)
        df = pd.DataFrame(lineups) # df contient les colonnes: Set, Team, Starters (liste des 6 joueurs)

    if df.empty:
        st.error("Extraction failed. Check PDF.")
        return

    # --- Préparation du tableau de données complet (pour les onglets 5 et 6) ---
    export = df.copy()
    # Convertit la liste des Starters en 6 colonnes séparées (Z1 à Z6)
    cols = pd.DataFrame(export['Starters'].tolist(), columns=[f'Z{i+1}' for i in range(6)])
    # Fusionne les colonnes Set et Team avec les colonnes de rotation
    final_df_table = pd.concat([export[['Set', 'Team']], cols], axis=1)
    
    # Scoreboard (non modifié)
    h_wins = sum(1 for s in scores if s['Home'] > s['Away'])
    a_wins = sum(1 for s in scores if s['Away'] > s['Home'])
    
    c1, c2, c3 = st.columns([2, 1, 2])
    c1.metric("HOME", t_home)
    c3.metric("AWAY", t_away)
    c2.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{h_wins} - {a_wins}</h1>", unsafe_allow_html=True)

    # Analytics Tabs (Modification ici: ajout de tab5, Export devient tab6)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["1. Money Time", "2. Players", "3. Rotations", "4. Duration", "5. Data Table", "6. Export"])

    with tab1:
        if scores:
            analysis, clutch = analyze_money_time(scores, t_home, t_away)
            c_mt1, c_mt2 = st.columns(2)
            c_mt1.metric(f"Clutch Wins ({t_home})", clutch.get(t_home, 0))
            c_mt2.metric(f"Clutch Wins ({t_away})", clutch.get(t_away, 0))
            for item in analysis: st.write(item)
        else: st.warning("No score data found.")

    with tab2:
        if scores:
            stats = calculate_player_stats(df, scores)
            if not stats.empty:
                ca, cb = st.columns(2)
                with ca: st.dataframe(stats[stats['Team']=="Home"], use_container_width=True)
                with cb: st.dataframe(stats[stats['Team']=="Away"], use_container_width=True)

    with tab3:
        c_s, c_t = st.columns(2)
        sel_set = c_s.selectbox("Set", df['Set'].unique())
        sel_team = c_t.selectbox("Team", ["Home", "Away"])
        row = df[(df['Set'] == sel_set) & (df['Team'] == sel_team)]
        if not row.empty:
            st.plotly_chart(draw_court_view(row.iloc[0]['Starters']), use_container_width=False)
            

    with tab4:
        if scores:
            durations = [s['Duration'] for s in scores if 'Duration' in s]
            if durations:
                st.metric("Total Duration", f"{sum(durations)} min")
                st.bar_chart(pd.DataFrame({"Set": range(1, len(durations)+1), "Minutes": durations}).set_index("Set"))

    with tab5: # Nouvel Onglet: Affichage du tableau de données des rotations
        st.subheader("📊 Rotations des Joueurs par Set et par Équipe")
        st.markdown("**Z1** correspond à la position arrière droit (serveur), **Z6** est la position arrière central.")
        st.dataframe(
            final_df_table, 
            use_container_width=True,
            column_order=('Set', 'Team', 'Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6') # Ordre des colonnes logique
        )

    with tab6: # Ancien Tab5, maintenant Tab6
        try:
            f_bytes = uploaded_file.getvalue()
            img, _ = get_page_image(f_bytes)
            st.image(draw_grid(img, base_x, base_y, w, h, off_x, off_y))
            st.caption("Visualisation des zones d'extraction du PDF (Rouge=Home, Bleu=Away).")
        except: pass
        
        st.download_button(
            "Download CSV", 
            final_df_table.to_csv(index=False).encode('utf-8'), # Utilise final_df_table préparé
            "match_rotations.csv", 
            "text/csv"
        )

if __name__ == "__main__":
    main()
