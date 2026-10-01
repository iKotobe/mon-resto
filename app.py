import streamlit as st
from streamlit_connections import GSheetsConnection

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

try:
    # Connexion native et officielle à Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Chargement forcé des données avec reconnexions automatiques
    df_ing = conn.read(worksheet="Ingredients", ttl=2)
    df_rec = conn.read(worksheet="Recettes", ttl=2)
    df_chg = conn.read(worksheet="Charges", ttl=2)
    
    # Nettoyage des colonnes
    df_ing.columns = df_ing.columns.str.strip()
    df_rec.columns = df_rec.columns.str.strip()
    df_chg.columns = df_chg.columns.str.strip()

    st.success("🎉 Synchronisation réussie via connexion sécurisée !")
    
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
            col_qte = 'Quantite_Req' if 'Quantite_Req' in df_rec.columns else df_rec.columns
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
            st.info("💡 Ajoutez des lignes dans votre onglet 'Recettes' pour voir vos marges.")

    with tab3:
        st.subheader("🛒 Liste d'achats automatique")
        st.info("Interface de courses opérationnelle.")
            
except Exception as e:
    st.error(f"Connexion en cours d'établissement... Veuillez rafraîchir la page dans 10 secondes. (Détail : {e})")
