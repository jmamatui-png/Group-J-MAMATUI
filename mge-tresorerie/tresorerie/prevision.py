"""Prévision de trésorerie hebdomadaire et scénarios."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from .categorisation import Regle, categoriser
from .delais import DelaiClient, retard_global
from .imports import FREQUENCES, Charge, Facture, LigneBanque
from .valeurs import ajouter_mois, lundi

BASE, RETARD, PERTE = "base", "retard", "perte"
SRC_CLIENTS, SRC_FOURN, SRC_CHARGES, SRC_DIVERS = (
    "Factures clients", "Factures fournisseurs", "Charges récurrentes", "Dépenses diverses (moyenne historique)")


@dataclass(frozen=True)
class Parametres:
    date_debut: date                 # ramenée au lundi
    solde_initial: int               # solde bancaire au matin du lundi de départ
    seuil: int = 0                   # seuil d'alerte
    nb_semaines: int = 13
    retard_scenario_jours: int = 30
    seuil_douteux_jours: int = 90    # factures clients échues depuis plus longtemps : exclues (prudence)
    categories_divers: tuple[str, ...] = ()   # catégories bancaires extrapolées à leur moyenne hebdomadaire
    semaines_historique: int = 13

    def __post_init__(self):
        object.__setattr__(self, "date_debut", lundi(self.date_debut))
        if not 1 <= self.nb_semaines <= 52:
            raise ValueError("nombre de semaines entre 1 et 52")

    @property
    def date_fin(self) -> date:
        return self.date_debut + timedelta(days=7 * self.nb_semaines - 1)


@dataclass(frozen=True)
class Flux:
    date: date
    montant: int          # signé : + encaissement, − décaissement
    source: str
    tiers: str
    libelle: str
    date_origine: date
    reporte: bool = False  # date d'origine antérieure au départ : ramenée en semaine 1


@dataclass(frozen=True)
class Semaine:
    numero: int
    debut: date
    fin: date
    solde_debut: int
    encaissements: int    # ≥ 0
    decaissements: int    # ≥ 0
    solde_fin: int
    sous_seuil: bool

    @property
    def variation(self) -> int:
        return self.solde_fin - self.solde_debut


@dataclass
class Prevision:
    scenario: str
    titre: str
    parametres: Parametres
    semaines: list[Semaine]
    flux: list[Flux]                                        # flux dans l'horizon
    hors_horizon: list[Flux] = field(default_factory=list)
    exclus: list[tuple[Facture, str]] = field(default_factory=list)
    avertissements: list[str] = field(default_factory=list)

    @property
    def solde_min(self) -> Semaine:
        return min(self.semaines, key=lambda s: (s.solde_fin, s.numero))

    @property
    def alertes(self) -> list[Semaine]:
        return [s for s in self.semaines if s.sous_seuil]

    def flux_semaine(self, numero: int) -> list[Flux]:
        s = self.semaines[numero - 1]
        return [f for f in self.flux if s.debut <= f.date <= s.fin]


def premier_client(factures_clients: list[Facture]) -> str | None:
    """1er client = plus gros montant TTC facturé (factures ouvertes + soldées)."""
    totaux: dict[str, int] = {}
    for f in factures_clients:
        totaux[f.tiers] = totaux.get(f.tiers, 0) + f.montant_ttc
    return max(sorted(totaux), key=lambda c: totaux[c]) if totaux else None


def occurrences(c: Charge, debut: date, fin: date) -> list[date]:
    pas = FREQUENCES[c.frequence]
    dates, k = [], 0
    while True:
        if c.frequence == "hebdomadaire":
            d = c.prochaine_echeance + timedelta(weeks=k)
        elif pas is None:
            d = c.prochaine_echeance if k == 0 else None
        else:
            d = ajouter_mois(c.prochaine_echeance, pas * k)
        if d is None or d > fin or (c.date_fin and d > c.date_fin):
            return dates
        if d >= debut:
            dates.append(d)
        k += 1


def moyenne_divers(banque: list[LigneBanque], regles: list[Regle], p: Parametres) -> int:
    """Moyenne hebdomadaire des débits des catégories choisies, sur les semaines complètes avant le départ."""
    if not p.categories_divers or not banque:
        return 0
    debut_hist = max(lundi(banque[0].date) + (timedelta(0) if banque[0].date.weekday() == 0 else timedelta(weeks=1)),
                     p.date_debut - timedelta(weeks=p.semaines_historique))
    nb = (p.date_debut - debut_hist).days // 7
    if nb <= 0:
        return 0
    total = sum(-l.montant for l in banque
                if debut_hist <= l.date < p.date_debut and l.montant < 0
                and categoriser(l.libelle, l.montant, regles) in p.categories_divers)
    return (total + nb // 2) // nb


def generer_flux(clients: list[Facture], fournisseurs: list[Facture], charges: list[Charge],
                 delais: dict[str, DelaiClient], p: Parametres, scenario: str = BASE,
                 divers_hebdo: int = 0, client_perdu: str | None = None):
    flux, exclus, avert = [], [], []
    retard_defaut = retard_global(delais)

    def ajouter(d, montant, source, tiers, libelle):
        flux.append(Flux(max(d, p.date_debut), montant, source, tiers, libelle, d, d < p.date_debut))

    for f in clients:
        if not f.ouverte:
            continue
        if scenario == PERTE and f.tiers == client_perdu:
            exclus.append((f, "scénario perte du 1er client"))
            continue
        echu = (p.date_debut - f.echeance).days
        if echu > p.seuil_douteux_jours:
            exclus.append((f, f"échue depuis {echu} jours : considérée comme douteuse"))
            continue
        retard = delais[f.tiers].retard_moyen if f.tiers in delais else retard_defaut
        if scenario == RETARD:
            retard += p.retard_scenario_jours
        ajouter(f.echeance + timedelta(days=retard), f.montant_ttc, SRC_CLIENTS, f.tiers,
                f"Facture {f.numero or ''} échéance {f.echeance:%d/%m/%Y}".replace("  ", " "))

    for f in fournisseurs:
        if f.ouverte:
            ajouter(f.echeance, -f.montant_ttc, SRC_FOURN, f.tiers,
                    f"Facture {f.numero or ''} échéance {f.echeance:%d/%m/%Y}".replace("  ", " "))

    for c in charges:
        if c.prochaine_echeance < p.date_debut:
            avert.append(f"Charge « {c.libelle} » : prochaine échéance ({c.prochaine_echeance:%d/%m/%Y}) antérieure "
                         f"au départ ; les occurrences passées sont supposées payées.")
        signe = 1 if c.sens == "encaissement" else -1
        for d in occurrences(c, p.date_debut, p.date_fin):
            ajouter(d, signe * c.montant, SRC_CHARGES, c.categorie, c.libelle)

    if divers_hebdo:
        for i in range(p.nb_semaines):
            d = p.date_debut + timedelta(weeks=i)
            ajouter(d, -divers_hebdo, SRC_DIVERS, "", ", ".join(p.categories_divers))
    return flux, exclus, avert


def construire(flux: list[Flux], p: Parametres) -> tuple[list[Semaine], list[Flux], list[Flux]]:
    dans, hors = [], []
    for f in flux:
        (dans if f.date <= p.date_fin else hors).append(f)
    semaines, solde = [], p.solde_initial
    for i in range(p.nb_semaines):
        deb = p.date_debut + timedelta(weeks=i)
        fin = deb + timedelta(days=6)
        fs = [f for f in dans if deb <= f.date <= fin]
        enc = sum(f.montant for f in fs if f.montant > 0)
        dec = -sum(f.montant for f in fs if f.montant < 0)
        solde_fin = solde + enc - dec
        semaines.append(Semaine(i + 1, deb, fin, solde, enc, dec, solde_fin, solde_fin < p.seuil))
        solde = solde_fin
    return semaines, dans, hors


TITRES = {BASE: "Base", RETARD: "Retard clients +{j} jours", PERTE: "Perte du 1er client ({c})"}


def prevoir(clients, fournisseurs, charges, delais, p: Parametres, banque=(), regles=()) -> dict[str, Prevision]:
    divers = moyenne_divers(list(banque), list(regles), p)
    perdu = premier_client(clients)
    res = {}
    for sc in (BASE, RETARD, PERTE):
        flux, exclus, avert = generer_flux(clients, fournisseurs, charges, delais, p, sc, divers, perdu)
        semaines, dans, hors = construire(flux, p)
        titre = TITRES[sc].format(j=p.retard_scenario_jours, c=perdu or "aucun client")
        res[sc] = Prevision(sc, titre, p, semaines, dans, hors, exclus, avert)
    return res
