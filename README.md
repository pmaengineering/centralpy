# A Python client for ODK Central

ODK Central has an [API][api], and this Python package interacts with it. The use cases in this package were written to support PMA data management purposes, but the package can be extended for other use cases as well.

[api]: https://odkcentral.docs.apiary.io/#

# Installation

First, make sure Python3 (at least version 3.6) is installed. 

Use `pip` to install this package with

```
python3 -m pip install centralpy
```

From here, the program runs by using either the installed script, e.g.

```
centralpy --help
```

or, by invoking the module with

```
python3 -m centralpy --help
```

FYI: this package's dependencies are
- [`requests`][requests] for communicating with ODK Central
- [`click`][click] >=8.0.0 for composing the command-line interface

[requests]: https://requests.readthedocs.io/en/master/
[click]: https://click.palletsprojects.com/en/master/

## Upgrade

Upgrade this package with

```
python3 -m pip install --upgrade centralpy
```

# Usage

The main command `centralpy` does not do anything by itself. It has its own options to configure the program and then delegate to its subcommands.

The options for the main command `centralpy` are

Option | Description 
--- | ---
  -u, --url TEXT              | The URL for the ODK Central server
  -e, --email TEXT            | An ODK Central user email
  -p, --password TEXT         | The password for the account
  -l, --log-file FILE         | Where to save logs.  (default: ./centralpy.log)
  -v, --verbose               | Display logging messages to console. This cannot be enabled from a config file.
  -c, --config-file FILENAME  | A configuration file with KEY=VALUE defined (one per line). Keys should be formatted as `CENTRALPY_***`.
  --help                  | Show this message and exit.

There are then six subcommands.

- [`pullcsv`](#subcommand-pullcsv)
- [`push`](#subcommand-push)
- [`check`](#subcommand-check)
- [`update-attachments`](#subcommand-update-attachments)
- [`config`](#subcommand-config)
- [`version`](#subcommand-version)

## Subcommand: pullcsv

This subcommand downloads the CSV zip file and extracts data CSVs. The zip file is saved with a timestamp in the filename in order to assist in deleting old zip files (see the `--keep` option).

An easy way to get the project ID (a number) and the XForm ID is to navigate to the form on ODK Central, and then examine the URL.

The options for `pullcsv` are

Option | Description 
--- | ---
  -p, --project INTEGER    | The numeric ID of the project. ODK Central assigns this ID when the project is created.  (required)
  -f, --form-id TEXT       | The form ID (a string), usually defined in the XLSForm settings. This is a unique identifier for an ODK form. (required)
  -c, --csv-dir DIRECTORY  | The directory to export CSV files to  (default: ./)
  -z, --zip-dir DIRECTORY  | The directory to save the downloaded zip to  (default: ./)
  -A, --no-attachments     | If this flag is supplied, then the CSV zip will be downloaded without attachments.
  -k, --keep INTEGER       | The number of zip files to keep in the zip directory, keeping the most recent. The number must be 1 or larger for anything to happen.
  --help               | Show this message and exit.

## Subcommand: push

This subcommand crawls through a local directory looking for XML files to upload. The form ID is autodetected from the XML.

*NOTE* Centralpy expects there to be no more than one XML file per subfolder, which is how instances are saved on the phone by ODK Collect.

The options for `push` are

Option | Description 
--- | ---
  -p, --project INTEGER      | The numeric ID of the project  (required)
  -l, --local-dir DIRECTORY  | The directory to push uploads from  (default: ./)
  --help                 | Show this message and exit.

## Subcommand: check

Check the connection, configuration, and parameters for centralpy.

These checks are performed in order, checking that centralpy can

1. Connect to the server
2. Verify the server is an ODK Central server
3. Authenticate the provided credentials
4. Check existence and access to the project, if provided
5. Check existence and access to the form ID within the project, if provided
6. Check existence of the instance ID within the form, if provided

If any of the checks fail, then the remaining checks are not performed.

*TIP:* If a project is not provided, but the credentials are valid, then centralpy will show which projects are accessible for the user. Likewise, if there are valid credentials and a valid project, then centralpy will show which form IDs are accessible for the user.

Option | Description 
--- | ---
  -p, --project INTEGER |  The numeric ID of the project. ODK Central assigns this ID when the project is created.
  -f, --form-id TEXT |     The form ID (a string), usually defined in the XLSForm settings. This is a unique identifier for an ODK form.
  -i, --instance-id TEXT  | An instance ID, found in the metadata for a submission. This is a unique identifier for an ODK submission to a form.
  --help |             Show this message and exit.


## Subcommand: update-attachments

  Update one or more attachments for the given submission.

  To pass multiple attachments, use -a multiple times.

Option | Description 
--- | ---
  -p, --project INTEGER | The numeric ID of the project. ODK Central assigns this ID when the project is created.
  -f, --form-id TEXT | The form ID (a string), usually defined in the XLSForm settings. This is a unique identifier for an ODK form.
  -i, --instance-id TEXT | An instance ID, found in the metadata for a submission. This is a unique identifier for an ODK submission to a form.
  -a, --attachment FILENAME | The attachment file to update for the instance ID.
  --help | Show this message and exit.


## Subcommand: config

This subcommand prints out the configuration that the main command, `centralpy` uses

## Subcommand: version

This subcommand prints out centralpy's version.

*NOTE:* The logs generated from `cli.py` also include the version number.

# Example usage

How to
- Pull CSV data
- Save CSV data and zip files to different directories
- Keep the most recent 7 zip files

```
# First on one line
centralpy --url "https://central.example.com" --email "manager@example.com" --password "password1234" --verbose pullcsv --project 1 --form-id MY_FORM_ID --csv-dir /path/to/csv/dir --zip-dir /path/to/zip/dir --keep 7
# Then the same command on multiple lines
centralpy \
--url "https://central.example.com" \
--email "manager@example.com" \
--password "password1234" \
--verbose \
pullcsv \
--project 1 \
--form-id MY_FORM_ID \
--csv-dir /path/to/csv/dir \
--zip-dir /path/to/zip/dir \
--keep 7
```

How to
- Do the same as the above using a log file

```
# First on one line
centralpy --config-file /path/to/config.txt --verbose pullcsv --project 1 --form-id MY_FORM_ID --csv-dir /path/to/csv/dir --zip-dir /path/to/zip/dir --keep 7
# Then the same command on multiple lines
centralpy \
--config-file /path/to/config.txt \
--verbose \
pullcsv \
--project 1 \
--form-id MY_FORM_ID \
--csv-dir /path/to/csv/dir \
--zip-dir /path/to/zip/dir \
--keep 7
```

How to
- Push XML files to ODK Central

```
# First on one line
centralpy --url "https://odkcentral.example.com" --email "manager@example.com" --password "password1234" push --project 1 --local-dir /path/to/dir
# Then the same command on multiple lines
centralpy \
--url "https://odkcentral.example.com" \
--email "manager@example.com" \
--password "password1234" \
push \
--project 1 \
--local-dir /path/to/dir
```

# An example config file

A config file can be specified for the main command, `centralpy`. The following demonstrates the contents of an example config file:

```
CENTRALPY_URL=https://odkcentral.example.com
CENTRALPY_EMAIL=manager@example.com
CENTRALPY_PASSWORD=password1234
CENTRALPY_LOG_FILE=centralpy.log
```

# Usage: check-audits

Find audit files with incorrect number of fields in a record.

ODK Central expects audit files to have the correct number of fields per record.
The correct length is established by the header row.
An record is usually a line. However, using quoting, a CSV field can span multiple lines.

Option | Description
--- | ---
  -r, --record TEXT |    Which records to look at. Give a range or a single number. Default is all records.
  -l, --log-file FILE |  Where to save logs.  (default: ./centralpy.log)
  -v, --verbose       | Display logging messages to console. This cannot be enabled from a config file.
  --help               | Show this message and exit.

The command `check-audits` (not prefixed by `centralpy`) or `python3 -m centralpy.check_audits` can be used to check local `audit.csv` files for correct record length. ODK Central tends to get into a bad state if these files are downloaded as attachments.

```
check-audits /path/to/storage
```

# Develop

- Create a virtual environment `python3 -m venv env/ --prompt centralpy`
- Activate it `source env/bin/activate`
- Install `pip-tools` with `python3 -m pip install pip-tools`
- Clone this repository
- Download all developer packages: `pip-sync requirements.txt requirements-dev.txt`

# Bugs

Submit bug reports on the Github repository's issue tracker at [https://github.com/pmaengineering/centralpy/issues][issues]. Or, email the maintainer at jpringleBEAR@jhu.edu (minus the BEAR).

[issues]: https://github.com/pmaengineering/centralpy/issues

---



# Un client Python pour ODK Central

ODK Central a une [API][api], et ce package Python interagit avec elle. Les cas d'utilisation de ce package ont été écrits pour prendre en charge les objectifs de gestion des données PMA, mais le package peut également être étendu à d'autres cas d'utilisation.

# Installation

Tout d'abord, assurez-vous que Python3 (au moins la version 3.6) est installé.

Utilisez `pip` pour installer ce package avec

```
python3 -m pip install centralpy
```

À partir de là, le programme s'exécute en utilisant soit le script installé, par exemple

```
centralpy --help
```

ou, en invoquant le module avec

```
python3 -m centralpy --help
```

Pour info: les dépendances de ce package sont
- [`requests`][requests] pour communiquer avec ODK Central
- [`click`][click] >=8.0.0 pour composer l'interface de ligne de commande

## Améliorer

Mettez à niveau ce package avec

```
python3 -m pip install --upgrade centralpy
```

# Usage

La commande principale `centralpy` ne fait rien par elle-même. Il a ses propres options pour configurer le programme et ensuite déléguer à ses sous-commandes.

Les options de la commande principale `centralpy` sont

Option | Description
--- | ---
  -u, --url TEXT | L'URL du serveur ODK Central
  -e, --email TEXT | Un e-mail d'utilisateur ODK Central
  -p, --password TEXT | Le mot de passe du compte
  -l, --log-file FILE | Où enregistrer les journaux. (par défaut: ./centralpy.log)
  -v, --verbose | Afficher les messages de journalisation sur la console. Cela ne peut pas être activé à partir d'un fichier de configuration.
  -c, --config-file FILENAME | Un fichier de configuration avec KEY = VALUE défini (un par ligne). Les clés doivent être au format `CENTRALPY_***`.
  --help | Affichez ce message et quittez.

Il y a alors six sous-commandes.

- [`pullcsv`](#sous-commande-pullcsv)
- [`push`](#sous-commande-push)
- [`check`](#sous-commande-check)
- [`update-attachments`](#sous-commande-update-attachments)
- [`config`](#sous-commande-config)
- [`version`](#sous-commande-version)

## Sous-commande: pullcsv

Cette sous-commande télécharge le fichier zip CSV et extrait les données CSV. Le fichier zip est enregistré avec un horodatage dans le nom du fichier afin d'aider à supprimer les anciens fichiers zip (voir l'option `--keep`).

Un moyen simple d'obtenir l'ID de projet (un nombre) et l'ID XForm consiste à accéder au formulaire sur ODK Central, puis à examiner l'URL.

Les options pour `pullcsv` sont

Option | Description
--- | ---
  -p, --project INTEGER | L'ID numérique du projet. ODK Central attribue cet ID lors de la création du projet. (obligatoire)
  -f, --form-id TEXT | L'ID du formulaire (une chaîne), généralement défini dans les paramètres XLSForm. Il s'agit d'un identifiant unique pour un formulaire ODK. (obligatoire)
  -c, --csv-dir DIRECTORY | Le répertoire vers lequel exporter les fichiers CSV (par défaut: ./)
  -z, --zip-dir DIRECTORY | Le répertoire dans lequel enregistrer le zip téléchargé (par défaut: ./)
  -A, --no-attachments | Si cet indicateur est fourni, le zip CSV sera téléchargé sans pièces jointes.
  -k, --keep INTEGER | Le nombre de fichiers zip à conserver dans le répertoire zip, en conservant les plus récents. Le nombre doit être 1 ou plus pour que quoi que ce soit se passe.
  --help | Affichez ce message et quittez.

## Sous-commande: push

Cette sous-commande parcourt un répertoire local à la recherche de fichiers XML à télécharger. L'ID de formulaire est détecté automatiquement à partir du XML.

*REMARQUE* Centralpy s'attend à ce qu'il n'y ait pas plus d'un fichier XML par sous-dossier, c'est ainsi que les instances sont enregistrées sur le téléphone par ODK Collect. 

Les options pour `push` sont

Option | Description
--- | ---
  -p, --project INTEGER | L'ID numérique du projet (obligatoire)
  -l, --local-dir DIRECTORY | Le répertoire à partir duquel envoyer les téléchargements (par défaut: ./)
  --help | Affichez ce message et quittez.

## Sous-commande: check

Vérifiez la connexion, la configuration et les paramètres de centralpy.

Ces contrôles sont effectués dans l'ordre, en vérifiant que centralpy peut

1. Connectez-vous au serveur
2. Vérifiez que le serveur est un serveur ODK Central
3. Authentifiez les informations d'identification fournies
4. Vérifier l'existence et l'accès au projet, le cas échéant
5. Vérifier l'existence et l'accès à l'ID de formulaire dans le projet, s'il est fourni

Si l'une des vérifications échoue, les vérifications restantes ne sont pas effectuées.

*CONSEIL:* Si un projet n'est pas fourni, mais que les informations d'identification sont valides, alors centralpy montrera quels projets sont accessibles à l'utilisateur. De même, s'il existe des informations d'identification valides et un projet valide, alors centralpy affiche les ID de formulaire accessibles à l'utilisateur.


Option | Description
--- | ---
  -p, --project INTEGER | L'ID numérique du projet. ODK Central attribue cet ID lors de la création du projet.
  -f, --form-id TEXT |    L'ID du formulaire (une chaîne), généralement défini dans les paramètres XLSForm. Il s'agit d'un identifiant unique pour un formulaire ODK.
  -i, --instance-id TEXTE | Un identifiant d'instance, trouvé dans les métadonnées d'un soumission. Il s'agit d'un identifiant unique pour un ODK soumission à un formulaire.
  --help |            Affichez ce message et quittez.


## Sous-commande: update-attachments

Mettez à jour une ou plusieurs pièces jointes pour la soumission donnée.

   Pour transmettre plusieurs pièces jointes, utilisez -a plusieurs fois.

Options | Description
--- | ---
   -p, --project INTEGER | L'ID numérique du projet. ODK Central attribue cet ID lors de la création du projet.
   -f, --form-id TEXT | L'ID du formulaire (une chaîne), généralement défini dans le Paramètres XLSForm. Il s'agit d'un identifiant unique pour un formulaire ODK.
   -i, --instance-id TEXTE | Un identifiant d'instance, trouvé dans les métadonnées d'un soumission. Il s'agit d'un identifiant unique pour un Soumission ODK à un formulaire.
   -a, --attachment FILENAME | Le fichier de pièce jointe à mettre à jour pour l'instance IDENTIFIANT.
   --help | Affiche ce message et quitte.


## Sous-commande: config

Cette sous-commande imprime la configuration utilisée par la commande principale, `centralpy`

## Sous-commande: version

Cette sous-commande imprime la version de centralpy.

*REMARQUE:* Les journaux générés à partir de `cli.py` incluent également le numéro de version.

# Exemple d'utilisation

Comment
- Extraire les données CSV
- Enregistrer les données CSV et les fichiers zip dans différents répertoires
- Conservez les 7 fichiers zip les plus récents

```
# Premier sur une ligne
centralpy --url "https://central.example.com" --email "manager@example.com" --password "password1234" --verbose pullcsv --project 1 --form-id MY_FORM_ID --csv-dir /path/to/csv/dir --zip-dir /path/to/zip/dir --keep 7
# Puis la même commande sur plusieurs lignes
centralpy \
--url "https://central.example.com" \
--email "manager@example.com" \
--password "password1234" \
--verbose \
pullcsv \
--project 1 \
--form-id MY_FORM_ID \
--csv-dir /path/to/csv/dir \
--zip-dir /path/to/zip/dir \
--keep 7
```

Comment
- Faites la même chose que ci-dessus en utilisant un fichier journal

```
# Premier sur une ligne
centralpy --config-file /path/to/config.txt --verbose pullcsv --project 1 --form-id MY_FORM_ID --csv-dir /path/to/csv/dir --zip-dir /path/to/zip/dir --keep 7
# Puis la même commande sur plusieurs lignes
centralpy \
--config-file /path/to/config.txt \
--verbose \
pullcsv \
--project 1 \
--form-id MY_FORM_ID \
--csv-dir /path/to/csv/dir \
--zip-dir /path/to/zip/dir \
--keep 7
```

Comment
- Poussez les fichiers XML vers ODK Central

```
# Premier sur une ligne
centralpy --url "https://odkcentral.example.com" --email "manager@example.com" --password "password1234" push --project 1 --local-dir /path/to/dir
# Puis la même commande sur plusieurs lignes
centralpy \
--url "https://odkcentral.example.com" \
--email "manager@example.com" \
--password "password1234" \
push \
--project 1 \
--local-dir /path/to/dir
```

# Un exemple de fichier de configuration

Un fichier de configuration peut être spécifié pour la commande principale, `centralpy`. Ce qui suit montre le contenu d'un exemple de fichier de configuration:

```
CENTRALPY_URL=https://odkcentral.example.com
CENTRALPY_EMAIL=manager@example.com
CENTRALPY_PASSWORD=password1234
CENTRALPY_LOG_FILE=centralpy.log
```

# Utilisation : check-audits

Trouver des fichiers d'audit avec un nombre incorrect de champs dans un enregistrement.

ODK Central s'attend à ce que les fichiers d'audit aient le nombre correct de champs par enregistrement.
La longueur correcte est établie par la ligne d'en-tête.
Un enregistrement est généralement une ligne. Cependant, en utilisant les guillemets, un champ CSV peut s'étendre sur plusieurs lignes.

Option | Description
--- | ---
   -r, --record TEXTE | Quels enregistrements consulter. Donnez une plage ou un nombre unique. La valeur par défaut est tous les enregistrements.
   -l, --log-file FICHIER | Où enregistrer les journaux. (par défaut : ./centralpy.log)
   -v, --verbose | Afficher les messages de journalisation sur la console. Cela ne peut pas être activé à partir d'un fichier de configuration.
   --help | Affichez ce message et quittez.

La commande `check-audits` (non préfixée par `centralpy`) ou `python3 -m centralpy.check_audits` peut être utilisée pour vérifier la longueur d'enregistrement correcte des fichiers `audit.csv` locaux. ODK Central a tendance à se détériorer si ces fichiers sont téléchargés en tant que pièces jointes.

```
check-audits /chemin/vers/stockage
```

# Développer

- Créer un environnement virtuel `python3 -m venv env/ --prompt centralpy`
- Activez-le `source env/bin/activate`
- Installez `pip-tools` avec` python3 -m pip install pip-tools`
- Cloner ce référentiel
- Téléchargez tous les packages de développement: `pip-sync requirements.txt requirements-dev.txt`

# Insectes

Soumettez des rapports de bogue sur le suivi des problèmes du référentiel Github à l'adresse [https://github.com/pmaengineering/centralpy/issues][issues]. Ou, envoyez un e-mail au responsable à jpringleOURS@jhu.edu (moins l'OURS).

*Dernière mise à jour de la traduction française 09/28/2021*
