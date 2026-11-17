"""Les 5 points d'attention du rapport dirigeant : uniquement des faits calculés."""
from __future__ import annotations

from dataclasses import dataclass

from .delais import DelaiClient
from .imports import Facture
from .prevision import BASE, PERTE, RETARD, SRC_CLIENTS, Prevision, premier_client
from .valeurs import xpf


@dataclass(frozen=True)
class Point:
    titre: str
    texte: str
    niveau: str   # "alerte", "vigilance", "info"


def _sem(s) -> str:
    return f"semaine {s.numero} (du {s.debut:%d/%m} au {s.fin:%d/%m})"


def points_attention(prev: dict[str, Prevision], clients: list[Facture], delais: dict[str, DelaiClient]) -> list[Point]:
    base, ret, per = prev[BASE], prev[RETARD], prev[PERTE]
    p = base.parametres
    pts = []

    # 1. Point bas et seuil (scénario de base)
    m = base.solde_min
    if base.alertes:
        a = base.alertes[0]
        pts.append(Point("Passage sous le seuil", f"Dans le scénario de base, le solde passe sous le seuil de {xpf(p.seuil)} "
                         f"dès la {_sem(a)} ({xpf(a.solde_fin)}). Point bas : {xpf(m.solde_fin)} en {_sem(m)}. "
                         f"{len(base.alertes)} semaine(s) sur {p.nb_semaines} sous le seuil.", "alerte"))
    else:
        pts.append(Point("Point bas de trésorerie", f"Dans le scénario de base, le point bas est de {xpf(m.solde_fin)} en "
                         f"{_sem(m)}, soit une marge de {xpf(m.solde_fin - p.seuil)} au-dessus du seuil de {xpf(p.seuil)}.",
                         "info"))

    # 2. Sensibilité aux retards clients
    mr = ret.solde_min
    txt = (f"Si tous les clients payent {p.retard_scenario_jours} jours plus tard que d'habitude, le point bas descend à "
           f"{xpf(mr.solde_fin)} en {_sem(mr)} (écart de {xpf(mr.solde_fin - m.solde_fin)} par rapport à la base).")
    if ret.alertes:
        txt += f" Le seuil est franchi dès la {_sem(ret.alertes[0])}."
    pts.append(Point("Sensibilité aux retards de paiement", txt, "alerte" if ret.alertes else "vigilance"))

    # 3. Dépendance au 1er client
    pc = premier_client(clients)
    enc_total = sum(f.montant for f in base.flux if f.source == SRC_CLIENTS)
    enc_pc = sum(f.montant for f in base.flux if f.source == SRC_CLIENTS and f.tiers == pc)
    part = round(100 * enc_pc / enc_total) if enc_total else 0
    mp = per.solde_min
    if pc:
        txt = (f"{pc} est le premier client (plus gros montant facturé) et représente {part} % des encaissements clients "
               f"attendus sur la période ({xpf(enc_pc)}). Sans ses paiements, le point bas serait de {xpf(mp.solde_fin)} "
               f"en {_sem(mp)}.")
    else:
        txt = "Aucune facture client n'est saisie : la dépendance client ne peut pas être évaluée."
    pts.append(Point("Dépendance au premier client", txt, "alerte" if per.alertes else ("vigilance" if part >= 30 else "info")))

    # 4. Créances échues et délais réels
    echues = [f for f in clients if f.ouverte and f.echeance < p.date_debut]
    douteuses = [f for f, motif in base.exclus if "douteuse" in motif]
    if echues:
        txt = (f"{len(echues)} facture(s) client échue(s) au départ, pour {xpf(sum(f.montant_ttc for f in echues))} TTC")
        txt += (f", dont {xpf(sum(f.montant_ttc for f in douteuses))} échues depuis plus de {p.seuil_douteux_jours} jours "
                f"et exclues de la prévision." if douteuses else ".")
    else:
        txt = "Aucune facture client échue au départ."
    if delais:
        pire = max(delais.values(), key=lambda d: (d.retard_moyen, d.client))
        txt += f" Retard moyen le plus élevé : {pire.client}, {pire.retard_moyen} jours après échéance ({pire.nb_factures} facture(s) analysée(s))."
    else:
        txt += " Aucun historique de paiement : les encaissements sont prévus à l'échéance, ce qui est probablement optimiste."
    pts.append(Point("Créances clients", txt, "vigilance" if echues or not delais else "info"))

    # 5. Semaine la plus chargée en décaissements
    s = max(base.semaines, key=lambda s: (s.decaissements, -s.numero))
    postes: dict[str, int] = {}
    for f in base.flux_semaine(s.numero):
        if f.montant < 0:
            cle = f.tiers or f.source
            postes[cle] = postes.get(cle, 0) - f.montant
    top = sorted(postes.items(), key=lambda kv: -kv[1])[:3]
    reportes = sum(-f.montant for f in base.flux if f.reporte and f.montant < 0)
    txt = f"Les décaissements les plus lourds tombent en {_sem(s)} : {xpf(s.decaissements)}"
    txt += (", principalement " + ", ".join(f"{k} ({xpf(v)})" for k, v in top) + ".") if top else "."
    if reportes:
        txt += f" {xpf(reportes)} de dettes déjà échues au départ sont prévues en semaine 1."
    pts.append(Point("Pic de décaissements", txt, "vigilance" if s.decaissements > s.solde_debut else "info"))
    return pts
