"""Interface Streamlit : streamlit run app_streamlit.py"""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st
import yaml

from mge_docs import generation, numerotation
from mge_docs.calculs import taux_valide
from mge_docs.catalogue import charger_catalogue, charger_config
from mge_docs.fiche import FicheInvalide, valider
from mge_docs.formatage import pct, xpf

st.set_page_config(page_title="MGE Conseil — Propositions", page_icon="📄", layout="wide")
config = charger_config()
catalogue = charger_catalogue()
cond = config["conditions"]

st.title("Proposition commerciale et lettre de mission")
st.caption(f"Prochain numéro : **{numerotation.prochain_numero(generation.REGISTRE_DEFAUT)}**")

manquants = generation.champs_cabinet_manquants(config)
if manquants:
    st.warning("Champs du cabinet à compléter dans config/mge.yaml : " + ", ".join(manquants))

fichier = st.file_uploader("Charger une fiche client YAML (facultatif)", type=["yaml", "yml"])
init = {}
if fichier:
    try:
        init = yaml.safe_load(fichier.getvalue().decode("utf-8")) or {}
    except yaml.YAMLError as e:
        st.error(f"YAML illisible : {e}")

codes = list(catalogue)
col1, col2 = st.columns(2)
with col1:
    st.subheader("Client")
    raison_sociale = st.text_input("Raison sociale *", init.get("raison_sociale", ""))
    ridet = st.text_input("RIDET *", str(init.get("ridet", "")), help="7 chiffres, éventuellement suivis du n° d'établissement : 1234567.001")
    dirigeant = st.text_input("Dirigeant *", init.get("dirigeant", ""))
    qualite = st.text_input("Qualité du dirigeant", init.get("qualite_dirigeant", ""))
    adresse = st.text_input("Adresse", init.get("adresse", ""))
    secteur = st.text_input("Secteur d'activité *", init.get("secteur", ""))
    ca = st.number_input("Chiffre d'affaires annuel HT (F CFP) *", min_value=0, step=1_000_000,
                         value=int(init.get("chiffre_affaires") or 0))
    enjeux_init = init.get("enjeux", [])
    enjeux = st.text_area("Enjeux * (un par ligne)", "\n".join(enjeux_init) if isinstance(enjeux_init, list) else str(enjeux_init))

with col2:
    st.subheader("Mission")
    code_init = init.get("offre") if init.get("offre") in codes else codes[0]
    code = st.selectbox("Offre *", codes, index=codes.index(code_init), format_func=lambda c: catalogue[c].nom)
    offre = catalogue[code]
    prix_defaut = offre.prix_ht or offre.prix_ht_min
    prix = st.number_input("Prix HT (F CFP)" + (" / mois" if offre.mensuelle else " — forfait") + " *",
                           min_value=0, step=10_000, value=int(init.get("prix_ht") or prix_defaut), key=f"prix_{code}")
    if offre.a_fourchette:
        st.caption(f"Fourchette catalogue : {xpf(offre.prix_ht_min)} à {xpf(offre.prix_ht_max)} HT")
    unite = "mois" if offre.mensuelle else "semaines (délai de remise)"
    duree = st.number_input(f"Durée ({unite}) *", min_value=1, step=1,
                            value=int(init.get("duree") or (12 if offre.mensuelle else 4)), key=f"duree_{code}")
    debut_init = init.get("date_debut")
    if isinstance(debut_init, str):
        debut_init = date.fromisoformat(debut_init)
    debut = st.date_input("Date de début *", debut_init or date.today() + timedelta(days=14), format="DD/MM/YYYY")
    taux = st.text_input("Taux de TGC (%)", str(cond["taux_tgc"]))
    formats = st.multiselect("Formats", list(generation.FORMATS), default=list(generation.FORMATS))

donnees = {"raison_sociale": raison_sociale, "ridet": ridet, "dirigeant": dirigeant, "qualite_dirigeant": qualite,
           "adresse": adresse, "secteur": secteur, "chiffre_affaires": int(ca) if ca else None,
           "enjeux": [e.strip(" -•") for e in enjeux.splitlines() if e.strip(" -•")],
           "offre": code, "prix_ht": int(prix) if prix else None, "duree": int(duree), "date_debut": debut}

st.divider()
try:
    taux_valide(taux)
    fiche = valider(donnees, catalogue, cond["engagement_mois"])
except FicheInvalide as e:
    st.error("La fiche est incomplète ou invalide :\n\n" + "\n".join(f"- {x}" for x in e.erreurs))
    st.stop()
except ValueError as e:
    st.error(str(e))
    st.stop()

for a in fiche.avertissements:
    st.warning(a)

m = generation.montants(fiche, taux)
c1, c2, c3 = st.columns(3)
suffixe = " / mois" if offre.mensuelle else ""
c1.metric("Honoraires HT" + suffixe, xpf(m.ht))
c2.metric(f"TGC ({pct(m.taux_tgc)})" + suffixe, xpf(m.tgc))
c3.metric("Total TTC" + suffixe, xpf(m.ttc))
if offre.mensuelle:
    st.caption(f"Sur {m.nb_periodes} mois : HT {xpf(m.total_ht)} · TGC {xpf(m.total_tgc)} · TTC {xpf(m.total_ttc)}")

if st.button("Générer les documents", type="primary", disabled=not formats):
    res = generation.generer(fiche, config, formats=formats, taux_tgc=taux)
    st.success(f"Documents générés : {res['numero']}")
    for f in res["fichiers"]:
        mime = "application/pdf" if f.suffix == ".pdf" else \
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        st.download_button(f"Télécharger {f.name}", f.read_bytes(), file_name=f.name, mime=mime, key=f.name)
