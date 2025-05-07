import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime
from pathlib import Path
from mongo import load_data, save_data
from PIL import Image

# ----------------------------
# Initialisierung & Laden
# ----------------------------
data = load_data()
image = Image.open("logo.png")
# ----------------------------
# Navigation
# ----------------------------
with st.sidebar:
    st.title("Bücher App")
    st.image(image, width=120)
    st.markdown("---")

    # Option Menu
    page = option_menu(
        menu_title="Navigation",  # Kein Titel
        options=["Wunschliste", "Übersicht", "Details", "Statistik"],
        icons=["heart", "book", "search", "bar-chart"],  # Bootstrap Icons
        menu_icon="cast",  # Optionales Icon
        default_index=0,
    )

    st.markdown("---")
    st.markdown("© **ROC**, 2025")
# ----------------------------
# Wunschliste
# ----------------------------
if page == "Wunschliste":
    st.header("Wunschliste")
    with st.form("add_wish"):
        title = st.text_input("Buchtitel")
        author = st.text_input("Autor")
        genre = st.selectbox(
            "Genre auswählen oder eingeben",
            options=[
            "Roman",
            "Krimi & Thriller",
            "Fantasy & Science-Fiction",
            "Historisch",
            "Liebesgeschichte",
            "Abenteuer",
            "Horror & Mystery",
            "Biografie & Memoiren",
            "Sachbuch",
            "Ratgeber",
            "Kinder- & Jugendbuch",
            "Poesie & Kurzgeschichten",
            "Gesellschaft & Politik",
            "Spiritualität & Religion",
            "Klassiker",
            "Anderes"
            ]
        )
        nationality = st.text_input("Nationalität des Autors")
        submit = st.form_submit_button("Zur Wunschliste hinzufügen")

        if submit and title:
            data["wishlist"].append({
                "Titel": title,
                "Autor": author,
                "Genre": genre,
                "Wunschdatum": datetime.now().strftime("%Y-%m-%d"),
                "Status": "offen",
                "Nationalität": nationality
            })
            save_data(data)
            st.success("Buch hinzugefügt!")

    st.subheader("Deine Wunschliste")
    for i, book in enumerate(data["wishlist"]):
        if book["Status"] == "offen":
            st.markdown(f"**{book['Titel']}** von {book['Autor']} ({book['Genre']})")
        
        col1, col2, col3 = st.columns([2, 2, 1])  # optional: Verhältnis für bessere Ausrichtung

        with col1:
            erhalten_durch = st.selectbox(
                "Erhalten durch",
                ["-", "gekauft", "ausgeliehen"],
                key=f"erhalten_{i}",
                label_visibility="collapsed"
            )

        with col2:
            if erhalten_durch != "-" and st.button(f"✅ Übernehmen", key=f"uebernehmen_{i}"):
                book["Status"] = "erledigt"
                book["Erhalten durch"] = erhalten_durch
                data["read_books"].append(book)
                data["wishlist"].pop(i)
                save_data(data)
                st.rerun()

        with col3:
            if st.button("🗑️ Entfernen", key=f"entfernen_{i}"):
                data["wishlist"].pop(i)
                save_data(data)
                st.rerun()

# ----------------------------
# Gekaufte/Gelesene Bücher (Tabelle + Filter)
# ----------------------------
elif page == "Übersicht":
    st.header("Übersicht")

    df = pd.DataFrame(data["read_books"])

    if df.empty:
        st.info("Noch keine Bücher gekauft oder gelesen.")
    else:
        st.subheader("Buch filtern")

        # Filter
        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("Titel oder Autor suchen")

        # Alle Genres und Autoren
        all_genres = df["Genre"].dropna().unique()
        all_authors = df["Autor"].dropna().unique()

        # Dynamische Optionen basierend auf Auswahl
        selected_author = None
        selected_genre = None

        with col2:
            selected_author = st.selectbox("Autor filtern", options=["Alle"] + list(all_authors))

        if selected_author != "Alle":
            genres_for_author = df[df["Autor"] == selected_author]["Genre"].dropna().unique()
            genre_options = ["Alle"] + list(genres_for_author)
        else:
            genre_options = ["Alle"] + list(all_genres)

        with col3:
            selected_genre = st.selectbox("Genre filtern", options=genre_options)
        
       
        col_dfrom, col_dto = st.columns(2)
        date_from = col_dfrom.date_input("Gelesen ab", value=None, key="date_from")
        date_to = col_dto.date_input("Gelesen bis", value=None, key="date_to")

        # Jetzt auch Autorenoptionen beschränken, wenn Genre gewählt
        if selected_genre != "Alle":
            authors_for_genre = df[df["Genre"] == selected_genre]["Autor"].dropna().unique()
            author_options = ["Alle"] + list(authors_for_genre)

            if selected_author not in author_options:
                selected_author = "Alle"

        # Filter anwenden
        filtered_df = df.copy()

        if search:
            filtered_df = filtered_df[
                filtered_df["Titel"].str.contains(search, case=False) | 
                filtered_df["Autor"].str.contains(search, case=False)
            ]

        if selected_author != "Alle":
            filtered_df = filtered_df[filtered_df["Autor"] == selected_author]

        if selected_genre != "Alle":
            filtered_df = filtered_df[filtered_df["Genre"] == selected_genre]

        # Datumsbereichsfilter anwenden
        if date_from and date_to:
            def match_date_range(entry):
                if isinstance(entry, list):
                    for date_str in entry:
                        try:
                            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
                            if date_from <= dt <= date_to:
                                return True
                        except Exception:
                            continue
                elif isinstance(entry, str):
                    try:
                        dt = datetime.strptime(entry, "%Y-%m-%d").date()
                        return date_from <= dt <= date_to
                    except:
                        pass
                return False
            filtered_df = filtered_df[filtered_df["Gelesen am"].apply(match_date_range)]

        sql_filter = st.text_input("Query eingeben (z.B. `Genre == 'Krimi' and Autor.str.contains('King')`)")

        if sql_filter:
            try:
                filtered_df = filtered_df.query(sql_filter)
            except Exception as e:
                st.error(f"Fehler in der Query: {e}")

        st.markdown("---")

        # Anzahl der gefilterten Bücher anzeigen
        st.markdown(f"##### Gefundene Bücher: {len(filtered_df)}")

        if "Gelesen am" in filtered_df.columns:
            filtered_df["Gelesen am (Mehrfach)"] = filtered_df["Gelesen am"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else str(x) if pd.notnull(x) else "-"
            )
        else:
             filtered_df["Gelesen am (Mehrfach)"] = "-"
        st.dataframe(
            filtered_df[["Titel", "Autor", "Genre", "Erhalten durch", "Gelesen am (Mehrfach)"]],
            use_container_width=True
        )

# ----------------------------
# Details
# ----------------------------
elif page == "Details":
    st.header("Details")

    if not data["read_books"]:
        st.warning("Bitte zuerst Bücher als gekauft markieren.")
    else:
            df_details = pd.DataFrame(data["read_books"])

    # Filter-Auswahl
    st.subheader("Buch filtern")
    col1, col2 = st.columns(2)

    with col1:
        selected_author = st.selectbox("Autor auswählen", ["Alle"] + sorted(df_details["Autor"].dropna().unique().tolist()))

    with col2:
        if selected_author != "Alle":
            titles = df_details[df_details["Autor"] == selected_author]["Titel"].unique()
        else:
            titles = df_details["Titel"].unique()

        selected_title = st.selectbox("Titel auswählen", ["Alle"] + sorted(titles))

    # Bücher filtern
    filtered_books = data["read_books"]
    if selected_author != "Alle":
        filtered_books = [b for b in filtered_books if b["Autor"] == selected_author]
    if selected_title != "Alle":
        filtered_books = [b for b in filtered_books if b["Titel"] == selected_title]

    st.markdown("---")

    # Anzeige
    if not filtered_books:
        st.info("Keine Bücher mit diesen Filtern gefunden.")
    else:
        st.subheader("Details")
        for book in filtered_books:
            with st.expander(f"{book['Titel']} von {book['Autor']}"):
                # Gelesen-Datum
                gelesen_am = st.date_input(f"Gelesen am ({book['Titel']})", value=datetime.today(), key=f"date_{book['Titel']}")
                if st.button(f"💾 Speichern (Gelesen am) für {book['Titel']}", key=f"save_{book['Titel']}"):
                    new_date = gelesen_am.strftime("%Y-%m-%d")
                    if "Gelesen am" not in book:
                        book["Gelesen am"] = []

                    if new_date not in book["Gelesen am"]:
                        book["Gelesen am"].append(new_date)
                        save_data(data)
                        st.success("Lesedatum gespeichert!")
                    else:
                        st.info("Dieses Datum wurde bereits gespeichert.")

                # Notizen
                if "Notizen" not in book:
                    book["Notizen"] = []

                with st.form(f"form_{book['Titel']}"):
                    note = st.text_area("Neue Anmerkung")
                    submit_note = st.form_submit_button("Speichern")
                    if submit_note and note:
                        book["Notizen"].append({
                            "Text": note,
                            "Zeit": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        save_data(data)
                        st.success("Anmerkung gespeichert!")

                st.markdown("**Anmerkungen:**")
                for note in book["Notizen"]:
                    st.markdown(f"- _{note['Zeit']}_: {note['Text']}")

# ----------------------------
# Speicherung
# ----------------------------
save_data(data)
