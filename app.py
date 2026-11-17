"""Tableau de bord du groupe — streamlit run app.py"""
from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from tdb import donnees as dn
from tdb.indicateurs import GROUPE, Donnees, fin_de_mois, liste_mois, lundi_chiffres, lundi_mouvements, mois_de
from tdb.valeurs import lundi as lundi_de, xpf

RACINE = Path(__file__).parent
DOSSIER = Path(os.environ.get("TDB_DONNEES", RACINE / "donnees"))
CONFIG = RACINE / ("config.local.yaml" if (RACINE / "config.local.yaml").exists() else "config.yaml")

st.set_page_config(page_title="Tableau de bord du groupe", page_icon="📊", layout="wide")
cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
NOMS = {e: v["nom"] for e, v in cfg["entites"].items()} | {GROUPE: "Groupe (consolidé)"}


def fmt(v, kind="xpf"):
    if v is None:
        return "à saisir"
    if kind == "pct":
        return f"{v * 100:.0f} %".replace(".", ",")
    if kind == "nb":
        return f"{v:,.1f}".replace(",", " ").replace(".", ",").replace(" ", " ")
    return xpf(int(v))


def txt(v):
    return "à saisir" if v is None else str(v)


@st.cache_data(show_spinner=False)
def charger(dossier: str, signature: tuple):
    F, P, B, erreurs = [], [], [], []
    for e in cfg["entites"]:
        for nom, lecteur, liste, cle in [("factures.csv", dn.lire_factures, F, "factures"),
                                         ("paiements.csv", dn.lire_paiements, P, "paiements"),
                                         ("banque.csv", dn.lire_banque, B, "banque")]:
            chemin = Path(dossier) / e / nom
            if chemin.exists():
                try:
                    liste += lecteur(chemin, e, cfg["colonnes"][cle], f"{e}/{nom}")
                except dn.ErreurDonnees as err:
                    erreurs.append(str(err))
            else:
                erreurs.append(f"{e}/{nom} absent")
    try:
        S = dn.lire_saisie(Path(dossier) / "saisie_mensuelle.csv")
    except dn.ErreurDonnees as err:
        S, _ = dn.Saisie(), erreurs.append(str(err))
    return F, P, B, S, erreurs


def signature():
    return tuple(sorted((str(p), p.stat().st_mtime) for p in DOSSIER.rglob("*.csv"))) if DOSSIER.exists() else ()


F, P, B, S, erreurs = charger(str(DOSSIER), signature())
d = Donnees(F, P, B, S, cfg["entites"], cfg.get("soldes_initiaux") or {}, cfg.get("jours_retard_creances", 30))
seuil = cfg.get("seuil_part_premier_client", 0.75)
n_jours = cfg.get("jours_retard_creances", 30)

with st.sidebar:
    st.header("Groupe")
    page = st.radio("Page", ["Lundi", "Indicateurs mensuels", "Terrawaves", "MGE", "Personnel", "Saisie mensuelle", "Données"])
    st.caption(f"Données : `{DOSSIER}`")
    if erreurs:
        st.error(f"{len(erreurs)} problème(s) de données — voir la page « Données ».")

dates = [f.date for f in F] + [m.date for m in B]
if not dates:
    st.title("Tableau de bord du groupe")
    st.warning(f"Aucune donnée trouvée dans {DOSSIER}. Voir la page « Données » et le README.")
    if page != "Données":
        st.stop()
derniere = max(dates) if dates else date.today()
tous_mois = liste_mois(mois_de(min(dates)), mois_de(derniere)) if dates else []

# =================================================================== Lundi ===
if page == "Lundi":
    ref = st.date_input("Semaine du lundi", lundi_de(min(date.today(), derniere + timedelta(days=7))), format="DD/MM/YYYY")
    ref = lundi_de(ref)
    st.title(f"Lundi {ref:%d/%m/%Y}")
    mv = lundi_mouvements(d, ref)
    deb, fin = mv["periode"]
    st.caption(f"Situation au dimanche {fin:%d/%m} au soir, comparée au dimanche {fin - timedelta(days=7):%d/%m}. "
               f"Données disponibles jusqu'au {derniere:%d/%m/%Y}.")
    if derniere < fin:
        st.warning("Les exports sont antérieurs à la fin de la semaine : pensez à les mettre à jour.")
    cols = st.columns(5)
    for col, c in zip(cols, lundi_chiffres(d, ref, seuil)):
        var = c.variation
        if c.format == "pct":
            delta = None if var is None else f"{var * 100:+.0f} pts".replace(".", ",")
        else:
            delta = None if var is None else f"{var:+,.0f} F".replace(",", " ")
        col.metric(c.libelle, fmt(c.valeur, c.format), delta,
                   delta_color="off" if delta == "stable" else ("normal" if c.sens_favorable > 0 else "inverse"),
                   help="Variation par rapport au dimanche précédent")
        if c.alerte:
            col.error(f"Au-dessus de {seuil:.0%} ({c.detail})".replace(".", ","))
        elif c.detail:
            col.caption(c.detail)
    st.subheader("Ce qui a bougé cette semaine")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Nouvelles créances à plus de {n_jours} jours**")
    for f, r in mv["nouvelles_creances_30"]:
        c1.write(f"{NOMS[f.entite]} · {f.tiers} · {f.ref} — {xpf(r)}")
    if not mv["nouvelles_creances_30"]:
        c1.caption("Aucune.")
    c2.markdown("**Plus grosses factures émises**")
    for f in mv["factures"]:
        c2.write(f"{NOMS[f.entite]} · {f.tiers} — {xpf(f.ht)} HT")
    if not mv["factures"]:
        c2.caption("Aucune facture émise.")
    c3.markdown("**Plus gros encaissements**")
    for p in mv["paiements"]:
        c3.write(f"{NOMS[p.entite]} · {p.ref_facture} — {xpf(p.montant)}")
    if not mv["paiements"]:
        c3.caption("Aucun encaissement.")

# ===================================================== Indicateurs mensuels ===
elif page == "Indicateurs mensuels":
    st.title("Indicateurs mensuels")
    nb = st.slider("Nombre de mois", 3, max(3, len(tous_mois)), min(12, max(3, len(tous_mois))))
    mois = tous_mois[-nb:]
    libelles = {"ca_ht": "CA HT", "marge": "Marge", "charges_fixes": "Charges fixes", "resultat": "Résultat estimé",
                "tresorerie": "Trésorerie fin de mois", "creances_30": f"Créances > {n_jours} j"}
    for ent in [GROUPE, *cfg["entites"]]:
        st.subheader(NOMS[ent])
        lignes = {m: d.indicateurs_mois(ent, m) for m in mois}
        if ent == GROUPE and mois and mois[-1] == mois_de(derniere) and derniere != fin_de_mois(mois[-1]):
            st.caption(f"{mois[-1]} : mois en cours (données au {derniere:%d/%m/%Y}).")
        tab = pd.DataFrame({libelles[k]: [fmt(lignes[m][k]) for m in mois] for k in libelles}, index=mois).T
        st.dataframe(tab, width="stretch")
        if ent == GROUPE:
            ecarts = {m: lignes[m]["ecart_intragroupe"] for m in mois if lignes[m]["ecart_intragroupe"]}
            if ecarts:
                st.warning("Facturation intragroupe non réconciliée (CA intragroupe ≠ charges intragroupe saisies) : "
                           + ", ".join(f"{m} : {xpf(v)}" for m, v in ecarts.items()))
            graph = pd.DataFrame({"CA HT": [lignes[m]["ca_ht"] for m in mois],
                                  "Trésorerie": [lignes[m]["tresorerie"] for m in mois]}, index=mois)
            st.line_chart(graph)

# ============================================================== Terrawaves ===
elif page == "Terrawaves":
    st.title("Terrawaves Logistics")
    mois = tous_mois[-12:]
    t = {m: d.terrawaves_mois(m, seuil) for m in mois}
    dernier = t[mois[-1]]
    c = st.columns(4)
    c[0].metric(f"Part du 1er client ({mois[-1]})", fmt(dernier["part_premier_client"], "pct"))
    c[1].metric("Heures vendues par fourgon", fmt(dernier["heures_par_fourgon"], "nb"))
    c[2].metric("Carburant par km", "à saisir" if dernier["carburant_par_km"] is None else f"{dernier['carburant_par_km']:.0f} F/km")
    c[3].metric("Sous-traitance", fmt(dernier["sous_traitance"]))
    alertes = [m for m in mois if t[m]["alerte_concentration"]]
    if alertes:
        st.error(f"Dépendance client : le 1er client dépasse {seuil:.0%} du CA en ".replace(".", ",") + ", ".join(alertes))
    st.dataframe(pd.DataFrame({
        "1er client": [t[m]["premier_client"] or "" for m in mois],
        "Part du CA": [fmt(t[m]["part_premier_client"], "pct") for m in mois],
        "Alerte": ["⚠" if t[m]["alerte_concentration"] else "" for m in mois],
        "Heures / fourgon": [fmt(t[m]["heures_par_fourgon"], "nb") for m in mois],
        "Carburant F/km": [fmt(t[m]["carburant_par_km"], "nb") for m in mois],
        "Sous-traitance HT": [fmt(t[m]["sous_traitance"]) for m in mois],
        "Sous-traitance / CA": [fmt(t[m]["sous_traitance_pct_ca"], "pct") for m in mois]}, index=mois).T, width="stretch")

# ===================================================================== MGE ===
elif page == "MGE":
    st.title("MGE Conseil")
    mois = tous_mois[-12:]
    dispo = cfg.get("jours_disponibles_mge", 10)
    g = {m: d.mge_mois(m, dispo) for m in mois}
    der = g[mois[-1]]
    c = st.columns(4)
    c[0].metric("Revenu mensuel récurrent signé", fmt(der["mrr_signe"]))
    c[1].metric("Jours facturés", "à saisir" if der["jours_factures"] is None else f"{der['jours_factures']} / {der['jours_disponibles']}")
    c[2].metric("Taux d'occupation", fmt(der["taux_occupation"], "pct"))
    c[3].metric("Pipeline", " → ".join(str(der[k] if der[k] is not None else "–") for k in ("contacts", "rendez_vous", "diagnostics")),
                help="Contacts → rendez-vous → diagnostics")
    st.dataframe(pd.DataFrame({
        "Revenu récurrent signé": [fmt(g[m]["mrr_signe"]) for m in mois],
        "Jours facturés": [txt(g[m]["jours_factures"]) for m in mois], "Jours disponibles": [txt(g[m]["jours_disponibles"]) for m in mois],
        "Occupation": [fmt(g[m]["taux_occupation"], "pct") for m in mois],
        "Contacts": [txt(g[m]["contacts"]) for m in mois], "Rendez-vous": [txt(g[m]["rendez_vous"]) for m in mois],
        "Diagnostics": [txt(g[m]["diagnostics"]) for m in mois],
        "Contacts → RDV": [fmt(g[m]["conversion_rdv"], "pct") for m in mois],
        "RDV → diagnostic": [fmt(g[m]["conversion_diagnostic"], "pct") for m in mois]}, index=mois).T, width="stretch")

# =============================================================== Personnel ===
elif page == "Personnel":
    st.title("Personnel — prélèvements du dirigeant")
    taux = cfg.get("taux_provision_fiscale")
    taux_ui = st.number_input("Taux de provision fiscale (%)", 0.0, 100.0, float(taux * 100) if taux is not None else 0.0, 0.5,
                              help="Taux moyen estimé d'impôt et de cotisations à mettre de côté sur les sommes prélevées. "
                                   "À fixer avec votre expert-comptable.")
    if taux is None:
        st.warning("Aucun taux enregistré dans config.yaml (taux_provision_fiscale). La provision ci-dessous utilise le taux saisi ici, "
                   "sans l'enregistrer.")
    r = d.personnel(tous_mois[-12:], taux_ui / 100)
    if r:
        a = r[-1]
        c = st.columns(3)
        c[0].metric(f"Prélevé en {a['mois'][:4]} (cumul)", xpf(a["cumul_preleve"]))
        c[1].metric("Provision fiscale recommandée (cumul)", fmt(a["cumul_provision"]))
        c[2].metric("Taux appliqué", f"{taux_ui:.1f} %".replace(".", ","))
        st.dataframe(pd.DataFrame([{"Mois": x["mois"], "Prélevé": fmt(x["preleve"]), "Provision": fmt(x["provision"]),
                                    "Cumul prélevé (année)": xpf(x["cumul_preleve"]),
                                    "Cumul provision (année)": fmt(x["cumul_provision"])} for x in r]),
                     width="stretch", hide_index=True)
    st.caption("Estimation simplifiée à taux unique : l'impôt réel (barème progressif, cotisations) peut différer. "
               "À valider avec votre expert-comptable.")

# ======================================================== Saisie mensuelle ===
elif page == "Saisie mensuelle":
    st.title("Saisie mensuelle")
    st.markdown("Une ligne par mois et par entité (`terrawaves`, `mge`, `holding`, `personnel`). Montants HT en F CFP. "
                "Laisser vide ce qui ne s'applique pas.")
    with st.expander("Signification des colonnes"):
        st.table(pd.DataFrame([{"colonne": k, "signification": v[0], "entité": v[1]} for k, v in dn.CHAMPS_SAISIE.items()]))
    chemin = DOSSIER / "saisie_mensuelle.csv"
    lignes = dn._lire_csv(chemin) if chemin.exists() else []
    df = pd.DataFrame(lignes).reindex(columns=["mois", "entite", *dn.CHAMPS_SAISIE])
    edit = st.data_editor(df, num_rows="dynamic", width="stretch", key="saisie",
                          column_config={"entite": st.column_config.SelectboxColumn(options=dn.ENTITES_SAISIE)})
    if st.button("Enregistrer", type="primary"):
        DOSSIER.mkdir(parents=True, exist_ok=True)
        tmp = DOSSIER / "saisie_mensuelle.tmp"
        dn.ecrire_saisie([{k: ("" if pd.isna(v) else v) for k, v in r.items()} for r in edit.to_dict("records")], tmp)
        try:
            dn.lire_saisie(tmp)
            tmp.replace(chemin)
            st.success("Saisie enregistrée.")
            st.cache_data.clear()
        except dn.ErreurDonnees as e:
            tmp.unlink(missing_ok=True)
            st.error(f"Non enregistré : {e}")

# ================================================================= Données ===
else:
    st.title("Données")
    st.markdown(f"""Déposer pour chaque entité, dans `{DOSSIER}/<entité>/` :
- `factures.csv` — Dolibarr : *Outils › Exports › Factures clients et lignes de factures*
- `paiements.csv` — *Factures clients et règlements*
- `banque.csv` — *Écritures bancaires et relevés*

Les intitulés de colonnes attendus sont dans `config.yaml` (rubrique `colonnes`).""")
    for e in erreurs:
        st.error(e)
    st.dataframe(pd.DataFrame([{"entité": NOMS[e], "factures": sum(f.entite == e for f in F),
                                "paiements": sum(p.entite == e for p in P), "écritures bancaires": sum(m.entite == e for m in B),
                                "dernière écriture": max((m.date for m in B if m.entite == e), default=None)}
                               for e in cfg["entites"]]), hide_index=True, width="stretch")
    if not any(cfg.get("soldes_initiaux", {}).get(e) for e in cfg["entites"]):
        st.warning("Aucun solde initial bancaire dans config.yaml : la trésorerie affichée ne compte que les écritures exportées.")
