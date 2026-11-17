"""Prévision de trésorerie à 13 semaines — MGE Conseil.  Lancer : streamlit run app.py"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from tresorerie import stockage
from tresorerie.attention import points_attention
from tresorerie.categorisation import NON_CATEGORISE, categoriser
from tresorerie.delais import delais_clients, retard_global
from tresorerie.exports import graphique, pdf_dirigeant, xlsx_detaille
from tresorerie.imports import ErreurImport
from tresorerie.prevision import BASE, Parametres, prevoir
from tresorerie.valeurs import lundi, xpf

st.set_page_config(page_title="Trésorerie 13 semaines — MGE", page_icon="📈", layout="wide")

# ---------------------------------------------------------------- Client ----
with st.sidebar:
    st.header("Dossier client")
    clients = stockage.lister_clients()
    choix = st.selectbox("Client", clients, index=None, placeholder="Choisir un client")
    with st.expander("Nouveau client"):
        nom = st.text_input("Nom de l'entreprise")
        if st.button("Créer le dossier") and nom.strip():
            try:
                st.session_state["client"] = stockage.creer_client(nom)
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    client = choix or st.session_state.get("client")
    st.caption(f"Données stockées localement dans :\n`{stockage.racine()}`")

if not client:
    st.title("Prévision de trésorerie à 13 semaines")
    st.info("Créez ou choisissez un dossier client dans la barre latérale.")
    st.stop()

st.title(f"Trésorerie à 13 semaines — {client}")
try:
    data = stockage.charger(client)
except (ErreurImport, ValueError) as e:
    st.error(f"Données du dossier illisibles : {e}")
    st.stop()

onglets = st.tabs(["1. Données", "2. Catégorisation", "3. Paramètres", "4. Prévision", "5. Exports"])

# ---------------------------------------------------------------- Données ---
FORMATS = {
    "banque": ("Relevé bancaire", "`date ; libelle ; montant` (montant signé : + crédit, − débit) — ou colonnes `debit` / `credit`. Colonne `solde` facultative."),
    "clients": ("Factures clients", "`client ; montant_ttc ; echeance` + facultatif `numero ; date_emission ; date_paiement`. "
                "Les factures **avec** date de paiement servent à calculer les délais réels ; celles **sans** sont les factures ouvertes."),
    "fournisseurs": ("Factures fournisseurs ouvertes", "`fournisseur ; montant_ttc ; echeance` + facultatif `numero`."),
    "charges": ("Charges récurrentes et ventes prévues", "`libelle ; categorie ; montant ; frequence ; prochaine_echeance ; date_fin ; sens`. "
                "Fréquence : hebdomadaire, mensuelle, trimestrielle, semestrielle, annuelle, ponctuelle. "
                "Sens : décaissement (défaut) ou **encaissement** — à utiliser pour les ventes futures pas encore facturées."),
}
with onglets[0]:
    st.caption("CSV séparés par ; ou , — dates JJ/MM/AAAA — montants en F CFP. Un import remplace le fichier précédent.")
    for type_, (titre, aide) in FORMATS.items():
        st.subheader(f"{titre} — {len(data[type_])} ligne(s)")
        st.markdown(aide)
        f = st.file_uploader(titre, type=["csv", "txt"], key=f"up_{type_}", label_visibility="collapsed")
        if f is not None and st.button(f"Importer {f.name}", key=f"btn_{type_}"):
            try:
                n = stockage.enregistrer_csv(client, type_, f.getvalue())
                st.success(f"{n} ligne(s) importée(s).")
                st.rerun()
            except ErreurImport as e:
                st.error("Fichier refusé :\n\n" + "\n".join(f"- {x}" for x in e.erreurs[:20]))

# ------------------------------------------------------- Catégorisation -----
with onglets[1]:
    st.markdown("Règles appliquées dans l'ordre : **la première qui correspond l'emporte**. Le motif est cherché dans le "
                "libellé (sans tenir compte des majuscules ni des accents) ; préfixe `re:` pour une expression régulière. "
                "Sens : `credit`, `debit` ou vide.")
    df_regles = pd.DataFrame(data["regles_brutes"]).reindex(columns=["motif", "sens", "categorie"])
    edit = st.data_editor(df_regles, num_rows="dynamic", width="stretch", key="regles",
                          column_config={"sens": st.column_config.SelectboxColumn(options=["credit", "debit", None])})
    if st.button("Enregistrer les règles"):
        regles = [{k: (None if pd.isna(v) or v == "" else v) for k, v in r.items()}
                  for r in edit.to_dict("records") if not pd.isna(r.get("motif")) and r.get("motif")]
        try:
            stockage.sauver_regles(client, regles)
            st.success("Règles enregistrées.")
            st.rerun()
        except ValueError as e:
            st.error(str(e))
    if data["banque"]:
        lignes = pd.DataFrame([{"date": l.date, "libellé": l.libelle, "montant": l.montant,
                                "catégorie": categoriser(l.libelle, l.montant, data["regles"])} for l in data["banque"]])
        nc = lignes[lignes["catégorie"] == NON_CATEGORISE]
        c1, c2 = st.columns(2)
        c1.metric("Lignes non catégorisées", f"{len(nc)} / {len(lignes)}")
        resume = lignes.groupby("catégorie")["montant"].agg(["count", "sum"]).rename(columns={"count": "lignes", "sum": "total"})
        c2.dataframe(resume.sort_values("total"), width="stretch")
        if len(nc):
            st.subheader("À catégoriser")
            st.dataframe(nc, width="stretch", hide_index=True)
        with st.expander("Toutes les lignes"):
            st.dataframe(lignes, width="stretch", hide_index=True)

# -------------------------------------------------------------- Paramètres --
brut = stockage.charger_parametres(client)
derniere = data["banque"][-1].date if data["banque"] else date.today()
defaut_debut = lundi(derniere) + timedelta(weeks=1)
p0 = stockage.parametres_depuis(brut, defaut_debut)
categories = sorted({categoriser(l.libelle, l.montant, data["regles"]) for l in data["banque"] if l.montant < 0})

with onglets[2]:
    soldes = [l for l in data["banque"] if l.solde is not None]
    if soldes:
        st.info(f"Dernier solde lu dans le relevé : {xpf(soldes[-1].solde)} au {soldes[-1].date:%d/%m/%Y}.")
    c1, c2, c3 = st.columns(3)
    debut = c1.date_input("Lundi de départ", p0.date_debut, format="DD/MM/YYYY",
                          help="Ramené automatiquement au lundi de la semaine choisie.")
    solde = c2.number_input("Solde bancaire au départ (F CFP)", value=p0.solde_initial, step=100_000)
    seuil = c3.number_input("Seuil d'alerte (F CFP)", value=p0.seuil, step=100_000)
    c1, c2, c3 = st.columns(3)
    retard = c1.number_input("Retard du scénario (jours)", 1, 180, p0.retard_scenario_jours)
    douteux = c2.number_input("Exclure les créances échues depuis plus de (jours)", 1, 3650, p0.seuil_douteux_jours)
    hist = c3.number_input("Historique pour les dépenses diverses (semaines)", 1, 52, p0.semaines_historique)
    divers = st.multiselect("Catégories bancaires à extrapoler (moyenne hebdomadaire)", categories,
                            [c for c in p0.categories_divers if c in categories],
                            help="Uniquement des dépenses qui ne figurent PAS déjà dans les factures fournisseurs ou les "
                                 "charges récurrentes, sinon elles seraient comptées deux fois.")
    try:
        params = Parametres(debut, int(solde), int(seuil), 13, int(retard), int(douteux), tuple(divers), int(hist))
    except ValueError as e:
        st.error(str(e))
        st.stop()
    if params.date_debut != debut:
        st.caption(f"Départ retenu : lundi {params.date_debut:%d/%m/%Y}.")
    if st.button("Enregistrer les paramètres"):
        stockage.sauver_parametres(client, params)
        st.success("Paramètres enregistrés.")

# --------------------------------------------------------------- Prévision --
delais = delais_clients(data["clients"])
prev = prevoir(data["clients"], data["fournisseurs"], data["charges"], delais, params, data["banque"], data["regles"])
points = points_attention(prev, data["clients"], delais)

with onglets[3]:
    if not (data["clients"] or data["fournisseurs"] or data["charges"]):
        st.warning("Aucune donnée de prévision importée (factures ou charges).")
    for pr in prev.values():
        if pr.alertes:
            a = pr.alertes[0]
            msg = f"**{pr.titre}** : solde sous le seuil de {xpf(params.seuil)} dès la semaine {a.numero} (du {a.debut:%d/%m}) — {xpf(a.solde_fin)}"
            (st.error if pr.scenario == BASE else st.warning)(msg)
    if not any(pr.alertes for pr in prev.values()):
        st.success(f"Aucune semaine sous le seuil de {xpf(params.seuil)}, quel que soit le scénario.")
    for a in prev[BASE].avertissements:
        st.caption(f"⚠ {a}")

    st.pyplot(graphique(prev), width="stretch")

    choix_sc = st.radio("Scénario", list(prev), format_func=lambda k: prev[k].titre, horizontal=True)
    pr = prev[choix_sc]
    tab = pd.DataFrame([{"Semaine": f"S{s.numero}", "Du": s.debut.strftime("%d/%m"), "Au": s.fin.strftime("%d/%m"),
                         "Solde début": s.solde_debut, "Encaissements": s.encaissements, "Décaissements": s.decaissements,
                         "Solde fin": s.solde_fin, "Alerte": "⚠" if s.sous_seuil else ""} for s in pr.semaines])
    st.dataframe(tab.style.format({c: lambda v: xpf(v) for c in ["Solde début", "Encaissements", "Décaissements", "Solde fin"]})
                 .map(lambda v: "color:#b00020;font-weight:bold" if isinstance(v, int) and v < params.seuil else "", subset=["Solde fin"]),
                 width="stretch", hide_index=True)
    with st.expander("Détail des flux de la semaine"):
        n = st.selectbox("Semaine", range(1, 14), format_func=lambda i: f"S{i}")
        st.dataframe(pd.DataFrame([{"date": f.date, "source": f.source, "tiers": f.tiers, "libellé": f.libelle,
                                    "montant": f.montant, "reporté": "oui" if f.reporte else ""} for f in pr.flux_semaine(n)]),
                     width="stretch", hide_index=True)
    if pr.exclus:
        with st.expander(f"{len(pr.exclus)} facture(s) exclue(s)"):
            st.dataframe(pd.DataFrame([{"client": f.tiers, "échéance": f.echeance, "montant": f.montant_ttc, "motif": m}
                                       for f, m in pr.exclus]), width="stretch", hide_index=True)

    st.subheader("Délais de paiement réels")
    if delais:
        st.caption(f"Retard moyen global (appliqué aux clients sans historique) : {retard_global(delais)} jours.")
        st.dataframe(pd.DataFrame([{"client": d.client, "factures analysées": d.nb_factures, "montant": d.montant_total,
                                    "retard moyen (j)": d.retard_moyen, "retard max (j)": d.retard_max,
                                    "délai depuis émission (j)": d.delai_moyen_emission}
                                   for d in sorted(delais.values(), key=lambda d: -d.retard_moyen)]),
                     width="stretch", hide_index=True)
    else:
        st.info("Aucune facture client avec date de paiement : encaissements prévus à l'échéance (hypothèse optimiste).")

    st.subheader("5 points d'attention")
    for i, p in enumerate(points, 1):
        {"alerte": st.error, "vigilance": st.warning, "info": st.info}[p.niveau](f"**{i}. {p.titre}** — {p.texte}")

# ----------------------------------------------------------------- Exports --
with onglets[4]:
    dossier = stockage.dossier(client) / "exports"
    base_nom = f"tresorerie_{client}_{params.date_debut:%Y-%m-%d}"
    if st.button("Générer le PDF dirigeant et le classeur XLSX", type="primary"):
        f_pdf = pdf_dirigeant(prev, points, client, dossier / f"{base_nom}.pdf")
        f_xlsx = xlsx_detaille(prev, points, client, dossier / f"{base_nom}.xlsx", data["banque"], data["regles"], delais)
        st.session_state["exports"] = [str(f_pdf), str(f_xlsx)]
        stockage.sauver_parametres(client, params)
    for chemin in st.session_state.get("exports", []):
        from pathlib import Path
        p = Path(chemin)
        if p.exists():
            st.download_button(f"Télécharger {p.name}", p.read_bytes(), file_name=p.name, key=p.name)
    st.caption(f"Les fichiers sont aussi enregistrés dans `{dossier}`.")
