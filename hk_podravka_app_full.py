
# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from pathlib import Path
from datetime import date

st.set_page_config(page_title="HK Podravka Admin", layout="wide")

DB_PATH = "podravka.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def table_exists(conn, name: str) -> bool:
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
        return cur.fetchone() is not None
    except Exception:
        return False

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS competitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        kind TEXT,
        subtype TEXT,
        date_from TEXT,
        date_to TEXT,
        country TEXT,
        iso_code TEXT,
        ioc_code TEXT,
        place TEXT,
        style TEXT,
        age_group TEXT,
        club_competitors INTEGER,
        team_rank TEXT,
        wins INTEGER,
        losses INTEGER,
        coaches_text TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS coaches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT
    )""")
    conn.commit(); conn.close()

def show_logo_safe(src: str | None, caption: str = "", width=None, use_column_width=True):
    if not src:
        st.warning("Logo nije dostupan."); return
    try:
        p = Path(str(src))
        if p.exists() and p.is_file():
            st.image(str(p), caption=caption, width=width, use_column_width=use_column_width); return
        st.image(src, caption=caption, width=width, use_column_width=use_column_width)
    except Exception as e:
        st.warning(f"Logo nije moguće učitati ({e.__class__.__name__}).")
        if caption: st.caption(caption)

def download_df_as_excel_button(df: pd.DataFrame, filename_base: str):
    buf = BytesIO(); df.to_excel(buf, index=False); buf.seek(0)
    st.download_button("💾 Preuzmi Excel", data=buf.getvalue(), file_name=f"{filename_base}.xlsx")

def compute_competition_stats(conn, member_id: int | None = None):
    try:
        if member_id is None:
            q = """
                SELECT
                    c.kind AS vrsta_natjecanja,
                    COALESCE(c.subtype,'') AS podvrsta,
                    c.date_from AS datum_od,
                    c.date_to   AS datum_do,
                    c.country   AS država,
                    c.place     AS mjesto,
                    c.style     AS stil,
                    c.age_group AS uzrast,
                    c.club_competitors AS nastupilo_hrvača,
                    c.team_rank AS ekipni_plasman,
                    COALESCE(SUM(cr.wins),0)   AS pobjeda,
                    COALESCE(SUM(cr.losses),0) AS poraza,
                    c.coaches_text AS treneri
                FROM competitions c
                LEFT JOIN competition_results cr ON cr.competition_id = c.id
                GROUP BY c.id
                ORDER BY c.date_from DESC
            """
            df = pd.read_sql_query(q, conn)
        else:
            q = """
                SELECT
                    c.kind AS vrsta_natjecanja,
                    COALESCE(c.subtype,'') AS podvrsta,
                    c.date_from AS datum_od,
                    c.date_to   AS datum_do,
                    c.country   AS država,
                    c.place     AS mjesto,
                    c.style     AS stil,
                    c.age_group AS uzrast,
                    c.club_competitors AS nastupilo_hrvača,
                    c.team_rank AS ekipni_plasman,
                    COALESCE(SUM(cr.wins),0)   AS pobjeda,
                    COALESCE(SUM(cr.losses),0) AS poraza,
                    c.coaches_text AS treneri,
                    MAX(COALESCE(cr.placement,0)) AS plasman
                FROM competitions c
                LEFT JOIN competition_results cr ON cr.competition_id = c.id
                WHERE cr.member_id = ?
                GROUP BY c.id
                ORDER BY c.date_from DESC
            """
            df = pd.read_sql_query(q, conn, params=(int(member_id),))
        if not df.empty:
            for col in ["datum_od","datum_do"]:
                try:
                    df[col] = pd.to_datetime(df[col]).dt.strftime("%d.%m.%Y.")
                except Exception:
                    pass
        return df
    except Exception as e:
        st.error(f"Greška pri dohvaćanju podataka: {e}")
        return pd.DataFrame()

def page_header(title, subtitle=""):
    st.subheader(title)
    if subtitle: st.caption(subtitle)

# ---- Sekcije (placeholders zadržavaju sve stranice) ----
def section_club():
    page_header("Klub", "Osnovni podaci")
    st.text_input("Naziv kluba")
    st.text_input("Adresa")
    st.text_input("OIB")
    st.text_input("IBAN")
    logo = "https://hk-podravka.com/wp-content/uploads/2021/08/cropped-HK-Podravka-logo.png"
    show_logo_safe(logo, caption="Hrvački klub Podravka")

def section_members():
    page_header("Članovi")
    st.info("Postojeća logika za članove može se zalijepiti ovdje.")
    conn = get_conn()
    if table_exists(conn, "members"):
        df = pd.read_sql_query("SELECT * FROM members", conn)
        st.dataframe(df, use_container_width=True)
        download_df_as_excel_button(df, "clanovi_export")
    conn.close()

def section_coaches():
    page_header("Treneri")
    st.info("Postojeća logika za trenere može se zalijepiti ovdje.")
    conn = get_conn()
    if table_exists(conn, "coaches"):
        df = pd.read_sql_query("SELECT * FROM coaches", conn)
        st.dataframe(df, use_container_width=True)
        download_df_as_excel_button(df, "treneri_export")
    conn.close()

def section_groups():
    page_header("Grupe")
    st.info("Postojeća logika za grupe može se zalijepiti ovdje.")

def section_presence():
    page_header("Prisutstvo")
    st.info("Postojeća logika za prisutnost može se zalijepiti ovdje.")

def section_stats():
    page_header("Statistika")
    st.info("Osnovna statistika.")

def section_competitions():
    page_header("Natjecanja i rezultati", "Unos i pregled")
    conn = get_conn()

    KINDS = [
        "PRVENSTVO HRVATSKE","MEĐUNARODNI TURNIR","REPREZENTATIVNI NASTUP",
        "HRVAČKA LIGA ZA SENIORE","MEĐUNARODNA HRVAČKA LIGA ZA KADETE",
        "REGIONALNO PRVENSTVO","LIGA ZA DJEVOJČICE","OSTALO"
    ]
    REP_SUB = ["PRVENSTVO EUROPE","PRVENSTVO SVIJETA","PRVENSTVO BALKANA","UWW TURNIR","OSTALO"]
    STYLES = ["GR","FS","WW","BW"]
    AGES = ["POČETNICI","U11","U13","U15","U17","U20","U23","SENIORI"]

    try:
        import pycountry
        COUNTRIES = sorted(
            [(f"{c.name} ({getattr(c,'alpha_3','').upper()})",
              getattr(c,'alpha_3','').lower(),
              getattr(c,'alpha_3','').upper())
             for c in pycountry.countries],
            key=lambda x: x[0]
        )
    except Exception:
        COUNTRIES = [("Croatia (CRO)","hrv","CRO"),("Serbia (SRB)","srb","SRB"),("Slovenia (SLO)","svn","SLO")]

    with st.form("comp_form"):
        kind = st.selectbox("Vrsta natjecanja", KINDS)
        subtype = ""
        if kind == "REPREZENTATIVNI NASTUP":
            rep_choice = st.selectbox("Podvrsta reprezentativnog nastupa", REP_SUB)
            subtype = st.text_input("Upiši podvrstu", value="") if rep_choice=="OSTALO" else rep_choice
        elif kind == "OSTALO":
            subtype = st.text_input("Upiši vrstu (ako 'OSTALO')", value="")

        name = st.text_input("Naziv natjecanja (opcionalno)")

        c1, c2 = st.columns(2)
        date_from = c1.date_input("Datum od", value=date.today())
        date_to = c2.date_input("Datum do", value=date.today())

        country_names = [c[0] for c in COUNTRIES]
        sel_country = st.selectbox("Država", country_names)
        iso_code = next(c[1] for c in COUNTRIES if c[0]==sel_country)
        ioc_code = next(c[2] for c in COUNTRIES if c[0]==sel_country)
        st.text_input("ISO3 (auto)", iso_code, disabled=True)
        st.text_input("IOC (auto)", ioc_code, disabled=True)

        place = st.text_input("Mjesto")
        style = st.selectbox("Stil", STYLES)
        age_group = st.selectbox("Uzrast", AGES)

        c3,c4 = st.columns(2)
        club_competitors = c3.number_input("Broj naših hrvača", min_value=0, step=1)
        team_rank = c4.text_input("Ekipni plasman")

        auto_results = table_exists(conn, "competition_results")
        if auto_results:
            st.info("Pobjede/porazi se računaju automatski iz competition_results (ako postoji).")
            wins = 0; losses = 0
        else:
            c5,c6 = st.columns(2)
            wins = c5.number_input("Ukupan broj pobjeda", min_value=0, step=1)
            losses = c6.number_input("Ukupan broj poraza", min_value=0, step=1)

        # Trener(i)
        coaches = [r[0] for r in conn.execute("SELECT full_name FROM coaches ORDER BY full_name").fetchall()] if table_exists(conn,"coaches") else []
        mode = st.radio("Odabir trenera", ["Jedan","Više"], horizontal=True)
        if mode=="Jedan":
            coach_text = st.selectbox("Trener", coaches if coaches else [""])
        else:
            coach_text = ", ".join(st.multiselect("Treneri", coaches))

        submit = st.form_submit_button("Spremi natjecanje")

    if submit:
        errors = []
        if not kind: errors.append("Odaberi vrstu natjecanja.")
        if not sel_country: errors.append("Odaberi državu.")
        if not place: errors.append("Upiši mjesto.")
        if date_to < date_from: errors.append("Datum 'do' ne može biti prije 'od'.")
        if mode == "Jedan" and (not coach_text or coach_text.strip()==""): errors.append("Odaberi trenera.")
        if mode == "Više" and (not coach_text or coach_text.strip()==""): errors.append("Odaberi barem jednog trenera.")
        if errors:
            for e in errors: st.error(e)
        else:
            conn.execute(
                "INSERT INTO competitions (name,kind,subtype,date_from,date_to,country,iso_code,ioc_code,place,style,age_group,club_competitors,team_rank,wins,losses,coaches_text) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (name, kind, subtype, str(date_from), str(date_to), sel_country, iso_code, ioc_code, place, style, age_group, int(club_competitors), team_rank, int(wins), int(losses), coach_text)
            )
            conn.commit()
            st.success("Natjecanje spremljeno.")

    # Sažetak ispod
    st.markdown("---"); st.subheader("Sažetak natjecanja")
    view_mode = st.radio("Prikaz", ["Statistika kluba","Statistika sportaša"], horizontal=True)

    if view_mode == "Statistika kluba":
        df = compute_competition_stats(conn, None)
        st.dataframe(df, use_container_width=True)
        if not df.empty: download_df_as_excel_button(df, "natjecanja_klub")
    else:
        members = conn.execute("SELECT id, full_name FROM members ORDER BY full_name").fetchall() if table_exists(conn,"members") else []
        if members:
            sel = st.selectbox("Sportaš", [f"{m[0]} – {m[1]}" for m in members])
            mid = int(sel.split(" – ")[0])
            df = compute_competition_stats(conn, mid)
            st.dataframe(df, use_container_width=True)
            if not df.empty: download_df_as_excel_button(df, "natjecanja_sportas")
        else:
            st.info("Nema unesenih sportaša.")

def main():
    init_db()
    with st.sidebar:
        st.title("Hrvački klub Podravka")
        choice = st.radio("Navigacija", ["Klub","Članovi","Treneri","Natjecanja i rezultati","Statistika","Grupe","Prisutstvo"], index=3)

    if choice=="Klub": section_club()
    elif choice=="Članovi": section_members()
    elif choice=="Treneri": section_coaches()
    elif choice=="Natjecanja i rezultati": section_competitions()
    elif choice=="Statistika": section_stats()
    elif choice=="Grupe": section_groups()
    elif choice=="Prisutstvo": section_presence()

    with st.sidebar:
        st.divider()
        try:
            conn = get_conn(); conn.execute("SELECT 1"); st.success("DB OK")
        except Exception as e:
            st.error(f"Baza greška: {e}")

if __name__ == "__main__":
    main()
