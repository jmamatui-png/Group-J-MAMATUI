"""Calcul des indicateurs. Fonctions pures, testées : aucune lecture de fichier ici."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from .donnees import Facture, Mouvement, Paiement, Saisie, norm
from .valeurs import ajouter_mois

GROUPE = "groupe"


def mois_de(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def fin_de_mois(mois: str) -> date:
    a, m = int(mois[:4]), int(mois[5:])
    return ajouter_mois(date(a, m, 1), 1) - timedelta(days=1)


def liste_mois(debut: str, fin: str) -> list[str]:
    res, d = [], date(int(debut[:4]), int(debut[5:]), 1)
    while mois_de(d) <= fin:
        res.append(mois_de(d))
        d = ajouter_mois(d, 1)
    return res


def ratio(a, b) -> float | None:
    return None if a is None or not b else a / b


def arrondi(x) -> int:
    return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@dataclass
class Donnees:
    factures: list[Facture]
    paiements: list[Paiement]
    banque: list[Mouvement]
    saisie: Saisie
    entites: dict[str, dict]                         # code -> {nom, noms_tiers}
    soldes_initiaux: dict[str, dict[str, int]] = field(default_factory=dict)
    jours_retard: int = 30

    def __post_init__(self):
        self._intra = {norm(n): code for code, e in self.entites.items() for n in e.get("noms_tiers", []) + [e.get("nom", "")]}
        self._paye: dict[tuple[str, str], list[Paiement]] = defaultdict(list)
        for p in self.paiements:
            self._paye[(p.entite, p.ref_facture)].append(p)

    def est_intragroupe(self, f: Facture) -> bool:
        """Facture adressée à une autre entité du groupe."""
        code = self._intra.get(norm(f.tiers))
        return code is not None and code != f.entite

    def factures_de(self, entite: str | None = None, externes=False):
        return [f for f in self.factures
                if (entite in (None, GROUPE) or f.entite == entite) and not (externes and self.est_intragroupe(f))]

    # ------------------------------------------------------------------ CA ---
    def ca_ht(self, entite: str, debut: date, fin: date) -> int:
        """CA HT facturé entre deux dates incluses. Groupe = hors facturation intragroupe."""
        return sum(f.ht for f in self.factures_de(entite, externes=entite == GROUPE) if debut <= f.date <= fin)

    def ca_ht_mois(self, entite: str, mois: str) -> int:
        return self.ca_ht(entite, date(int(mois[:4]), int(mois[5:]), 1), fin_de_mois(mois))

    def ca_intragroupe_mois(self, mois: str) -> int:
        return sum(f.ht for f in self.factures if self.est_intragroupe(f) and mois_de(f.date) == mois)

    def ca_par_client(self, entite: str, debut: date, fin: date) -> dict[str, int]:
        r: dict[str, int] = defaultdict(int)
        for f in self.factures_de(entite):
            if debut <= f.date <= fin:
                r[f.tiers] += f.ht
        return dict(r)

    def part_premier_client(self, entite: str, debut: date, fin: date) -> tuple[str | None, float | None]:
        r = self.ca_par_client(entite, debut, fin)
        total = sum(r.values())
        if total <= 0:
            return None, None
        client = max(sorted(r), key=lambda c: r[c])
        return client, r[client] / total

    # ---------------------------------------------------------- Trésorerie ---
    def tresorerie(self, entite: str, au: date) -> int:
        """Solde bancaire en fin de journée « au » (soldes initiaux + écritures jusqu'à cette date)."""
        ents = list(self.entites) if entite == GROUPE else [entite]
        total = sum(sum(self.soldes_initiaux.get(e, {}).values()) for e in ents)
        return total + sum(m.montant for m in self.banque if m.entite in ents and m.date <= au)

    # ------------------------------------------------------------ Créances ---
    def reste_du(self, f: Facture, au: date) -> int:
        paye = sum(p.montant for p in self._paye.get((f.entite, f.ref), []) if p.date <= au)
        return max(0, f.ttc - paye)

    def creances_echues(self, entite: str, au: date, jours: int | None = None) -> list[tuple[Facture, int]]:
        """Factures émises au plus tard le jour « au », échues depuis plus de N jours, avec leur reste dû TTC."""
        n = self.jours_retard if jours is None else jours
        res = []
        for f in self.factures_de(entite, externes=entite == GROUPE):
            if f.ttc > 0 and f.date <= au and (au - f.echeance).days > n:
                reste = self.reste_du(f, au)
                if reste:
                    res.append((f, reste))
        return res

    def creances_plus_30(self, entite: str, au: date) -> int:
        return sum(r for _, r in self.creances_echues(entite, au))

    def encaissements(self, entite: str, debut: date, fin: date) -> int:
        ents = list(self.entites) if entite == GROUPE else [entite]
        refs_intra = {(f.entite, f.ref) for f in self.factures if self.est_intragroupe(f)}
        return sum(p.montant for p in self.paiements if p.entite in ents and debut <= p.date <= fin
                   and not (entite == GROUPE and (p.entite, p.ref_facture) in refs_intra))

    # --------------------------------------------------------- Saisie / mois ---
    def s(self, mois: str, entite: str, champ: str) -> int | None:
        return self.saisie.get(mois, entite, champ)

    def couts_directs_totaux(self, mois: str, entite: str) -> int | None:
        champs = ["couts_directs"] + (["sous_traitance", "carburant"] if entite == "terrawaves" else [])
        vals = [self.s(mois, entite, c) for c in champs]
        return None if all(v is None for v in vals) else sum(v or 0 for v in vals)

    def indicateurs_mois(self, entite: str, mois: str) -> dict:
        """CA HT, marge, charges fixes, trésorerie fin de mois, créances > N jours fin de mois."""
        fin = fin_de_mois(mois)
        if entite != GROUPE:
            ca = self.ca_ht_mois(entite, mois)
            cd = self.couts_directs_totaux(mois, entite)
            cf = self.s(mois, entite, "charges_fixes")
            return {"ca_ht": ca, "marge": None if cd is None else ca - cd, "charges_fixes": cf,
                    "resultat": None if cd is None or cf is None else ca - cd - cf,
                    "tresorerie": self.tresorerie(entite, fin), "creances_30": self.creances_plus_30(entite, fin)}
        par = {e: self.indicateurs_mois(e, mois) for e in self.entites}
        intra_ca = self.ca_intragroupe_mois(mois)
        intra_cd = sum(self.s(mois, e, "couts_directs_intragroupe") or 0 for e in self.entites)
        intra_cf = sum(self.s(mois, e, "charges_fixes_intragroupe") or 0 for e in self.entites)
        marges = [p["marge"] for p in par.values()]
        cfs = [p["charges_fixes"] for p in par.values()]
        marge = None if any(m is None for m in marges) else sum(marges) - intra_ca + intra_cd
        cf = None if any(c is None for c in cfs) else sum(cfs) - intra_cf
        return {"ca_ht": sum(p["ca_ht"] for p in par.values()) - intra_ca, "marge": marge, "charges_fixes": cf,
                "resultat": None if marge is None or cf is None else marge - cf,
                "tresorerie": sum(p["tresorerie"] for p in par.values()),
                "creances_30": self.creances_plus_30(GROUPE, fin),
                "ecart_intragroupe": intra_ca - intra_cd - intra_cf}

    # ------------------------------------------------------------ Terrawaves ---
    def terrawaves_mois(self, mois: str, seuil: float) -> dict:
        e = "terrawaves"
        ca = self.ca_ht_mois(e, mois)
        client, part = self.part_premier_client(e, date(int(mois[:4]), int(mois[5:]), 1), fin_de_mois(mois))
        st = self.s(mois, e, "sous_traitance")
        return {"premier_client": client, "part_premier_client": part, "alerte_concentration": part is not None and part > seuil,
                "heures_par_fourgon": ratio(self.s(mois, e, "heures_vendues"), self.s(mois, e, "fourgons")),
                "carburant_par_km": ratio(self.s(mois, e, "carburant"), self.s(mois, e, "km")),
                "sous_traitance": st, "sous_traitance_pct_ca": ratio(st, ca)}

    # ------------------------------------------------------------------- MGE ---
    def mge_mois(self, mois: str, jours_dispo_defaut: int) -> dict:
        e = "mge"
        dispo = self.s(mois, e, "jours_disponibles") or jours_dispo_defaut
        c, r, d = (self.s(mois, e, k) for k in ("contacts", "rendez_vous", "diagnostics"))
        jf = self.s(mois, e, "jours_factures")
        return {"mrr_signe": self.s(mois, e, "mrr_signe"), "jours_factures": jf, "jours_disponibles": dispo,
                "taux_occupation": ratio(jf, dispo), "contacts": c, "rendez_vous": r, "diagnostics": d,
                "conversion_rdv": ratio(r, c), "conversion_diagnostic": ratio(d, r)}

    # ------------------------------------------------------------- Personnel ---
    def personnel(self, mois_liste: list[str], taux: float | None) -> list[dict]:
        res, cumul_annee, cumul_prov = [], {}, {}
        for m in mois_liste:
            p = self.s(m, "personnel", "prelevement_dirigeant")
            prov = None if p is None or taux is None else arrondi(Decimal(p) * Decimal(str(taux)))
            a = m[:4]
            cumul_annee[a] = cumul_annee.get(a, 0) + (p or 0)
            cumul_prov[a] = cumul_prov.get(a, 0) + (prov or 0)
            res.append({"mois": m, "preleve": p, "provision": prov, "cumul_preleve": cumul_annee[a],
                        "cumul_provision": cumul_prov[a] if taux is not None else None})
        return res


# ------------------------------------------------------------------ Lundi ---
@dataclass(frozen=True)
class Chiffre:
    cle: str
    libelle: str
    valeur: float | None
    precedent: float | None
    format: str            # "xpf" ou "pct"
    sens_favorable: int    # +1 si une hausse est bonne, −1 si une baisse est bonne
    alerte: bool = False
    detail: str = ""

    @property
    def variation(self):
        return None if self.valeur is None or self.precedent is None else self.valeur - self.precedent


def lundi_chiffres(d: Donnees, lundi: date, seuil_part: float) -> list[Chiffre]:
    """Les 5 chiffres du lundi, au dimanche soir précédent, comparés à la semaine d'avant."""
    fin = lundi - timedelta(days=1)          # dimanche soir
    fin_prec = fin - timedelta(days=7)

    def ca30(f):
        return d.ca_ht(GROUPE, f - timedelta(days=29), f)

    def enc7(f):
        return d.encaissements(GROUPE, f - timedelta(days=6), f)

    def part90(f):
        return d.part_premier_client("terrawaves", f - timedelta(days=89), f)

    c, p = part90(fin)
    _, p_prec = part90(fin_prec)
    return [
        Chiffre("tresorerie", "Trésorerie groupe", d.tresorerie(GROUPE, fin), d.tresorerie(GROUPE, fin_prec), "xpf", 1),
        Chiffre("creances", f"Créances > {d.jours_retard} j", d.creances_plus_30(GROUPE, fin),
                d.creances_plus_30(GROUPE, fin_prec), "xpf", -1),
        Chiffre("ca30", "CA HT 30 jours", ca30(fin), ca30(fin_prec), "xpf", 1),
        Chiffre("enc7", "Encaissements 7 jours", enc7(fin), enc7(fin_prec), "xpf", 1),
        Chiffre("part", "1er client Terrawaves (90 j)", p, p_prec, "pct", -1,
                alerte=p is not None and p > seuil_part, detail=c or ""),
    ]


def lundi_mouvements(d: Donnees, lundi: date, n: int = 5) -> dict[str, list]:
    """Ce qui a bougé pendant la semaine écoulée (lundi précédent -> dimanche)."""
    fin = lundi - timedelta(days=1)
    debut = fin - timedelta(days=6)
    avant = debut - timedelta(days=1)
    deja = {(f.entite, f.ref) for f, _ in d.creances_echues(GROUPE, avant)}
    nouvelles = sorted(((f, r) for f, r in d.creances_echues(GROUPE, fin) if (f.entite, f.ref) not in deja),
                       key=lambda x: -x[1])
    factures = sorted((f for f in d.factures_de(GROUPE, externes=True) if debut <= f.date <= fin), key=lambda f: -f.ht)
    paiements = sorted((p for p in d.paiements if debut <= p.date <= fin), key=lambda p: -p.montant)
    return {"periode": (debut, fin), "nouvelles_creances_30": nouvelles[:n], "factures": factures[:n], "paiements": paiements[:n]}
