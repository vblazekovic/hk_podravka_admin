# Hrvački klub Podravka - Streamlit aplikacija

Ova aplikacija omogućuje administraciju i praćenje aktivnosti Hrvačkog kluba Podravka.

## Sadržaj paketa
- **hk_podravka_app_full.py** – glavna aplikacija sa svim sekcijama
- **podravka.db** – SQLite baza podataka (prazna, spremna za korištenje)
- **exports/** – direktorij za izvezene datoteke (Excel/CSV)
- **logos/** – direktorij za spremanje logotipa kluba

## Pokretanje
1. Instaliraj potrebne pakete:
   ```bash
   pip install streamlit pandas openpyxl pycountry
   ```

2. Pokreni aplikaciju:
   ```bash
   streamlit run hk_podravka_app_full.py
   ```

## Sekcije u aplikaciji
- **Klub** – osnovni podaci i prikaz loga
- **Članovi** – pregled, pretraživanje i izvoz članova (CSV/Excel)
- **Treneri** – pregled, pretraživanje i izvoz trenera (CSV/Excel)
- **Grupe** – pregled i izvoz grupa (ako postoji tablica u bazi)
- **Prisutnost** – evidencija i izvoz prisutnosti (tablice presence/attendance)
- **Statistika** – brzi export ključnih tablica (natjecanja, članovi, treneri)
- **Natjecanja i rezultati** – unos, filtriranje i statistika s podrškom za reprezentativne nastupe, ISO/IOC kodove država, trenere i Excel export

## Napomena
Ako se baza ne učita, provjeri da se datoteka `podravka.db` nalazi u istom direktoriju kao aplikacija.

Autor: Vedran Blažeković
Verzija: 2025-10
