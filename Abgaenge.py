
import streamlit as st
import pandas as pd
import plotly.express as px
from cleaning import clean_data


def abgaenge():
    """
    Diese Funktion stellt die Analyse-Seite „Abgänge – Analyse aufnehmender Vereine“ dar.
    
    Zweck der Seite:
    - Analyse, zu welchen Vereinen Spieler den aktuellen Verein verlassen haben
    - Untersuchung der Abgänge nach:
        • aufnehmendem Verein
        • Entwicklungsbereich beim Austritt
        • Abmeldezeitraum
        • Verweildauer im Verein
    - Bereitstellung interaktiver Filter zur gezielten Auswertung
    - Visualisierung der Ergebnisse mit Balkendiagrammen
    
    Es werden ausschließlich Spieler berücksichtigt,
    die nicht mehr im Verein aktiv sind.
    """
    
    #Seitentitel
    st.title("Abgänge – Analyse aufnehmender Vereine")

    # Prüfen, ob Upload vorhanden ist
    if "players_df" not in st.session_state:
        st.error("Bitte zuerst eine Spielerliste hochladen.")
        st.stop()

    # Bereinigung
    df = clean_data(st.session_state["players_df"])

    # Zeilen löschen, die für diese Analyse unbrauchbar sind
    df = df[df["Im Verein"]== "nein"]
    df = df.dropna(subset=[
        "aufnehmender Verein",
        "im Verein bis"
    ])

    # Entwicklungsbereiche definieren
    grundlagen = ["U8", "U9", "U10", "U11"]
    aufbau = ["U12", "U13", "U14", "U15"]
    leistungs = ["U16", "U17", "U18", "U19", "U21/U23"]

    def bereich(u):
        """
        Ordnet eine Altersstufe einem Entwicklungsbereich zu.
        """
        if u in grundlagen:
            return "Grundlagenbereich (U8–U11)"
        elif u in aufbau:
            return "Aufbaubereich (U12–U15)"
        elif u in leistungs:
            return "Leistungsbereich (U16–U23)"
        return None

    # Neue Spalte für den Entwicklungsbereich
    df["Entwicklungsbereich"] = df["im Verein bis"].apply(bereich)


    # Abmeldezeiträume definieren
    def verpflichtungs_kategorie(datum):
        """
        Kategorisiert das Abmeldedatum in feste Zeiträume.
        """
        if pd.isna(datum):
            return None
        if datum >= pd.Timestamp("2021-07-01"):
            return ">= 01.07.2021"
        elif datum <= pd.Timestamp("2017-06-30"):
            return "<= 30.06.2017"
        else:
            return "01.07.2017-30.06.2021"
        
    # Neue Spalte für den Abmeldezeitraum
    df["Abmeldezeitraum"] = df["Abmeldedatum"].apply(
        verpflichtungs_kategorie
    )
    
    # Sidebar Filter
    # -----------------------------------------------------
    st.sidebar.header("Filter")

    entwicklung_options = [
        "Alle",
        "Grundlagenbereich (U8–U11)",
        "Aufbaubereich (U12–U15)",
        "Leistungsbereich (U16–U23)"
    ]
    entwicklung_sel = st.sidebar.selectbox("Entwicklungsbereich:", entwicklung_options)

    zeit_options = [
        "Alle",
        "<= 30.06.2017",
        "01.07.2017-30.06.2021",
        ">= 01.07.2021"
    ]
    zeit_sel = st.sidebar.selectbox("Abmeldezeitraum:", zeit_options)
    
    status_list = ["Alle"] + sorted(df["Status2"].dropna().unique())
    selected_status = st.sidebar.selectbox("Status2:", status_list)

    min_v, max_v = int(df["Tagesdifferenz"].min()), int(df["Tagesdifferenz"].max())
    verweil = st.sidebar.slider("Verweildauer (Tage):", min_v, max_v, (min_v, max_v))
    
    # Jahrgang
    min_y, max_y = int(df["Geburtsjahr"].min()), int(df["Geburtsjahr"].max())
    jahrgang = st.sidebar.slider("Geburtsjahr:", min_y, max_y, (min_y, max_y))
    
    # Mindestanzahl an Spielern pro Verein
    min_spieler = st.sidebar.number_input(
        "Mindestanzahl der Spieler pro Verein (für Verweildauer-Analyse):",
        min_value=1,
        value=1,
        step=1
    )
    # -----------------------------------------------------

    # Filter anwenden
    # -----------------------------------------------------
    df = df[(df["Tagesdifferenz"] >= verweil[0]) & (df["Tagesdifferenz"] <= verweil[1])]

    if entwicklung_sel != "Alle":
        df = df[df["Entwicklungsbereich"] == entwicklung_sel]

    if zeit_sel != "Alle":
        df = df[df["Abmeldezeitraum"] == zeit_sel]
        
    if selected_status != "Alle":
        df = df[df["Status2"].astype(str).str.lower() == selected_status.lower()]
    

    df = df[(df["Geburtsjahr"] >= jahrgang[0]) & (df["Geburtsjahr"] <= jahrgang[1])]
    
    # -----------------------------------------------------


    # Plot 1 – Top 10 aufnehmende Vereine
    # -----------------------------------------------------
    st.subheader("Top 10 – Aufnehmende Vereine")

    if df.empty:
        st.warning("Keine Daten für diese Filterkombination.")
        return

    top10 = df["aufnehmender Verein"].value_counts().head(10).reset_index()
    top10.columns = ["aufnehmender Verein", "Anzahl"]

    # Reihenfolge fixieren
    vereins_order_1 = top10["aufnehmender Verein"].tolist()

    fig = px.bar(
        top10,
        x="aufnehmender Verein",
        y="Anzahl",
        category_orders={"aufnehmender Verein": vereins_order_1},
        color_discrete_sequence=["steelblue"],
        title="Top 10 aufnehmende Vereine"
    )

    fig.update_layout(
        xaxis_title="Aufnehmender Verein",
        yaxis_title="Anzahl Spieler",
        xaxis_tickangle=-45
    )

    st.plotly_chart(fig, use_container_width=True)

    df_top10 = df[df["aufnehmender Verein"].isin(vereins_order_1)]
    df_top10["aufnehmender Verein"] = pd.Categorical(
        df_top10["aufnehmender Verein"],
        categories=vereins_order_1,
        ordered=True
    )

        
    # Zusatzplot 1 – Aufnehmende Vereine × Entwicklungsbereich
    # -----------------------------------------------------
    st.subheader("Aufnehmende Vereine × Entwicklungsbereich")

    df_grouped1 = (
        df_top10
        .groupby(["aufnehmender Verein", "Entwicklungsbereich"])
        .size()
        .reset_index(name="Anzahl")
    )

    fig_group1 = px.bar(
        df_grouped1,
        x="aufnehmender Verein",
        y="Anzahl",
        color="Entwicklungsbereich",
        barmode="group",
        category_orders={"aufnehmender Verein": vereins_order_1},
        title="Spielerabgänge nach Entwicklungsbereich (Top 10)"
    )
    fig_group1.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig_group1, use_container_width=True)
    # -----------------------------------------------------

    # Zusatzplot 2 – Aufnehmende Vereine × Abmeldezeitraum
    # -----------------------------------------------------
    st.subheader("Aufnehmende Vereine × Abmeldezeitraum")

    df_grouped2 = (
        df_top10
        .groupby(["aufnehmender Verein", "Abmeldezeitraum"])
        .size()
        .reset_index(name="Anzahl")
    )

    fig_group2 = px.bar(
        df_grouped2,
        x="aufnehmender Verein",
        y="Anzahl",
        color="Abmeldezeitraum",
        barmode="group",
        category_orders={"aufnehmender Verein": vereins_order_1},
        title="Spielerabgänge nach Abmeldezeitraum (Top 10)"
    )
    fig_group2.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig_group2, use_container_width=True) 
    # -----------------------------------------------------
    # -----------------------------------------------------
    
    # -----------------------------------------------------
    # Histogramm 2 – Durchschnittliche Verweildauer

    st.subheader("Verweildauer – Vereine mit der höchsten durchschnittlichen Verweildauer")
    # Alle Vereine zählen
    verein_counts = df.groupby("aufnehmender Verein").size()
    
    # Nur Vereine mit mindestens min_spieler Spielern
    vereine_fuer_verweildauer = verein_counts[verein_counts >= min_spieler].index
    
    df_verweildauer = df[df["aufnehmender Verein"].isin(vereine_fuer_verweildauer)]
    
    # Durchschnittliche Verweildauer berechnen
    df_verweildauer_agg = (
        df_verweildauer.groupby("aufnehmender Verein")
        .agg(
            Verweildauer_Tage=("Tagesdifferenz", "mean"),
            Spieleranzahl=("Tagesdifferenz", "count")
        )
        .sort_values("Verweildauer_Tage", ascending=False)
        .head(10)
        .reset_index()
    )
    
    
    fig2 = px.bar(
        df_verweildauer_agg,
        x="aufnehmender Verein",
        y="Verweildauer_Tage",
        color_discrete_sequence=["indianred"],
        title="Top 10 Vereine nach durchschnittlicher Verweildauer",
        hover_data={"Verweildauer_Tage": ":.1f", "Spieleranzahl": True}
    )
    
    fig2.update_layout(
        xaxis_title="Aufnehmender Verein",
        yaxis_title="Durchschnittliche Verweildauer (Tage)",
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    # -----------------------------------------------------
    
    # Fußnote
    st.markdown(
        "<sub>Für diese Analysen wurden nur Spieler berücksichtigt, die nicht mehr im Verein spielen. "
        "<br>Davon wurden alle Zeilen ohne "
        "<i>aufnehmender Verein</i> oder <i>im Verein bis</i> entfernt.</sub>",
        unsafe_allow_html=True
    )
