import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pilote Resto", page_icon="🍽️", layout="wide")

st.title("🍽️ Pilote Resto Pro")
st.caption("Objectif : 66% Coût Matière Max | 34% Marge Brute Min")

sheet_id = st.text_input("🔑 Entrez l'identifiant unique de votre Google Sheet :", type="password")

if not sheet_id:
    st.info("👋 Veuillez coller l'identifiant de votre Google Sheet.")
else:
    try:
        # Nettoyage de l'identifiant au cas où
        clean_id = sheet_id.strip()
        if "spreadsheets/d/" in clean_id:
            clean_id = clean_id.split("spreadsheets/d/")[1].split("/")[0]

        # FONCTION DE LECTURE UNIVERSELLE GOOGLE SHEETS
        def load_sheet(sheet_name):
            url = f"https://google.com{clean_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
            return pd.read_csv(url)

        # Chargement des données
        df_ing = load_sheet("Ingredients")
        df_rec = load_sheet("Recettes")
        df_chg = load_sheet("Charges")
        
        # Nettoyage des colonnes
        df_ing.columns = df_ing.columns.str.strip()
        df_rec.columns = df_rec.columns.str.strip()
        df_chg.columns = df_chg.columns.str.strip()

        st.success("🎉 Synchronisation réussie !")
        
        tab1, tab2, tab3 = st.tabs(["📊 Rentabilité", "🍳 Recettes & Marges", "🛒 Courses"])

        with tab1:
            st.subheader("📈 Bilan Financier du Mois")
            ca_ttc = st.number_input("Chiffre d'Affaires Mensuel TTC (€) :", min_value=0.0, value=10000.0, step=500.0)
            ca_ht = ca_ttc / 1.10
            cout_matiere_estimé = ca_ht * 0.66
            marge_brute_estimée = ca_ht * 0.34
            
            if not df_chg.empty and 'Type' in df_chg.columns and 'Montant_Mensuel' in df_chg.columns:
                total_charges_fixes = float(df_chg[df_chg['Type'].astype(str).str.lower() == 'fixe']['Montant_Mensuel'].sum())
            else:
                total_charges_fixes = 0.0
                
            benefice_net = marge_brute_estimée - total_charges_fixes
            st.metric("CA Hors Taxes", f"{ca_ht:.2f} €")
            st.metric("Coût Matière Max (66%)", f"{cout_matiere_estimé:.2f} €")
            st.metric("Frais Fixes", f"{total_charges_fixes:.2f} €")
            if benefice_net >= 0:
                st.success(f"Bénéfice Net : +{benefice_net:.2f} €")
            else:
                st.error(f"Déficit : {benefice_net:.2f} €")

        with tab2:
            st.subheader("🍳 Analyse Fiches Techniques")
            if not df_rec.empty and 'Plat' in df_rec.columns:
                col_qte = 'Quantite_Req' if 'Quantite_Req' in df_rec.columns else df_rec.columns[2]
                prix_dict = dict(zip(df_ing['Ingredient'].astype(str).str.strip(), df_ing['Prix_Achat'].astype(float)))
                
                for plat in df_rec['Plat'].unique():
                    df_plat = df_rec[df_rec['Plat'] == plat]
                    cout_plat = 0.0
                    for _, row in df_plat.iterrows():
                        ing = str(row['Ingredient']).strip()
                        qte = float(row[col_qte])
                        cout_plat += qte * prix_dict.get(ing, 0.0)
                    
                    with st.expander(f"🍽️ {plat}"):
                        st.write(f"Coût ingrédients : {cout_plat:.2f} €")
            else:
                st.info("💡 Ajoutez des lignes dans l'onglet 'Recettes' pour voir vos marges.")

        with tab3:
            st.subheader("🛒 Liste d'achats automatique")
            st.success("🎉 Interface connectée.")
                
    except Exception as e:
        st.error(f"Erreur d'accès : {e}. Vérifiez que votre Google Sheet est bien partagé en mode 'Tous les utilisateurs disposant du lien'.")     
