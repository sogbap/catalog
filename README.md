# Catalogue de cours D and R Learn

Ce dépôt contient les cours téléchargeables par l'application **D and R Learn** :
un `manifest.json` à la racine qui liste les cours, et un fichier JSON par cours.

```
manifest.json
histoire/terminale/*.json
geographie/terminale/*.json
hggsp/terminale/*.json
jp/koukou/rekishi-sougou/*.json
```

## Contrat de format (côté app)

L'app importe un cours via `CatalogCourseImporter.importCourse(from:context:)`,
qui décode le JSON puis alimente le cache de distracteurs
(`DistractorCacheManager.seedDistractors(easy:medium:hard:into:)`).
Le décodeur accepte les variantes de clés suivantes :

| Champ | Clés acceptées |
|---|---|
| Titre du cours | `title`, `titre` |
| Question (recto) | `recto`, `question`, `front` |
| Réponse (verso) | `verso`, `answer`, `back` |
| Distracteurs | objet `{easy, medium, hard}` (ou `{facile, moyen, difficile}`), ou liste plate |

Ce dépôt utilise la convention : `title`, `recto`, `verso`,
`distractors: {easy, medium, hard}` avec **exactement 3 distracteurs par niveau**.

### `manifest.json`

Chaque entrée de `courses` :

```json
{
  "id": "histoire-terminale-crise-1929",
  "title": "La crise de 1929",
  "emoji": "📉",
  "subject": "history",
  "country": "fr",
  "language": "fr",
  "courseDescription": "…",
  "cardCount": 16,
  "version": 1,
  "path": "histoire/terminale/crise-1929.json",
  "level": "Terminale",
  "theme": "…"
}
```

`path` est relatif à la racine du dépôt et `cardCount` doit correspondre au
nombre réel de cartes du fichier.

### Fichier de cours

```json
{
  "id": "…",
  "title": "…",
  "emoji": "…",
  "subject": "…",
  "country": "fr",
  "courseDescription": "…",
  "lesson": "<h1>…</h1> (HTML de la leçon)",
  "questionLang": "fr",
  "answerLang": "fr",
  "version": 1,
  "level": "…",
  "theme": "…",
  "cards": [
    {
      "recto": "Question ?",
      "verso": "Bonne réponse",
      "explanation": "Pourquoi c'est la bonne réponse.",
      "tags": ["notion"],
      "distractors": {
        "easy":   ["…", "…", "…"],
        "medium": ["…", "…", "…"],
        "hard":   ["…", "…", "…"]
      }
    }
  ]
}
```

## Règles de qualité

Validées par la CI (`.github/workflows/validate.yml`) via
`scripts/validate_catalog.py` sur chaque push et pull request :

- le manifest référence des fichiers existants, sans doublon d'`id` ni de `path`,
  et ses `cardCount` sont exacts ; aucun fichier de cours orphelin ;
- chaque carte a un recto, un verso et des distracteurs complets
  (≥ 3 chaînes non vides par niveau) ;
- aucun distracteur identique à la bonne réponse, aucun distracteur en double
  au sein d'une carte, aucun recto en double dans un cours.

Pour valider en local :

```sh
python3 scripts/validate_catalog.py
```

## Ajouter un cours

1. Créer le fichier JSON sous `<matière>/<niveau>/…json` en suivant le format
   ci-dessus (3 distracteurs par niveau pour chaque carte).
2. Ajouter l'entrée correspondante dans `manifest.json` (avec le bon `cardCount`).
3. Lancer `python3 scripts/validate_catalog.py` et corriger les erreurs éventuelles.
