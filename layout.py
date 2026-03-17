import streamlit as st

# Seiten importieren
from upload import load_page
from Verweildauer_Altersgruppe import verweildauer_altersgruppe
from Verweildauer_Status import verweildauer_status
from Zugaenge import zugaenge
from Abgaenge import abgaenge  
from Quartal import verweildauer_quartal
from Entwicklung import entwicklung
#from Karte1 import create_transfer_map
#from streamlit_folium import st_folium



st.set_page_config(
    page_title="FCA Scouting Analyse",
    layout="wide"
)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Seite auswählen:",
    (
        "Startseite – Datei laden",
        "Zugänge – Abgebende Vereine",
        "Abgänge – Aufnehmende Vereine",
        "Verweildauer × Altersgruppe",
        "Verweildauer × Status",
        "Verweildauer × Quartal",
        "Spielerentwicklung",
        "Interaktive Karte"
    )
)

# Seitenlogik
if page == "Startseite – Datei laden":
    load_page()

elif page == "Verweildauer × Altersgruppe":
    verweildauer_altersgruppe()

elif page == "Verweildauer × Status":
    verweildauer_status()

elif page == "Zugänge – Abgebende Vereine":
    zugaenge()

elif page == "Abgänge – Aufnehmende Vereine":   
    abgaenge()
    
elif page == "Verweildauer × Quartal":
    verweildauer_quartal()

elif page == "Spielerentwicklung":
    entwicklung()
    
#elif page == "Interaktive Karte":
#    m = create_transfer_map()
#    if m:
#        st_folium(m, width=None, height=800)
