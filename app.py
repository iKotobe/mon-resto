import streamlit as st
import pandas as pd

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

# Lecture simplifiée de l'identifiant
if "RESTAURANT_SHEET_URL" in st.secrets:
    sheet_id = st.secrets["RESTAURANT_SHEET_URL"]
else:
    sheet_id = st.text_input("🔑 Entrez l'identifiant unique de votre Google Sheet :", type="password")

if not sheet_id:
    st.info("👋 Veuillez configurer l'identifiant Google Sheets pour activer le tableau de bord.")
else:
    try:
        # Nettoyage automatique au cas où l'utilisateur met le lien entier
        id_propre = sheet_id.strip()
        if "spreadsheets/d/" in id_propre:
            id_propre = id_propre.split("spreadsheets/d/")[1].split("/")[0]

        @st.cache_data(ttl=2)
        def load_sheet(sheet_name):
            url = f"https://google.com{id_propre}/export?format=csv&sheet={sheet_name}"
            return pd.read_csv(url)

        # Chargement automatique de vos 3 onglets configurés
        df_ing = load_sheet("Ingredients")
        df_rec = load_sheet("Recettes")
        df_chg = load_sheet("Charges")
        
        # Nettoyage automatique des noms de colonnes
        df_ing.columns = df_ing.columns.str.strip()
        df_rec.columns = df_rec.columns.str.strip()
        df_chg.columns = df_chg.columns.str.strip()

        df_ing = df_ing.fillna({"Stock_Actuel": 0, "Stock_Alerte": 0, "Fournisseur": "Inconnu", "Prix_Achat": 0})

        # CRÉATION DES ONGLETS SUR VOTRE ÉCRAN MOBILE
        tab1, tab2, tab3 = st.tabs(["📊 Rentabilité", "🍳 Recettes & Marges", "🛒 Courses"])

        # TAB 1 : RENTABILITÉ GLOBALE
        with tab1:
            st.subheader("📈 Bilan Financier du Mois")
            ca_ttc = st.number_input("Chiffre d'Affaires Mensuel TTC (€) :", min_value=0.0, value=10000.0, step=500.0)
            
            ca_ht = ca_ttc / 1.10
            tva_collectee = ca_ttc - ca_ht
            cout_matiere_estimé = ca_ht * 0.66
            marge_brute_estimée = ca_ht * 0.34
            
            if not df_chg.empty and 'Type' in df_chg.columns and 'Montant_Mensuel' in df_chg.columns:
                total_charges_fixes = float(df_chg[df_chg['Type'].astype(str).str.lower() == 'fixe']['Montant_Mensuel'].sum())
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

        # TAB 2 : RECETTES & MARGES
        with tab2:
            st.subheader("🍳 Analyse Fiches Techniques")
            if not df_rec.empty and 'Plat' in df_rec.columns:
                # S'adapte à l'orthographe exacte de vos colonnes
                col_qte = 'Quantite_Req' if 'Quantite_Req' in df_rec.columns else 'Quantite_Requise'
                col_px_vente = 'Prix_Vente_TTC' if 'Prix_Vente_TTC' in df_rec.columns else df_rec.columns[-1]
                
                prix_dict = dict(zip(df_ing['Ingredient'].astype(str).str.strip(), df_ing['Prix_Achat'].astype(float)))
                
                for plat in df_rec['Plat'].unique():
                    df_plat = df_rec[df_rec['Plat'] == plat]
                    cout_plat = 0.0
                    
                    for _, row in df_plat.iterrows():
                        ing = str(row['Ingredient']).strip()
                        qte = float(row[col_qte])
                        cout_plat += qte * prix_dict.get(ing, 0.0)
                    
                    try:
                        px_vente_ttc = float(df_plat[col_px_vente].iloc[0])
                    except:
                        px_vente_ttc = 0.0
                        
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
                st.info("💡 Ajoutez des recettes complètes dans votre Sheet pour voir vos marges.")

        # TAB 3 : LISTE DE COURSES
        with tab3:
            st.subheader("🛒 Liste d'achats automatique")
            if 'Stock_Actuel' in df_ing.columns and 'Stock_Alerte' in df_ing.columns:
                df_ing['Stock_Actuel'] = pd.to_numeric(df_ing['Stock_Actuel'], errors='coerce').fillna(0)
                df_ing['Stock_Alerte'] = pd.to_numeric(df_ing['Stock_Alerte'], errors='coerce').fillna(0)
                
                df_alerte = df_ing[df_ing['Stock_Actuel'] < df_ing['Stock_Alerte']]
                
                if df_alerte.empty:
                    st.success("🎉 Stocks parfaits ! Aucune commande nécessaire.")
                else:
                    liste_texte = "📋 COMMANDES RESTAURANT :\n"
                    for _, row in df_alerte.iterrows():
                        manquant = float(row['Stock_Alerte']) - float(row['Stock_Actuel'])
                        fourn = row['Fournisseur'] if 'Fournisseur' in df_ing.columns else "Général"
                        liste_texte += f"- {row['Ingredient']} : {manquant:.1f}\n"
                        st.write(f"❌ **{row['Ingredient']}** ({fourn}) : reste {row['Stock_Actuel']} (Alerte: {row['Stock_Alerte']})")
                    
                    st.text_area("Texte à copier :", value=liste_texte, height=120)
                
    except Exception as e:
        st.error(f"Erreur de lecture : {e}. Assurez-vous que l'onglet 'Ingredients' contient bien du contenu.")
