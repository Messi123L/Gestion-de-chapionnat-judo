import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

# Configuration initiale
st.set_page_config(page_title="Championnat Marocain de Judo - Tableau de Bord", layout="wide", page_icon="🥋")
st.markdown("<h1 style='text-align: center; color: #2E86C1;'>Championnat Marocain de Judo 2022-2023</h1>", unsafe_allow_html=True)

# Fonctions utilitaires
def categorie_poids(poids):
    if poids <= 60: return "-60 kg"
    elif poids <= 66: return "-66 kg"
    elif poids <= 73: return "-73 kg"
    elif poids <= 81: return "-81 kg"
    elif poids <= 90: return "-90 kg"
    elif poids <= 100: return "-100 kg"
    else: return "+100 kg"

def save_data():
    with open("judo_data.json", "w") as f:
        json.dump({
            "judo_data": st.session_state.judo_data.to_dict(),
            "classement_equipes": st.session_state.classement_equipes.to_dict(),
            "classement_joueurs": st.session_state.classement_joueurs.to_dict()
        }, f)

def load_data():
    try:
        with open("judo_data.json", "r") as f:
            data = json.load(f)
            st.session_state.judo_data = pd.DataFrame(data["judo_data"])
            st.session_state.classement_equipes = pd.DataFrame(data["classement_equipes"])
            st.session_state.classement_joueurs = pd.DataFrame(data["classement_joueurs"])
    except FileNotFoundError:
        st.session_state.judo_data = pd.DataFrame(columns=['Equipe', 'Joueur', 'Poids', 'Victoires', 'Defaites', 'Points', 'Performance', 'Categorie'])
        st.session_state.classement_equipes = pd.DataFrame(columns=['Equipe', 'Points_Totaux', 'Victoires_Totaux'])
        st.session_state.classement_joueurs = pd.DataFrame(columns=['Joueur', 'Equipe', 'Points', 'Victoires'])

# Charger les données au démarrage
if 'judo_data' not in st.session_state:
    load_data()

# Sidebar pour la navigation
st.sidebar.markdown("<h2 style='color: #2E86C1;'>Gestion de la Compétition</h2>", unsafe_allow_html=True)
option = st.sidebar.selectbox("Choisir une action", [
    "Ajouter Équipe/Joueur", "Enregistrer un Match", "Supprimer Données", "Modifier Données", 
    "Voir Classements", "Analyser Performances", "Exporter/Importer Données", "Podium"
], key="nav_select")

# Fonction pour ajouter un séparateur stylisé
def add_separator():
    st.markdown("<hr style='border: 1px solid #2E86C1;'>", unsafe_allow_html=True)

# Fonction pour exporter en PDF
def export_to_pdf(title, stats, table_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))
    
    if stats:
        elements.append(Paragraph("Statistiques", styles['Heading2']))
        for label, value in stats.items():
            elements.append(Paragraph(f"{label}: {value}", styles['Normal']))
        elements.append(Spacer(1, 12))
    
    if table_data is not None and not table_data.empty:
        elements.append(Paragraph("Détails", styles['Heading2']))
        table = Table([table_data.columns.tolist()] + table_data.values.tolist())
        table.setStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ])
        elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# 1. Ajout d'équipes et de joueurs
if option == "Ajouter Équipe/Joueur":
    st.subheader("Ajouter une Équipe ou un Joueur")
    add_separator()
    with st.form("ajout_form"):
        col1, col2 = st.columns(2)
        with col1:
            equipe = st.text_input("Nom de l'Équipe", placeholder="Ex: Équipe Casablanca")
            joueur = st.text_input("Nom du Joueur", placeholder="Ex: Ahmed Benali")
        with col2:
            poids = st.number_input("Poids (kg)", min_value=30, max_value=150, step=1)
        
        victoires = st.number_input("Nombre de Victoires", min_value=0, step=1, value=0)
        defaites = st.number_input("Nombre de Défaites", min_value=0, step=1, value=0)
        
        submit = st.form_submit_button("Ajouter", type="primary")
        
        if submit and equipe and joueur:
            if joueur in st.session_state.judo_data['Joueur'].values:
                st.error("Ce joueur existe déjà !")
            else:
                new_data = pd.DataFrame({
                    'Equipe': [equipe],
                    'Joueur': [joueur],
                    'Poids': [poids],
                    'Victoires': [victoires],
                    'Defaites': [defaites],
                    'Points': [0],
                    'Performance': [victoires / (victoires + defaites) if (victoires + defaites) > 0 else 0],
                    'Categorie': [categorie_poids(poids)]
                })
                st.session_state.judo_data = pd.concat([st.session_state.judo_data, new_data], ignore_index=True)
                
                if equipe not in st.session_state.classement_equipes['Equipe'].values:
                    st.session_state.classement_equipes = pd.concat([st.session_state.classement_equipes, 
                                                                  pd.DataFrame({'Equipe': [equipe], 'Points_Totaux': [0], 'Victoires_Totaux': [victoires]})], 
                                                                  ignore_index=True)
                else:
                    st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Equipe'] == equipe, 'Victoires_Totaux'] += victoires
                
                if joueur not in st.session_state.classement_joueurs['Joueur'].values:
                    st.session_state.classement_joueurs = pd.concat([st.session_state.classement_joueurs, 
                                                                  pd.DataFrame({'Joueur': [joueur], 'Equipe': [equipe], 'Points': [0], 'Victoires': [victoires]})], 
                                                                  ignore_index=True)
                else:
                    st.session_state.classement_joueurs.loc[st.session_state.classement_joueurs['Joueur'] == joueur, 'Victoires'] += victoires
                
                save_data()
                st.success(f"Équipe/Joueur {joueur} ajouté avec succès !", icon="✅")

# 2. Enregistrer un match
if option == "Enregistrer un Match":
    st.subheader("Enregistrer un Match")
    add_separator()
    joueurs = st.session_state.judo_data['Joueur'].tolist()
    
    if not joueurs:
        st.warning("Aucun joueur disponible. Ajoutez des joueurs d'abord !")
    else:
        if 'vainqueur_key' not in st.session_state:
            st.session_state.vainqueur_key = "Égalité"
        
        col1, col2 = st.columns(2)
        with col1:
            joueur1 = st.selectbox("Joueur 1", joueurs, key="joueur1")
        with col2:
            joueur2 = st.selectbox("Joueur 2", joueurs, index=1 if len(joueurs) > 1 else 0, key="joueur2")
        
        vainqueur = st.selectbox("Vainqueur", ["Égalité"] + joueurs, key="vainqueur_select")
        st.session_state.vainqueur_key = vainqueur
        is_egalite = (st.session_state.vainqueur_key == "Égalité")
        type_victoire = st.selectbox("Type de victoire", ["Ippon (10 pts)", "Waza-ari (7 pts)", "Yuko (5 pts)"], 
                                     disabled=is_egalite, key="type_victoire")
        
        with st.form("match_form"):
            submit_match = st.form_submit_button("Enregistrer", type="primary")
            
            if submit_match:
                if joueur1 == joueur2:
                    st.error("Les deux joueurs doivent être différents !")
                else:
                    points_gagnes = 0
                    if not is_egalite:
                        if type_victoire == "Ippon (10 pts)": points_gagnes = 10
                        elif type_victoire == "Waza-ari (7 pts)": points_gagnes = 7
                        elif type_victoire == "Yuko (5 pts)": points_gagnes = 5
                    
                    if vainqueur == joueur1:
                        st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur1, 'Victoires'] += 1
                        st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur1, 'Points'] += points_gagnes
                        st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur2, 'Defaites'] += 1
                        equipe1 = st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur1, 'Equipe'].values[0]
                        st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Equipe'] == equipe1, 'Points_Totaux'] += points_gagnes
                        st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Equipe'] == equipe1, 'Victoires_Totaux'] += 1
                        st.session_state.classement_joueurs.loc[st.session_state.classement_joueurs['Joueur'] == joueur1, 'Points'] += points_gagnes
                        st.session_state.classement_joueurs.loc[st.session_state.classement_joueurs['Joueur'] == joueur1, 'Victoires'] += 1
                    elif vainqueur == joueur2:
                        st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur2, 'Victoires'] += 1
                        st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur2, 'Points'] += points_gagnes
                        st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur1, 'Defaites'] += 1
                        equipe2 = st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur2, 'Equipe'].values[0]
                        st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Equipe'] == equipe2, 'Points_Totaux'] += points_gagnes
                        st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Equipe'] == equipe2, 'Victoires_Totaux'] += 1
                        st.session_state.classement_joueurs.loc[st.session_state.classement_joueurs['Joueur'] == joueur2, 'Points'] += points_gagnes
                        st.session_state.classement_joueurs.loc[st.session_state.classement_joueurs['Joueur'] == joueur2, 'Victoires'] += 1
                    elif vainqueur != "Égalité":
                        st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == vainqueur, 'Victoires'] += 1
                        st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == vainqueur, 'Points'] += points_gagnes
                        st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur1, 'Defaites'] += 1
                        st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur2, 'Defaites'] += 1
                        equipe_v = st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == vainqueur, 'Equipe'].values[0]
                        st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Equipe'] == equipe_v, 'Points_Totaux'] += points_gagnes
                        st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Equipe'] == equipe_v, 'Victoires_Totaux'] += 1
                        st.session_state.classement_joueurs.loc[st.session_state.classement_joueurs['Joueur'] == vainqueur, 'Points'] += points_gagnes
                        st.session_state.classement_joueurs.loc[st.session_state.classement_joueurs['Joueur'] == vainqueur, 'Victoires'] += 1
                    
                    for joueur in [joueur1, joueur2] + ([vainqueur] if vainqueur not in [joueur1, joueur2, "Égalité"] else []):
                        v = st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur, 'Victoires'].values[0]
                        d = st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur, 'Defaites'].values[0]
                        st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur, 'Performance'] = v / (v + d) if (v + d) > 0 else 0
                    
                    save_data()
                    st.success(f"Match {joueur1} vs {joueur2} enregistré !", icon="✅")

# 3. Supprimer des données
if option == "Supprimer Données":
    st.subheader("Supprimer des Données")
    add_separator()
    with st.form("supprimer_form"):
        joueur_a_supprimer = st.selectbox("Joueur à supprimer", st.session_state.judo_data['Joueur'].tolist())
        submit_supprimer = st.form_submit_button("Supprimer", type="primary")
        
        if submit_supprimer:
            equipe = st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur_a_supprimer, 'Equipe'].values[0]
            points = st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur_a_supprimer, 'Points'].values[0]
            victoires = st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur_a_supprimer, 'Victoires'].values[0]
            
            st.session_state.judo_data = st.session_state.judo_data[st.session_state.judo_data['Joueur'] != joueur_a_supprimer]
            st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Equipe'] == equipe, 'Points_Totaux'] -= points
            st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Equipe'] == equipe, 'Victoires_Totaux'] -= victoires
            st.session_state.classement_joueurs = st.session_state.classement_joueurs[st.session_state.classement_joueurs['Joueur'] != joueur_a_supprimer]
            
            if equipe not in st.session_state.judo_data['Equipe'].values:
                st.session_state.classement_equipes = st.session_state.classement_equipes[st.session_state.classement_equipes['Equipe'] != equipe]
            
            save_data()
            st.success(f"Joueur {joueur_a_supprimer} supprimé avec succès !", icon="✅")

# 4. Modifier des données
if option == "Modifier Données":
    st.subheader("Modifier des Données")
    add_separator()
    joueurs = st.session_state.judo_data['Joueur'].tolist()
    if joueurs:
        with st.form("modifier_form"):
            joueur_a_modifier = st.selectbox("Joueur à modifier", joueurs)
            joueur_data = st.session_state.judo_data[st.session_state.judo_data['Joueur'] == joueur_a_modifier].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                equipe = st.text_input("Nom de l'Équipe", value=joueur_data['Equipe'])
                poids = st.number_input("Poids (kg)", min_value=30, max_value=150, step=1, value=int(joueur_data['Poids']))
            with col2:
                victoires = st.number_input("Nombre de Victoires", min_value=0, step=1, value=int(joueur_data['Victoires']))
                defaites = st.number_input("Nombre de Défaites", min_value=0, step=1, value=int(joueur_data['Defaites']))
            
            submit_modifier = st.form_submit_button("Modifier", type="primary")
            
            if submit_modifier:
                ancienne_equipe = joueur_data['Equipe']
                st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur_a_modifier, 'Equipe'] = equipe
                st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur_a_modifier, 'Poids'] = poids
                st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur_a_modifier, 'Victoires'] = victoires
                st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur_a_modifier, 'Defaites'] = defaites
                st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur_a_modifier, 'Performance'] = victoires / (victoires + defaites) if (victoires + defaites) > 0 else 0
                st.session_state.judo_data.loc[st.session_state.judo_data['Joueur'] == joueur_a_modifier, 'Categorie'] = categorie_poids(poids)
                
                st.session_state.classement_joueurs.loc[st.session_state.classement_joueurs['Joueur'] == joueur_a_modifier, 'Equipe'] = equipe
                st.session_state.classement_joueurs.loc[st.session_state.classement_joueurs['Joueur'] == joueur_a_modifier, 'Victoires'] = victoires
                
                if ancienne_equipe != equipe:
                    st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Equipe'] == ancienne_equipe, 'Victoires_Totaux'] -= joueur_data['Victoires']
                    if equipe not in st.session_state.classement_equipes['Equipe'].values:
                        st.session_state.classement_equipes = pd.concat([st.session_state.classement_equipes, 
                                                                      pd.DataFrame({'Equipe': [equipe], 'Points_Totaux': [joueur_data['Points']], 'Victoires_Totaux': [victoires]})], 
                                                                      ignore_index=True)
                    else:
                        st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Equipe'] == equipe, 'Victoires_Totaux'] += victoires
                
                save_data()
                st.success(f"Joueur {joueur_a_modifier} modifié avec succès !", icon="✅")
    else:
        st.warning("Aucun joueur à modifier.")

# 5. Voir les classements
if option == "Voir Classements":
    st.subheader("Classements")
    add_separator()
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Classement des Équipes")
        filtre_equipe = st.selectbox("Filtrer par catégorie", ["Toutes"] + st.session_state.judo_data['Categorie'].unique().tolist(), key="filtre_equipe")
        classement_equipes = st.session_state.classement_equipes.sort_values(by='Points_Totaux', ascending=False)
        st.table(classement_equipes[['Equipe', 'Points_Totaux', 'Victoires_Totaux']].style.set_properties(**{'text-align': 'center'}))
    
    with col2:
        st.markdown("### Classement des Joueurs")
        filtre_joueur = st.selectbox("Filtrer par catégorie", ["Toutes"] + st.session_state.judo_data['Categorie'].unique().tolist(), key="filtre_joueur")
        classement_joueurs = st.session_state.classement_joueurs.sort_values(by='Points', ascending=False)
        if filtre_joueur != "Toutes":
            classement_joueurs = classement_joueurs[classement_joueurs['Joueur'].isin(
                st.session_state.judo_data[st.session_state.judo_data['Categorie'] == filtre_joueur]['Joueur']
            )]
        st.table(classement_joueurs[['Joueur', 'Equipe', 'Points', 'Victoires']].style.set_properties(**{'text-align': 'center'}))

# 6. Analyser les performances (niveau olympique avec export PDF)
if option == "Analyser Performances":
    st.subheader("Analyse des Performances - Niveau Olympique")
    add_separator()
    df = st.session_state.judo_data
    
    if df.empty:
        st.warning("Aucune donnée disponible pour l'analyse.")
    else:
        # Filtres avancés
        st.markdown("### Filtres")
        col1, col2 = st.columns(2)
        with col1:
            categorie = st.selectbox("Catégorie de poids", ["Toutes"] + sorted(df['Categorie'].unique().tolist()), key="categorie_filter")
        with col2:
            equipe_filter = st.selectbox("Équipe", ["Toutes"] + sorted(df['Equipe'].unique().tolist()), key="equipe_filter")
        
        filtered_df = df
        if categorie != "Toutes":
            filtered_df = filtered_df[filtered_df['Categorie'] == categorie]
        if equipe_filter != "Toutes":
            filtered_df = filtered_df[filtered_df['Equipe'] == equipe_filter]
        
        # Statistiques avancées
        st.markdown("### Statistiques Avancées")
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        with col_stats1:
            total_combats = int(filtered_df['Victoires'].sum() + filtered_df['Defaites'].sum())
            st.metric("Total Combats", total_combats)
        with col_stats2:
            total_points = int(filtered_df['Points'].sum())
            st.metric("Points Totaux", total_points)
        with col_stats3:
            ratio = f"{filtered_df['Points'].sum() / filtered_df['Victoires'].sum():.2f}" if filtered_df['Victoires'].sum() > 0 else "N/A"
            st.metric("Ratio Points/Victoire", ratio)
        with col_stats4:
            perf_moyenne = f"{filtered_df['Performance'].mean():.2%}"
            st.metric("Performance Moyenne", perf_moyenne)
        
        # Visualisations olympiques
        st.markdown("### Visualisations")
        tab1, tab2, tab3, tab4 = st.tabs(["Classement par Points", "Performance par Équipe/Catégorie", "Top Joueurs (Radar)", "Victoires par Équipe"])
        
        with tab1:
            fig1 = px.bar(filtered_df.sort_values('Points', ascending=False), x='Joueur', y='Points', color='Equipe', 
                          title="Classement par Points", text=filtered_df['Points'].astype(int), height=500)
            fig1.update_traces(textposition='outside')
            fig1.update_layout(xaxis_title="Joueur", yaxis_title="Points", bargap=0.2, showlegend=True)
            st.plotly_chart(fig1, use_container_width=True)
        
        with tab2:
            heatmap_data = filtered_df.pivot_table(values='Performance', index='Equipe', columns='Categorie', aggfunc='mean').fillna(0)
            fig2 = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale='Viridis',
                text=heatmap_data.values.round(2),
                texttemplate="%{text}",
                textfont={"size": 12}
            ))
            fig2.update_layout(title="Performance Moyenne par Équipe et Catégorie", height=500)
            st.plotly_chart(fig2, use_container_width=True)
        
        with tab3:
            top_5 = filtered_df.sort_values('Points', ascending=False).head(5)
            if len(top_5) >= 1:
                fig3 = go.Figure()
                categories = ['Victoires', 'Points', 'Performance']
                for _, row in top_5.iterrows():
                    fig3.add_trace(go.Scatterpolar(
                        r=[row['Victoires'], row['Points'] / 10, row['Performance'] * 100],  # Normalisation pour lisibilité
                        theta=categories,
                        fill='toself',
                        name=f"{row['Joueur']} ({row['Equipe']})"
                    ))
                fig3.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, max(top_5['Points'].max() / 10, top_5['Victoires'].max(), top_5['Performance'].max() * 100)])),
                    showlegend=True,
                    title="Comparaison des Top 5 Joueurs (Radar)",
                    height=500
                )
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Pas assez de joueurs pour afficher un radar.")
        
        with tab4:
            victoires_par_equipe = filtered_df.groupby('Equipe')['Victoires'].sum().reset_index()
            fig4 = px.pie(victoires_par_equipe, names='Equipe', values='Victoires', 
                          title="Répartition des Victoires par Équipe", hole=0.3, height=500)
            fig4.update_traces(textinfo='percent+label', pull=[0.1 if i == 0 else 0 for i in range(len(victoires_par_equipe))])
            st.plotly_chart(fig4, use_container_width=True)
        
        # Tableau interactif détaillé
        st.markdown("### Tableau des Performances")
        st.dataframe(filtered_df[['Joueur', 'Equipe', 'Categorie', 'Poids', 'Victoires', 'Defaites', 'Points', 'Performance']], 
                     column_config={
                         "Performance": st.column_config.NumberColumn(format="%.2f"),
                         "Points": st.column_config.NumberColumn(format="%d"),
                         "Victoires": st.column_config.NumberColumn(format="%d"),
                         "Defaites": st.column_config.NumberColumn(format="%d")
                     }, use_container_width=True)
        
        # Bouton d'exportation en PDF
        stats = {
            "Total Combats": total_combats,
            "Points Totaux": total_points,
            "Ratio Points/Victoire": ratio,
            "Performance Moyenne": perf_moyenne
        }
        pdf_buffer = export_to_pdf("Analyse des Performances - Championnat Marocain de Judo", stats, filtered_df[['Joueur', 'Equipe', 'Categorie', 'Poids', 'Victoires', 'Defaites', 'Points', 'Performance']])
        st.download_button(
            label="Exporter l'Analyse en PDF",
            data=pdf_buffer,
            file_name=f"analyse_performances_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            type="primary"
        )

# 7. Exporter/Importer Données
if option == "Exporter/Importer Données":
    st.subheader("Exporter ou Importer les Données")
    add_separator()
    
    uploaded_file = st.file_uploader("Importer un fichier CSV", type="csv")
    if uploaded_file:
        imported_data = pd.read_csv(uploaded_file)
        imported_data['Categorie'] = imported_data['Poids'].apply(categorie_poids)
        imported_data['Performance'] = imported_data['Victoires'] / (imported_data['Victoires'] + imported_data['Defaites']).fillna(0)
        st.session_state.judo_data = pd.concat([st.session_state.judo_data, imported_data], ignore_index=True)
        save_data()
        st.success("Données importées avec succès !", icon="✅")
    
    if not st.session_state.judo_data.empty:
        csv = st.session_state.judo_data.to_csv(index=False)
        st.download_button(
            label="Télécharger les données en CSV",
            data=csv,
            file_name=f"championnat_judo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.warning("Aucune donnée à exporter.")

# 8. Podium (style olympique simplifié avec export PDF)
if option == "Podium":
    st.subheader("Podium Officiel")
    add_separator()
    
    if st.session_state.judo_data.empty:
        st.warning("Aucune donnée disponible pour établir un podium.")
    else:
        st.markdown("### Podium des Équipes et Joueurs")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Équipes")
            top_3_equipes = st.session_state.classement_equipes.sort_values(by='Points_Totaux', ascending=False).head(3)
            if not top_3_equipes.empty:
                podium_colors = ['#FFD700', '#C0C0C0', '#CD7F32']  # Or, Argent, Bronze
                for i, (index, row) in enumerate(top_3_equipes.iterrows()):
                    if i == 0:
                        st.markdown(f"<div style='background-color: {podium_colors[i]}; padding: 10px; text-align: center; border-radius: 5px;'><strong>1er - {row['Equipe']}</strong><br>{row['Points_Totaux']} pts | {row['Victoires_Totaux']} victoires</div>", unsafe_allow_html=True)
                    elif i == 1:
                        st.markdown(f"<div style='background-color: {podium_colors[i]}; padding: 10px; text-align: center; border-radius: 5px;'><strong>2e - {row['Equipe']}</strong><br>{row['Points_Totaux']} pts | {row['Victoires_Totaux']} victoires</div>", unsafe_allow_html=True)
                    elif i == 2:
                        st.markdown(f"<div style='background-color: {podium_colors[i]}; padding: 10px; text-align: center; border-radius: 5px;'><strong>3e - {row['Equipe']}</strong><br>{row['Points_Totaux']} pts | {row['Victoires_Totaux']} victoires</div>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)  # Espacement entre les places
            else:
                st.info("Pas assez d'équipes pour un podium.")
        
        with col2:
            st.markdown("#### Joueurs")
            top_3_joueurs = st.session_state.classement_joueurs.sort_values(by='Points', ascending=False).head(3)
            if not top_3_joueurs.empty:
                for i, (index, row) in enumerate(top_3_joueurs.iterrows()):
                    if i == 0:
                        st.markdown(f"<div style='background-color: {podium_colors[i]}; padding: 10px; text-align: center; border-radius: 5px;'><strong>1er - {row['Joueur']} ({row['Equipe']})</strong><br>{row['Points']} pts | {row['Victoires']} victoires</div>", unsafe_allow_html=True)
                    elif i == 1:
                        st.markdown(f"<div style='background-color: {podium_colors[i]}; padding: 10px; text-align: center; border-radius: 5px;'><strong>2e - {row['Joueur']} ({row['Equipe']})</strong><br>{row['Points']} pts | {row['Victoires']} victoires</div>", unsafe_allow_html=True)
                    elif i == 2:
                        st.markdown(f"<div style='background-color: {podium_colors[i]}; padding: 10px; text-align: center; border-radius: 5px;'><strong>3e - {row['Joueur']} ({row['Equipe']})</strong><br>{row['Points']} pts | {row['Victoires']} victoires</div>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)  # Espacement entre les places
            else:
                st.info("Pas assez de joueurs pour un podium.")
        
        # Bouton d'exportation en PDF pour le podium
        podium_equipes = top_3_equipes[['Equipe', 'Points_Totaux', 'Victoires_Totaux']] if not top_3_equipes.empty else pd.DataFrame(columns=['Equipe', 'Points_Totaux', 'Victoires_Totaux'])
        podium_joueurs = top_3_joueurs[['Joueur', 'Equipe', 'Points', 'Victoires']] if not top_3_joueurs.empty else pd.DataFrame(columns=['Joueur', 'Equipe', 'Points', 'Victoires'])
        combined_podium = pd.concat([podium_equipes, podium_joueurs], axis=1)
        pdf_buffer = export_to_pdf("Podium Officiel - Championnat Marocain de Judo", None, combined_podium)
        st.download_button(
            label="Exporter le Podium en PDF",
            data=pdf_buffer,
            file_name=f"podium_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            type="primary"
        )

# Résumé rapide (version pro)
st.sidebar.markdown("<h2 style='color: #2E86C1; text-align: center;'>Résumé Rapide</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='background-color: #F5F6F5; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)

# Stats principales
if not st.session_state.judo_data.empty:
    total_combats = int(st.session_state.judo_data['Victoires'].sum() + st.session_state.judo_data['Defaites'].sum())
    top_player = st.session_state.classement_joueurs.loc[st.session_state.classement_joueurs['Points'].idxmax()] if not st.session_state.classement_joueurs.empty else None
    top_team = st.session_state.classement_equipes.loc[st.session_state.classement_equipes['Points_Totaux'].idxmax()] if not st.session_state.classement_equipes.empty else None
    
    st.sidebar.markdown("<p style='font-weight: bold; color: #2E86C1;'>Participants</p>", unsafe_allow_html=True)
    st.sidebar.write(f"🏋️‍♂️ Joueurs inscrits : <strong>{len(st.session_state.judo_data)}</strong>", unsafe_allow_html=True)
    st.sidebar.write(f"🤼 Équipes participantes : <strong>{len(st.session_state.classement_equipes)}</strong>", unsafe_allow_html=True)
    st.sidebar.markdown("<hr style='border: 0.5px solid #D3D3D3;'>", unsafe_allow_html=True)
    
    st.sidebar.markdown("<p style='font-weight: bold; color: #2E86C1;'>Activité</p>", unsafe_allow_html=True)
    st.sidebar.write(f"🥊 Total matchs : <strong>{total_combats}</strong>", unsafe_allow_html=True)
    st.sidebar.write(f"🎯 Points attribués : <strong>{int(st.session_state.judo_data['Points'].sum())}</strong>", unsafe_allow_html=True)
    st.sidebar.markdown("<hr style='border: 0.5px solid #D3D3D3;'>", unsafe_allow_html=True)
    
    st.sidebar.markdown("<p style='font-weight: bold; color: #2E86C1;'>Leaders</p>", unsafe_allow_html=True)
    if top_player is not None:
        st.sidebar.write(f"🏅 Meilleur joueur : <strong>{top_player['Joueur']} ({top_player['Points']} pts)</strong>", unsafe_allow_html=True)
    else:
        st.sidebar.write("🏅 Meilleur joueur : <strong>N/A</strong>", unsafe_allow_html=True)
    if top_team is not None:
        st.sidebar.write(f"🥇 Équipe dominante : <strong>{top_team['Equipe']} ({top_team['Points_Totaux']} pts)</strong>", unsafe_allow_html=True)
    else:
        st.sidebar.write("🥇 Équipe dominante : <strong>N/A</strong>", unsafe_allow_html=True)
else:
    st.sidebar.write("Aucune donnée disponible pour le résumé.", unsafe_allow_html=True)

st.sidebar.markdown("</div>", unsafe_allow_html=True)