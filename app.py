import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Pilote Resto", page_icon="🍽️", layout="wide")

st.markdown("""
<style>
    .reportview-container .main .block-container{ max-width: 600px; padding-top: 1rem; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #FF4B4B; color: white; }
    .metric-box { padding: 15px; border-radius: 10px; background-color: #f0f2f6; margin-bottom: 10px; text-align: center; }
</style>
""", unsafe_allow_html=True)

st.title("🍽️ Pilote Resto Pro")
st.caption("Objectif : 66% Coût Matière Max | 34% Marge Brute Min")

# Lecture simplifiée du lien
if "RESTAURANT_SHEET_URL" in st.secrets:
    sheet_url = st.secrets["RESTAURANT_SHEET_URL"]
else:
    sheet_url = st.text_input("🔗 Lien secret Google Sheets :", type="password")

if not sheet_url:
    st.info("👋 Veuillez coller votre lien Google Sheets pour activer le tableau de bord.")
else:
    try:
        # Cette formule magique extrait l'identifiant unique du lien à coup sûr
        if "/d/" in sheet_url:
            sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        else:
            sheet_id = sheet_url

        @st.cache_data(ttl=5)
        def load_sheet(sheet_name):
            # Construction propre du lien d'export CSV pour Google Sheets
            url = f"https://google.com{sheet_id}/export?format=csv&sheet={sheet_name}"
            return pd.read_csv(url)

        # Chargement forcé des données
        df_ing = load_sheet("Ingredients")
        df_rec = load_sheet("Recettes")
        df_chg = load_sheet("Charges")
        
        # Nettoyage des colonnes
        df_ing.columns = df_ing.columns.str.strip()
        df_rec.columns = df_rec.columns.str.strip()
        df_chg.columns = df_chg.columns.str.strip()

        # Remplacement des valeurs vides par sécurité
        df_ing = df_ing.fillna({"Stock_Actuel": 0, "Stock_Alerte": 0, "Fournisseur": "Inconnu", "Prix_Achat": 0})

        st.success("🎉 Synchronisation réussie !")
        
        # Affichage des onglets de contrôle
        tab1, tab2, tab3 = st.tabs(["📊 Rentabilité", "🍳 Recettes & Marges", "🛒 Courses"])

        # TAB 1 : RENTABILITÉ GLOBALE
        with tab1:
            st.subheader("📈 Bilan Financier du Mois")
            ca_ttc = st.number_input("Chiffre d'Affaires Mensuel TTC (€) :", min_value=0.0, value=10000.0, step=500.0)
            
            ca_ht = ca_ttc / 1.10
            tva_collectee = ca_ttc - ca_ht
            cout_matiere_estimé = ca_ht * 0.66
            marge_brute_estimée = ca_ht * 0.34
            
            # Gestion si l'onglet charges est encore vide
            if not df_chg.empty and 'Type' in df_chg.columns and 'Montant_Mensuel' in df_chg.columns:
                total_charges_fixes = float(df_chg[df_chg['Type'].str.lower() == 'fixe']['Montant_Mensuel'].sum())
            else:
                total_charges_fixes = 0.0
                
            benefice_net = marge_brute_estimée - total_charges_fixes
            seuil_rentabilite_ttc = (total_charges_fixes / 0.34) * 1.10 if total_charges_fixes > 0 else 0.0

            st.markdown(f"<div class='metric-box'><h3>CA Hors Taxes</h3><h2>{ca_ht:.2f} €</h2><small>TVA : {tva_collectee:.2f} €</small></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-box'><h3>Coût Matière Max (66%)</h3><h2>{cout_matiere_estimé:.2f} €</h2></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-box'><h3>Frais Fixes</h3><h2>{total_charges_fixes:.2f} €</h2></div>", unsafe_allow_html=True)
            
            if benefice_net >= 0:
                st.markdown(f"<div class='metric-box' style='background-color: #d4edda; color: #155724;'><h3>Bénéfice Net</h3><h2>+{benefice_net:.2f} €</h2></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='metric-box' style='background-color: #f8d7da; color: #721c24;'><h3>Déficit Net</h3><h2>{benefice_net:.2f} €</h2></div>", unsafe_allow_html=True)
                
            st.info(f"📍 Objectif CA Minimum : **{seuil_rentabilite_ttc:.2f} € TTC**")

        # TAB 2 : RECETTES & MARGES
        with tab2:
            st.subheader("🍳 Analyse Fiches Techniques")
            if not df_rec.empty and 'Plat' in df_rec.columns:
                prix_dict = dict(zip(df_ing['Ingrédient'].str.strip(), df_ing['Prix_Achat']))
                
                for plat in df_rec['Plat'].unique():
                    df_plat = df_rec[df_rec['Plat'] == plat]
                    cout_plat = 0.0
                    
                    for _, row in df_plat.iterrows():
                        ing = str(row['Ingrédient']).strip()
                        qte = float(row['Quantité_Requise'])
                        cout_plat += qte * prix_dict.get(ing, 0.0)
                    
                    px_vente_ttc = float(df_plat['Prix_Vente_TTC'].iloc[0]) if 'Prix_Vente_TTC' in df_plat.columns else 0.0
                    px_vente_ht = px_vente_ttc / 1.10
                    food_cost_ratio = (cout_plat / px_vente_ht) * 100 if px_vente_ht > 0 else 0
                    prix_conseille_ttc = (cout_plat / 0.66) * 1.10
                    
                    with st.expander(f"🍽️ {plat}"):
                        st.write(f"Coût ingrédients : {cout_plat:.2f} €")
                        st.write(f"Prix actuel : {px_vente_ttc:.2f} € TTC")
                        if food_cost_ratio > 66:
                            st.markdown(f"🔴 **Food Cost : {food_cost_ratio:.1f}%** (> 66%)")
                            st.warning(f"Augmentez le prix à : **{prix_conseille_ttc:.2f} € TTC**")
                        else:
                            st.markdown(f"🟢 **Food Cost : {food_cost_ratio:.1f}%** (Marge OK)")
            else:
                st.info("💡 Ajoutez vos premières recettes dans l'onglet 'Recettes' pour voir vos marges.")

        # TAB 3 : LISTE DE COURSES
        with tab3:
            st.subheader("🛒 Liste d'achats automatique")
            if 'Stock_Actuel' in df_ing.columns and 'Stock_Alerte' in df_ing.columns:
                df_alerte = df_ing[df_ing['Stock_Actuel'].astype(float) < df_ing['Stock_Alerte'].astype(float)]
                
                if df_alerte.empty:
                    st.success("🎉 Stocks parfaits ! Aucune commande nécessaire.")
                else:
                    liste_texte = "📋 COMMANDES RESTAURANT :\n"
                    for _, row in df_alerte.iterrows():
                        manquant = float(row['Stock_Alerte']) - float(row['Stock_Actuel'])
                        liste_texte += f"- {row['Ingrédient']} ({row['Fournisseur']}) : {manquant:.1f} {row['Unité']}\n"
                        st.write(f"❌ **{row['Ingrédient']}** ({row['Fournisseur']}) : reste {row['Stock_Actuel']} (Alerte: {row['Stock_Alerte']})")
                    
                    st.text_area("Texte à copier pour SMS / WhatsApp :", value=liste_texte, height=120)
            else:
                st.warning("Vérifiez que les colonnes 'Stock_Actuel' et 'Stock_Alerte' existent dans votre onglet Ingredients.")
                
    except Exception as e:
        st.error(f"Erreur de lecture : {e}. Vérifiez que l'accès général de votre Google Sheet est bien sur 'Tous les utilisateurs disposant du lien'.")
