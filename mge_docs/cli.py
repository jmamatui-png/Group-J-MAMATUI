"""Ligne de commande : python -m mge_docs <commande>."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import generation, numerotation
from .catalogue import CATALOGUE_DEFAUT, CONFIG_DEFAUT, charger_catalogue, charger_config
from .fiche import FicheInvalide, charger_fiche
from .formatage import pct, xpf


def _charger(args):
    config = charger_config(args.config)
    catalogue = charger_catalogue(args.catalogue)
    fiche = charger_fiche(args.fiche, catalogue, config["conditions"]["engagement_mois"])
    return config, fiche


def _afficher_montants(fiche, m):
    if fiche.offre.mensuelle:
        print(f"  Par mois   : HT {xpf(m.ht)} + TGC {pct(m.taux_tgc)} {xpf(m.tgc)} = TTC {xpf(m.ttc)}")
        print(f"  Sur {m.nb_periodes} mois : HT {xpf(m.total_ht)} + TGC {xpf(m.total_tgc)} = TTC {xpf(m.total_ttc)}")
    else:
        print(f"  Forfait    : HT {xpf(m.ht)} + TGC {pct(m.taux_tgc)} {xpf(m.tgc)} = TTC {xpf(m.ttc)}")


def cmd_offres(args):
    for code, o in charger_catalogue(args.catalogue).items():
        prix = xpf(o.prix_ht) if o.prix_ht else f"{xpf(o.prix_ht_min)} à {xpf(o.prix_ht_max)}"
        unite = " HT / mois" if o.mensuelle else " HT (forfait)"
        print(f"{code:<24} {o.nom:<24} {prix}{unite}  {o.rythme}")


def cmd_verifier(args):
    config, fiche = _charger(args)
    taux = args.taux_tgc or config["conditions"]["taux_tgc"]
    print(f"Fiche valide : {fiche.raison_sociale} — {fiche.offre.nom}")
    _afficher_montants(fiche, generation.montants(fiche, taux))
    for a in fiche.avertissements:
        print(f"  ⚠ {a}")
    print(f"Prochain numéro : {numerotation.prochain_numero(args.registre)}")


def cmd_generer(args):
    config, fiche = _charger(args)
    for a in fiche.avertissements:
        print(f"⚠ {a}")
    manquants = generation.champs_cabinet_manquants(config)
    if manquants:
        print(f"⚠ Champs du cabinet à compléter dans {args.config} : {', '.join(manquants)}")
    docs = tuple(generation.DOCUMENTS) if args.document == "tous" else (args.document,)
    res = generation.generer(fiche, config, formats=args.format, sortie=args.sortie, registre=args.registre,
                             taux_tgc=args.taux_tgc, documents=docs)
    print(f"Numéro attribué : {res['numero']}")
    _afficher_montants(fiche, res["montants"])
    for f in res["fichiers"]:
        print(f"  → {f}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="mge-docs", description="Propositions commerciales et lettres de mission MGE Conseil")
    p.add_argument("--config", type=Path, default=CONFIG_DEFAUT)
    p.add_argument("--catalogue", type=Path, default=CATALOGUE_DEFAUT)
    p.add_argument("--registre", type=Path, default=generation.REGISTRE_DEFAUT)
    sp = p.add_subparsers(dest="commande", required=True)

    sp.add_parser("offres", help="lister le catalogue").set_defaults(func=cmd_offres)

    v = sp.add_parser("verifier", help="valider une fiche et afficher les montants, sans rien générer")
    v.add_argument("fiche", type=Path)
    v.add_argument("--taux-tgc")
    v.set_defaults(func=cmd_verifier)

    g = sp.add_parser("generer", help="générer les documents")
    g.add_argument("fiche", type=Path)
    g.add_argument("--format", nargs="+", choices=generation.FORMATS, default=list(generation.FORMATS))
    g.add_argument("--document", choices=["tous", *generation.DOCUMENTS], default="tous")
    g.add_argument("--sortie", type=Path, default=generation.SORTIE_DEFAUT)
    g.add_argument("--taux-tgc", help="taux de TGC en %% (remplace celui de config/mge.yaml)")
    g.set_defaults(func=cmd_generer)

    args = p.parse_args(argv)
    try:
        args.func(args)
    except FicheInvalide as e:
        print(e, file=sys.stderr)
        return 2
    except (ValueError, FileNotFoundError) as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
