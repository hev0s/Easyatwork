# EasyAtWork to Google Calendar Sync 📅

Ce script automatise la récupération de vos horaires de travail depuis **EasyAtWork** (utilisé par McDonald's et d'autres) et les ajoute automatiquement à votre **Google Agenda**.

## Fonctionnalités 🚀
- 🕵️‍♂️ **Mode furtif** : Utilise une version indétectable de Chrome pour éviter les blocages.
- 🔄 **Anti-doublons** : Vérifie l'historique pour ne pas ajouter deux fois le même horaire.
- 🤝 **Partage** : Ajoute automatiquement un invité (conjoint(e), ami) à l'événement.
- 🧹 **Nettoyage** : Supprime automatiquement les vieux historiques pour rester léger.
- 🔐 **Sécurisé** : Utilise un fichier `.env` pour vos identifiants.

## Prérequis
- Google Chrome installé.
- Python 3.x installé.

## Installation

1. Clonez ce dépôt :
   ```bash
   git clone [https://github.com/VOTRE_NOM_UTILISATEUR/EasyAtWork-Sync.git](https://github.com/VOTRE_NOM_UTILISATEUR/EasyAtWork-Sync.git)
   cd EasyAtWork-Sync
