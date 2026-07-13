#!/usr/bin/env python3
"""Valide le manifest et les fichiers de cours du catalogue.

Vérifie que chaque cours importable par D and R Learn est complet :
- le manifest référence des fichiers existants, sans doublon d'id ni de path,
  et ses cardCount correspondent au nombre réel de cartes ;
- chaque fichier de cours est bien référencé par le manifest ;
- chaque carte a un recto (recto/question/front) et un verso (verso/answer/back) ;
- chaque carte a des distracteurs : soit un objet {easy, medium, hard}
  (ou {facile, moyen, difficile}) avec au moins 3 chaînes non vides par niveau,
  soit une liste plate d'au moins 3 chaînes non vides ;
- qualité QCM : aucun distracteur identique à la bonne réponse, aucun doublon
  de distracteur au sein d'une carte, aucun recto en double dans un cours
  (comparaison insensible à la casse et à la normalisation Unicode).

Sort avec le code 1 et la liste des erreurs si quelque chose ne va pas.
"""

import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN_DISTRACTORS = 3

FRONT_KEYS = {"recto", "question", "front"}
BACK_KEYS = {"verso", "answer", "back"}
LEVEL_KEY_SETS = ({"easy", "medium", "hard"}, {"facile", "moyen", "difficile"})


def norm(value):
    return unicodedata.normalize("NFKC", value).strip().lower()


def non_empty_strings(values, minimum):
    return (
        isinstance(values, list)
        and len(values) >= minimum
        and all(isinstance(v, str) and v.strip() for v in values)
    )


def check_card(rel, index, card, errors):
    where = f"{rel} carte {index}"
    if not isinstance(card, dict):
        errors.append(f"{where}: la carte n'est pas un objet JSON")
        return
    if not (FRONT_KEYS & card.keys()):
        errors.append(f"{where}: aucun champ recto/question/front")
    if not (BACK_KEYS & card.keys()):
        errors.append(f"{where}: aucun champ verso/answer/back")

    answer = next((card[k] for k in BACK_KEYS if isinstance(card.get(k), str)), None)

    distractors = card.get("distractors", card.get("distracteurs"))
    if distractors is None:
        errors.append(f"{where}: pas de distracteurs")
        return
    if isinstance(distractors, dict):
        if not any(keys <= distractors.keys() for keys in LEVEL_KEY_SETS):
            errors.append(
                f"{where}: clés de distracteurs inattendues {sorted(distractors)}"
                " (attendu easy/medium/hard ou facile/moyen/difficile)"
            )
        levels = distractors.items()
    elif isinstance(distractors, list):
        levels = [(None, distractors)]
    else:
        errors.append(f"{where}: type de distracteurs invalide ({type(distractors).__name__})")
        return

    for level, values in levels:
        label = f"distractors.{level}" if level else "la liste de distracteurs"
        if not non_empty_strings(values, MIN_DISTRACTORS):
            errors.append(
                f"{where}: {label} doit contenir au moins"
                f" {MIN_DISTRACTORS} chaînes non vides"
            )

    # Qualité QCM : un distracteur identique à la bonne réponse rendrait la
    # question insoluble, un doublon réduit le choix réel proposé à l'élève.
    seen = set()
    for level, values in levels:
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, str):
                continue
            key = norm(value)
            if answer is not None and key == norm(answer):
                errors.append(f"{where}: distracteur identique à la bonne réponse : {value!r}")
            if key in seen:
                errors.append(f"{where}: distracteur en double : {value!r}")
            seen.add(key)


def main():
    errors = []

    manifest_path = ROOT / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"manifest.json illisible : {exc}", file=sys.stderr)
        return 1

    courses = manifest.get("courses")
    if not isinstance(courses, list) or not courses:
        print("manifest.json : le champ 'courses' doit être une liste non vide", file=sys.stderr)
        return 1

    seen_ids, seen_paths = set(), set()
    card_counts = {}

    for entry in courses:
        cid, path = entry.get("id"), entry.get("path")
        if not cid:
            errors.append(f"manifest : cours sans id ({entry.get('title')!r})")
        elif cid in seen_ids:
            errors.append(f"manifest : id en double {cid!r}")
        seen_ids.add(cid)

        if not path:
            errors.append(f"manifest : cours {cid!r} sans path")
            continue
        if path in seen_paths:
            errors.append(f"manifest : path en double {path!r}")
        seen_paths.add(path)

        if not (ROOT / path).is_file():
            errors.append(f"manifest : {path} n'existe pas")
        else:
            card_counts[path] = entry.get("cardCount")

    course_files = sorted(
        p for p in ROOT.rglob("*.json")
        if p != manifest_path and not p.is_relative_to(ROOT / "scripts")
    )
    checked_cards = 0

    for course_path in course_files:
        rel = course_path.relative_to(ROOT).as_posix()
        if rel not in seen_paths:
            errors.append(f"{rel}: fichier de cours absent du manifest")
        try:
            course = json.loads(course_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: JSON invalide ({exc})")
            continue

        if not (course.get("title") or course.get("titre")):
            errors.append(f"{rel}: aucun champ title/titre")

        cards = course.get("cards")
        if not isinstance(cards, list) or not cards:
            errors.append(f"{rel}: le champ 'cards' doit être une liste non vide")
            continue

        expected = card_counts.get(rel)
        if expected is not None and expected != len(cards):
            errors.append(
                f"{rel}: cardCount du manifest ({expected}) ≠ nombre réel de cartes ({len(cards)})"
            )

        seen_fronts = {}
        for index, card in enumerate(cards):
            check_card(rel, index, card, errors)
            checked_cards += 1
            if isinstance(card, dict):
                front = next((card[k] for k in FRONT_KEYS if isinstance(card.get(k), str)), None)
                if front is not None:
                    key = norm(front)
                    if key in seen_fronts:
                        errors.append(
                            f"{rel}: cartes {seen_fronts[key]} et {index} ont le même recto : {front!r}"
                        )
                    seen_fronts.setdefault(key, index)

    if errors:
        print(f"{len(errors)} erreur(s) détectée(s) :", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"OK : {len(course_files)} cours et {checked_cards} cartes validés, distracteurs complets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
