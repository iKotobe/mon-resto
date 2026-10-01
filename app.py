import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pilote Resto", page_icon="🍽️", layout="wide")

st.title("🍽️ Pilote Resto Pro")
st.caption("Objectif : 66% Coût Matière Max | 34% Marge Brute Min")

# Demande directement l'identifiant unique du tableur
sheet_id = st.text_input("🔑 Entrez l'identifiant unique de votre Google Sheet :", type="password")

if not sheet_id:
    st.info("👋 Veuillez coller l'identifiant de votre Google Sheet pour activer le tableau de bord.")
    st.markdown("""
    **Où le trouver ?**  
    Dans le lien de votre Google Sheet, c'est le long texte situé juste après `/d/`.  
    *Exemple : si votre lien est `.../d/1A2B3C4D5E6F/edit`, votre identifiant est `1A2B3C4D5E6F`*
    """)
else:
    try:
        # Nettoyage automatique au cas où l'utilisateur colle le lien entier malgré tout
        id_propre = sheet_id.strip()
        if "spreadsheets/d/" in id_propre:
            id_propre = id_propre.split("spreadsheets/d/")[1].split("/")[0]

        @st.cache_data(ttl=2)
        def load_sheet(sheet_name):
            url = f"https://google.com{id_propre}/export?format=csv&sheet={sheet_name}"
            return pd.read_csv(url)

        # Chargement des données
        df_ing = load_sheet("Ingredients")
        df_rec = load_sheet("Recettes")
        df_chg = load_sheet("Charges")
        
        df_ing.columns = df_ing.columns.str.strip()
        df_rec.columns = df_rec.columns.str.strip()
        df_chg.columns = df_chg.columns.str.strip()

        df_ing = df_ing.fillna({"Stock_Actuel": 0, "Stock_Alerte": 0, "Fournisseur": "Inconnu", "Prix_Achat": 0})

        st.success("🎉 Synchronisation réussie !")
        
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

            st.metric("CA Hors Taxes", f"{ca_ht:.2f} €", f"TVA: {tva_collectee:.2f} €")
            st.metric("Coût Matière Max (66%)", f"{cout_matiere_estimé:.2f} €")
            st.metric("Frais Fixes", f"{total_charges_fixes:.2f} €")
            
            if benefice_net >= 0:
                st.success(f"Bénéfice Net Estimé : +{benefice_net:.2f} €")
            else:
                st.error(f"Déficit Net Estimé : {benefice_net:.2f} €")

        # TAB 2 : RECETTES & MARGES
        with tab2:
            st.subheader("🍳 Analyse Fiches Techniques")
            if not df_rec.empty and 'Plat' in df_rec.columns:
                prix_dict = dict(zip(df_ing['Ingrédient'].astype(str).str.strip(), df_ing['Prix_Achat'].astype(float)))
                
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
                st.info("💡 Ajoutez des recettes dans votre Google Sheet pour voir vos marges.")

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
                        liste_texte += f"- {row['Ingrédient']} : {manquant:.1f} {row['Unité']}\n"
                        st.write(f"❌ **{row['Ingrédient']}** : reste {row['Stock_Actuel']} (Alerte: {row['Stock_Alerte']})")
                    
                    st.text_area("Texte à envoyer :", value=liste_texte, height=120)
                
    except Exception as e:
        st.error(f"Erreur d'accès : {e}. Assurez-vous que l'onglet de votre Google Sheet s'appelle bien 'Ingredients' (sans accent) et qu'il est partagé en mode 'Tous les utilisateurs disposant du lien'.")
        
