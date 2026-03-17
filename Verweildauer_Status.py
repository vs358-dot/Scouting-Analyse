import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from cleaning import clean_data

def verweildauer_status():
    """
        Diese Funktion stellt die Analyse-Seite „Verweildauer × Status“ dar.
        
        Zweck der Seite:
        - Analyse der Verweildauer von Spielern im Verein
          in Abhängigkeit vom aktuellen Spielerstatus
        - Bereitstellung interaktiver Filter (Im Verein, Eintrittsalter, Jahrgang)
        - Visualisierung der Daten mittels Histogramm und Scatterplot
        - Optionale Hervorhebung von Profiliga-Spielern sowie Anzeige von Mittelwerten
        
        Die Funktion verwendet die bereinigte Spielerliste,
        die zuvor in der Streamlit-App hochgeladen wurde.
    """

    #Seitentitel
    st.title("Verweildauer × Status")

    # Abbruch, falls noch keine Spielerliste vorhanden ist
    if "players_df" not in st.session_state:
        st.error("Bitte zuerst eine Spielerliste hochladen.")
        st.stop()

    # Bereinigung
    df = clean_data(st.session_state["players_df"])

    # ---------------------------------------------------------
    # Sidebar-Filter
    st.sidebar.header("Filter")

    # Im Verein
    verein_list = ["Alle"] + sorted(df["Im Verein"].dropna().unique())
    selected_verein = st.sidebar.selectbox("Im Verein:", verein_list)

    # Im Verein seit → als Dropdown
    stufen_order = ["U08","U09","U10","U11","U12","U13","U14","U15","U16","U17","U19","U21/U23"]
    selected_stufe = st.sidebar.selectbox("Im Verein seit:", ["Alle"] + stufen_order)

    # Jahrgang
    min_y, max_y = int(df["Geburtsjahr"].min()), int(df["Geburtsjahr"].max())
    jahrgang = st.sidebar.slider("Geburtsjahr:", min_y, max_y, (min_y, max_y))

    # Einheit
    y_unit = st.sidebar.selectbox("Verweildauer anzeigen in:", ["Tage", "Monate", "Jahre"])

    # Optionen
    profiliga_separat = st.sidebar.checkbox("Profiliga-Spieler als Stern anzeigen")
    mittelwertpunkte = st.sidebar.checkbox("Mittelwertpunkte anzeigen")
    # ---------------------------------------------------------
    

    # Zeilen mit fehlenden Werten löschen
    df = df.dropna(subset=["Geburtsjahr", "Status", "Im Verein"])

    # ---------------------------------------------------------
    # Filter anwenden
    if selected_verein != "Alle":
        df = df[df["Im Verein"].str.lower() == selected_verein.lower()]

    if selected_stufe != "Alle":
        df = df[df["im Verein seit"].astype(str).str.lower() == selected_stufe.lower()]

    df = df[(df["Geburtsjahr"] >= jahrgang[0]) & (df["Geburtsjahr"] <= jahrgang[1])]
    # ---------------------------------------------------------
    
    # Umrechnung der Tagesdifferenz in die gewünschte Einheit 
    if y_unit == "Monate":
        df["Verweildauer"] = df["Tagesdifferenz"] / 30
    elif y_unit == "Jahre":
        df["Verweildauer"] = df["Tagesdifferenz"] / 365
    else:
        df["Verweildauer"] = df["Tagesdifferenz"]
        
    # Vollständiger Name für Hover-Anzeige
    df["Name"] = df["Vorname"].astype(str) + " " + df["Nachname"].astype(str)


    # Status-Kategorien für saubere X-Achse
    df["Status"] = df["Status"].astype(str).str.strip()
    df["Status"] = pd.Categorical(df["Status"],
                                  categories=sorted(df["Status"].unique()),
                                  ordered=True)

    # ---------------------------------------------------------
    # Histogramm 
    st.subheader("Histogramm – Häufigkeit pro Status")

    hist = px.histogram(
        df,
        x="Status",
        color_discrete_sequence=["steelblue"]
    )
    st.plotly_chart(hist, use_container_width=True)
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # Scatterplot
    st.subheader("Scatterplot – Verweildauer nach Status")

    # Standarddarstellung ohne Trennung von Profiliga-Spielern
    if not profiliga_separat:
        fig = px.scatter(
            df,
            x="Status",
            y="Verweildauer",
            hover_name="Name",
            color_discrete_sequence=["green"]
        )
    # Trennung in Profiliga- und Nicht-Profiliga-Spieler
    else:
        nicht_profi = df[
            (~df["Status2"].astype(str).str.contains("Profiliga", na=False)) &
            (df["Profi geworden"] == "nein")
        ]
        
        profi = df[
            (df["Status2"].astype(str).str.contains("Profiliga", na=False)) |
            (df["Profi geworden"] == "ja")
        ]

        fig = px.scatter(
            nicht_profi,
            x="Status",
            y="Verweildauer",
            hover_name="Name",
            color_discrete_sequence=["green"]
        )
        
        # Sterne für Profiliga-Spieler
        fig.add_scatter(
            x=profi["Status"],
            y=profi["Verweildauer"],
            mode="markers",
            marker=dict(symbol="star", size=10, color="red"),
            hoverinfo="text",
            hovertext=[
                f"{r['Name']}<br>{y_unit}: {r['Verweildauer']:.1f}"
                for _, r in profi.iterrows()
            ]
        )

    # Mittelwertpunkte (optional)
    if mittelwertpunkte:
        mean_df = df.groupby("Status")["Verweildauer"].mean().reset_index()

        fig.add_scatter(
            x=mean_df["Status"],
            y=mean_df["Verweildauer"],
            mode="markers",
            marker=dict(symbol="x", size=12, color="orange"),
            name="Mittelwert"
        )

    fig.update_layout(
        xaxis_title="Status",
        yaxis_title=f"Verweildauer ({y_unit})",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)
    # ---------------------------------------------------------
    
    # Fußnote
    st.markdown(
        "<sub>Für diese Analysen wurden alle Zeilen, die einen der folgenden Werte nicht enthalten, entfernt:<br>"
        "Geburtsjahr, Im Verein, Status.<br>"
        "Als Profispieler werden alle Spieler gezählt, deren Status2 Profiliga ist oder für die Profi geworden = ja gilt.</sub>",
        unsafe_allow_html=True
    )
