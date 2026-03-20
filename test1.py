# --- PAGE 1 : ANALYSE TACTIQUE ---
if page == "📊 Analyse Tactique":
    # 1. AFFICHAGE DES EFFECTIFS
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader(f"🏠 {EQUIPE_A}")
        ta1, ta2, ta3 = st.tabs(["👥 Joueurs", "🛡️ Libéros", "👔 Staff"])
        with ta1: st.dataframe(df_a_final[df_a_final['Type'] == 'Joueur'][['ID', 'Identite', 'Licence']], use_container_width=True, hide_index=True)
        with ta2: st.dataframe(df_a_final[df_a_final['Type'] == 'Libéro'][['ID', 'Identite', 'Licence']], use_container_width=True, hide_index=True)
        with ta3: st.dataframe(df_a_final[df_a_final['Type'] == 'Staff'][['ID', 'Identite', 'Licence']], use_container_width=True, hide_index=True)

    with col_right:
        st.subheader(f"🚀 {EQUIPE_B}")
        tb1, tb2, tb3 = st.tabs(["👥 Joueurs", "🛡️ Libéros", "👔 Staff"])
        with tb1: st.dataframe(df_b_final[df_b_final['Type'] == 'Joueur'][['ID', 'Identite', 'Licence']], use_container_width=True, hide_index=True)
        with tb2: st.dataframe(df_b_final[df_b_final['Type'] == 'Libéro'][['ID', 'Identite', 'Licence']], use_container_width=True, hide_index=True)
        with tb3: st.dataframe(df_b_final[df_b_final['Type'] == 'Staff'][['ID', 'Identite', 'Licence']], use_container_width=True, hide_index=True)

    # 2. RÉCAPITULATIF DES SCORES
    st.divider()
    st.subheader("📊 Récapitulatif des Scores du Match")
    FINAL_SCORES_DISPLAY = FINAL_SCORES.copy()
    FINAL_SCORES_DISPLAY.columns = [f"Score {EQUIPE_A}", f"Score {EQUIPE_B}"]
    FINAL_SCORES_DISPLAY.insert(0, "Set", [f"Set {i+1}" for i in range(len(FINAL_SCORES_DISPLAY))])
    st.table(FINAL_SCORES_DISPLAY)

    # 3. ANALYSE DÉTAILLÉE PAR SET
    if sets_joues:
        tabs_sets = st.tabs(sets_joues)
        for idx, tab_name in enumerate(sets_joues):
            with tabs_sets[idx]:
                set_num = idx + 1
                
                # Extraction des DataFrames selon le Set (Alternance terrain)
                if set_num in [1, 3, 5]:
                    df_a, df_b = process_and_structure_set_1_a(extract_raw_set_1_a(st.session_state.PDF_FILENAME)), process_and_structure_set_1_b(extract_raw_set_1_b(st.session_state.PDF_FILENAME))
                    tm, n_g, n_d = extract_temps_mort_set_1(st.session_state.PDF_FILENAME), EQUIPE_A, EQUIPE_B
                else:
                    df_b, df_a = process_and_structure_set_2_b(extract_raw_set_2_b(st.session_state.PDF_FILENAME)), process_and_structure_set_2_a(extract_raw_set_2_a(st.session_state.PDF_FILENAME))
                    tm, n_g, n_d = extract_temps_mort_set_2(st.session_state.PDF_FILENAME), EQUIPE_B, EQUIPE_A

                st.info(f"🔥 ANALYSE DÉTAILLÉE : {tab_name.upper()}")
                st.write(f"⏱️ **Temps Morts :** {n_g} (`{tm[0] or '-'}` , `{tm[1] or '-'}`) | {n_d} (`{tm[2] or '-'}` , `{tm[3] or '-'}`)")
                
                # --- GRAPHIQUE DUEL (Évolution des points) ---
                tracer_duel_equipes(df_a, df_b, titre=f"Évolution {tab_name}", nom_g=n_g, nom_d=n_d)
                
                st.divider()

                # --- ANALYSE DES ROTATIONS ---
                v_a_vals, v_b_vals = df_a.iloc[0].values, df_b.iloc[0].values
                base_a = [v_a_vals[i%6] for i in range(6)]
                base_b = [v_b_vals[i%6] for i in range(6)]

                fig_rot, axes = plt.subplots(6, 2, figsize=(18, 45))

                for idx_col in range(6):
                    # CALCUL DES STATS (Logique serpentin RnCn)
                    m_a, e_a = [], []
                    for r in range(4, len(df_a)):
                        if str(df_a.iloc[r, idx_col]).strip() == '': break
                        
                        if r == 4 and idx_col == 0:
                            m_a.append(val_score(df_a, 4, 0))
                            e_a.append(val_score(df_b, 4, 0))
                        elif idx_col == 0:
                            m_a.append(val_score(df_a, r, 0) - val_score(df_a, r-1, 5))
                            e_a.append(val_score(df_b, r, 0) - val_score(df_b, r-1, 5))
                        else:
                            m_a.append(val_score(df_a, r, idx_col) - val_score(df_a, r, idx_col-1))
                            e_a.append(val_score(df_b, r, idx_col) - val_score(df_b, r, idx_col-1))

                    m_b, e_b = e_a, m_a 

                    # Affichage Terrain Gauche
                    rot_a_g = obtenir_rotation_positions(base_a, idx_col, doit_tourner=False)
                    rot_b_g = obtenir_rotation_positions(base_b, idx_col, doit_tourner=False)
                    dessiner_rotation_couleurs(axes[idx_col, 0], n_g, rot_a_g, n_d, rot_b_g, serveur='A')
                    
                    tm_a, te_a, td_a, tot_ma, tot_ea = format_stats(m_a, e_a)
                    axes[idx_col, 0].text(1, -1.5, f"pts marqués\n{tm_a}\n\nTotal: {tot_ma}", color='royalblue', va='top', family='monospace')
                    axes[idx_col, 0].text(7, -1.5, f"pts encaissés\n{te_a}\n\nTotal: {tot_ea}", color='salmon', va='top', family='monospace')
                    axes[idx_col, 0].text(13, -1.5, f"différence\n{td_a}\n\nTotal: {tot_ma-tot_ea:+d}", color='black', weight='bold', va='top', family='monospace')

                    # Affichage Terrain Droite
                    dessiner_rotation_couleurs(axes[idx_col, 1], n_g, rot_a_g, n_d, rot_b_g, serveur='B')
                    
                    tm_b, te_b, td_b, tot_mb, tot_eb = format_stats(m_b, e_b)
                    axes[idx_col, 1].text(1, -1.5, f"pts marqués\n{tm_b}\n\nTotal: {tot_mb}", color='darkorange', va='top', family='monospace')
                    axes[idx_col, 1].text(7, -1.5, f"pts encaissés\n{te_b}\n\nTotal: {tot_eb}", color='royalblue', va='top', family='monospace')
                    axes[idx_col, 1].text(13, -1.5, f"différence\n{td_b}\n\nTotal: {tot_mb-tot_eb:+d}", color='black', weight='bold', va='top', family='monospace')

                st.pyplot(fig_rot)
                plt.close(fig_rot)
