import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestion Restaurant", layout="centered")
st.title("🍽️ Gestion Restaurant - Ratios & Stocks")

sheet_url = st.text_input("Insérez le lien de partage Google Sheets secret ici :")

if sheet_url:
    try:
        csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '&gid=')
        if '/export?format=csv' not in csv_url:
            csv_url = csv_url.split('/edit')[0] + '/export?format=csv'
            
        df = pd.read_csv(csv_url)
        st.success("✅ Données chargées avec succès depuis Google Sheets !")
        st.write("### Vos Ingrédients & Ratios")
        st.dataframe(df)
    except Exception as e:
        st.error("Impossible de lire le fichier. Vérifiez que l'accès est bien configuré sur 'Tous les utilisateurs disposant du lien'.")
else:
    st.info("Veuillez coller votre lien Google Sheets pour afficher vos marges à 34% et vos stocks.")
  
