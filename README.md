# wxPython Wacom pressure test

Application wxPython avec contexte OpenGL pour tester la réponse à la pression d'un stylet (ex: Wacom) sous Windows 11.

## Prérequis

- Python 3.10+
- Pilote Wacom installé
- Dépendances Python:

```bash
pip install wxPython PyOpenGL
```

## Lancement

```bash
python app.py
```

## Utilisation

- Déplacez le stylet sur la zone OpenGL.
- Appuyez plus ou moins fort.
- La barre à droite et le disque central réagissent à la pression.
- Le graphe temporel (bas gauche) trace l’évolution de la pression dans le temps.
- La pression normalisée et la position sont affichées en bas et dans la barre de statut.

> Note: selon le pilote et l'API d'entrée exposée, la pression peut être transmise par des événements tablette dédiés ou via fallback souris.
