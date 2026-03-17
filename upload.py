import streamlit as st
import pandas as pd
import geopandas as gpd

def load_page():
    """
       Diese Funktion stellt die „Daten laden“-Seite der Streamlit-App dar.
    
       Zweck der Seite:
       - Hochladen aller für die Anwendung benötigten Dateien
         (Spielerliste, Vereinsliste mit Koordinaten und Regionsdaten als GeoJSON)
       - Einlesen der Dateien in passende Datenstrukturen
       - Speichern der Daten im Streamlit session_state, damit sie
         in anderen Seiten der App weiterverwendet werden können
       - Fehlerausgabe, falls benötigte Dateien fehlen oder falsch hochgeladen werden
    
       Die Seite dient als zentrale Einstiegskomponente der App.
       Erst wenn alle erforderlichen Dateien erfolgreich geladen wurden,
       können die Analyse-Seiten sinnvoll genutzt werden.
    """
   
    #Seitentitel
    st.title("Daten laden")

    #Spielerliste hochladen
    st.subheader("Spielerliste hochladen")
    uploaded_players = st.file_uploader(
        "Excel-Datei (Spielerliste)", 
        type=["xlsx"], 
        key="players_uploader"
    )

    if uploaded_players:
        try:
            df_players = pd.read_excel(uploaded_players)
            #Abspeichern im session_state
            st.session_state["players_df"] = df_players
            st.success("Spielerliste erfolgreich geladen!")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Spielerliste: {e}")

    if "players_df" in st.session_state:
        st.warning("Vorsicht: Alle Zeilen, die keinen Wert in der Spalte Privatspielberechtigt seit besitzen, werden entfernt. Außerdem werden alle Zeilen, in denen kein Abmeldedatum vorhanden ist, obwohl sie nicht mehr im Verein sind, gelöscht.")
        
    #Vereinsliste hochladen
    st.subheader("Vereinsliste hochladen")
    uploaded_vereine = st.file_uploader(
        "Excel-Datei (Vereinsliste)", 
        type=["xlsx"], 
        key="vereine_uploader"
    )

    if uploaded_vereine:
        try:
            df_vereine = pd.read_excel(uploaded_vereine)
            st.session_state["vereine_df"] = df_vereine
            st.success("Vereinsliste erfolgreich geladen!")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Vereinsliste: {e}")
    
    #GeoJSON für Regionen hochladen
    st.subheader("Regionen hochladen")
    uploaded_regionen = st.file_uploader("GeoJSON Datei", type=["geojson", "json"])

    if uploaded_regionen:
        try:
            regions = gpd.read_file(uploaded_regionen)
            st.session_state["regionen_df"] = regions
            st.success("Regionen erfolgreich geladen!")    
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Regionen-Datei: {e}")
    
    # Info-Box
    if "players_df" in st.session_state and "vereins_df" in st.session_state and "regionen_df" in st.session_state:
        st.info("Alle benötigten Dateien wurden erfolgreich geladen! Du kannst jetzt eine Analyse-Seite auswählen.")
        
    else:
        st.warning("Bitte lade alle benötigten Dateien hoch, bevor du Analyse-Seiten aufrufst.")

