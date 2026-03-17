import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from cleaning import clean_data

def verweildauer_quartal():
    """
    Diese Funktion stellt die Analyse-Seite „Verweildauer × Quartal“ dar.
    
    Zweck der Seite:
    - Analyse der Verweildauer von Spielern im Verein in Abhängigkeit
      vom Eintrittsquartal (Q1–Q4)
    - Vergleich der Anzahl und prozentualen Verteilung der Spieler
      je Eintrittsquartal
    - Untersuchung der Verweildauer mittels Scatterplot
    - Optionale Hervorhebung von Profiliga-Spielern
      sowie Anzeige der durchschnittlichen Verweildauer pro Quartal
    
    Die Seite ist Teil einer Streamlit-App und verwendet die zuvor
    hochgeladene und bereinigte Spielerliste.
    """

    #Titelseite
    st.title("Verweildauer × Quartal")


    # Datei prüfen
    if "players_df" not in st.session_state:
        st.error("Bitte zuerst eine Spielerliste hochladen.")
        st.stop()

    # Bereinigung
    df = clean_data(st.session_state["players_df"])


    # Zeilen ohne Quartal, Privatspielberechtigt seit oder Abmeldedatum entfernen
    df = df.dropna(subset=["Quartal", "Privatspielberechtigt seit", "Abmeldedatum"])
    df["Privatspielberechtigt seit"] = pd.to_datetime(df["Privatspielberechtigt seit"], errors="coerce")
    df["Abmeldedatum"] = pd.to_datetime(df["Abmeldedatum"], errors="coerce")
    df = df.dropna(subset=["Privatspielberechtigt seit", "Abmeldedatum"])

    # ------------------------------------
    # Sidebar Filter
    st.sidebar.header("Filter")

    # Im Verein Dropdown
    verein_list = ["Alle"] + sorted(df["Im Verein"].dropna().unique())
    selected_verein = st.sidebar.selectbox("Im Verein:", verein_list)
    if selected_verein != "Alle":
        df = df[df["Im Verein"].astype(str).str.lower() == selected_verein.lower()]

    # Jahrgang Slider
    min_y, max_y = int(df["Geburtsjahr"].min()), int(df["Geburtsjahr"].max())
    jahrgang = st.sidebar.slider("Geburtsjahr:", min_y, max_y, (min_y, max_y))
    df = df[(df["Geburtsjahr"] >= jahrgang[0]) & (df["Geburtsjahr"] <= jahrgang[1])]

    # Verweildauer Einheit
    y_unit = st.sidebar.selectbox("Verweildauer anzeigen in:", ["Tage", "Monate", "Jahre"])

    # Profiliga Checkbox
    profiliga_separat = st.sidebar.checkbox("Profiliga-Spieler als Stern anzeigen")

    # Mittelwertpunkte Checkbox
    mittelwertpunkte = st.sidebar.checkbox("Mittelwertpunkte anzeigen")
    # ------------------------------------
    
    # Verweildauer umrechnen
    if y_unit == "Monate":
        df["Verweildauer"] = df["Tagesdifferenz"] / 30
    elif y_unit == "Jahre":
        df["Verweildauer"] = df["Tagesdifferenz"] / 365
    else:
        df["Verweildauer"] = df["Tagesdifferenz"]

    df["Name"] = df["Vorname"].astype(str) + " " + df["Nachname"].astype(str)

    # Spalten nebeneinander für Diagramme
    quartal_order = ["Q1", "Q2", "Q3", "Q4"]
    col1, col2 = st.columns(2)

    #Visualisierungen
    # ------------------------------------    
    # Histogramm
    with col1:
        st.subheader("Histogramm – Anzahl Spieler pro Quartal")
        hist = px.histogram(
            df,
            x="Quartal",
            category_orders={"Quartal": quartal_order},
            color_discrete_sequence=["steelblue"]
        )
        st.plotly_chart(hist, use_container_width=True)

    # Kreisdiagramm (Pie Chart)
    with col2:
        st.subheader("Prozentuale Verteilung pro Quartal")
        pie_df = df["Quartal"].value_counts(normalize=True).reset_index()
        pie_df.columns = ["Quartal", "Anteil"]
        pie = px.pie(
            pie_df,
            names="Quartal",
            values="Anteil",
            hole=0.3,  # optional: Donut
            title="Prozentuale Verteilung"
        )
        pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(pie, use_container_width=True)


    # Scatterplot – Verweildauer
    st.subheader("Scatterplot – Verweildauer pro Quartal")

    if not profiliga_separat:
        fig = px.scatter(
            df,
            x="Quartal",
            y="Verweildauer",
            hover_name="Name",
            color_discrete_sequence=["green"]
        )
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
            x="Quartal",
            y="Verweildauer",
            hover_name="Name",
            color_discrete_sequence=["green"]
        )

        fig.add_scatter(
            x=profi["Quartal"],
            y=profi["Verweildauer"],
            mode="markers",
            marker=dict(symbol="star", size=10, color="red"),
            hoverinfo="text",
            hovertext=[f"{r['Name']}<br>{y_unit}: {r['Verweildauer']:.1f}" for _, r in profi.iterrows()]
        )

    # Mittelwertpunkte optional
    if mittelwertpunkte:
        mean_df = df.groupby("Quartal")["Verweildauer"].mean().reset_index()
        fig.add_scatter(
            x=mean_df["Quartal"],
            y=mean_df["Verweildauer"],
            mode="markers",
            marker=dict(symbol="x", size=12, color="orange"),
            name="Mittelwert"
        )

    fig.update_layout(
        xaxis_title="Quartal",
        yaxis_title=f"Verweildauer ({y_unit})",
        showlegend=False
    )
    fig.update_xaxes(categoryorder="array", categoryarray=quartal_order)

    st.plotly_chart(fig, use_container_width=True)
    # ------------------------------------
    
    # Fußnote
    st.markdown(
        "<sub>Für diese Analysen wurden alle Zeilen, die einen der folgenden Werte nicht enthalten, entfernt:<br>"
        "Geburtsjahr, Im Verein, Quartal.<br>"
        "Als Profispieler werden alle Spieler gezählt, deren Status2 Profiliga ist oder für die Profi geworden = ja gilt.</sub>",
        unsafe_allow_html=True
    )
