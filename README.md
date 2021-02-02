Ceci est un programme permettant de récupérer des données de fourmizzz et de générer un rapport hebdomadaire sur les floods et les convois effectués. De plus, il gère le décompte des convois automatiquement.
Je n'avais pas prévu de faire un programme de cette taille (bien qu'il ne sois pas très grand), ni de le partager. Alors, il est très mal optimisé et documenté. Je le laisse à disposition de mon alliance, la 10k. Je suis désolé mais le gros est en anglais, certaines parties sont en français pour des raisons obscures.


Téléchargez les fichiers et suivez les instructions.

Pour l'utiliser, vous aurez besoin d'installer Python 3. Google est votre ami.

Une fois Python installé, vous aurez également besoin d'une série de packages à ajouter à Python. Pour cela, ouvrez le terminal (sur Windows, touche Windows + R et tapez 'cmd') et faites les commandes suivantes :
- pip install pandas
- pip install requests
- pip install bs4
- pip install selenium
- pip install matplotlib
- pip install weasyprint
- pip install Pillow
- pip install numpy
- pip install engineering_notation

Dans le fichier files/identifiants_fmz.txt, écrivez votre pseudo, votre mot de passe et le token de cookie d'auto-connection sur trois lignes consécutives. Pour trouver ce token, utiliser cette extension. Le token doit ressembler à une série de chiffres et de lettres associées à un mot clé "PHPSESSID".
https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm?hl=fr

Enfin, lancez le programme, toujours via le terminal. Voyagez jusqu'au fichier "main.py" à l'aide de la commande cd et puis entrez la commande suivante:
- python main.py

Si ça ne fonctionne pas, replacez python par py ou python3. Sinon, python est mal installé ou vous n'êtes pas dans le bon dossier. Vérifiez également que Google Chrome est installé et à jour. Il est également possible que chromedriver ne soit pas à jour. Pour cela, télécharger la nouvelle version et placer le ficher "chromedriver.exe" dans le même dossier que émain.py".
https://chromedriver.chromium.org/downloads

De mon coté, le programme ne plante quasiment jamais. Si il plante, cela peut arriver pour deux raisons.
- La connection au webdriver a échoué. Ça arrive rarement mais ça arrive. il suffit de relancer le programme ou d'utiliser l'option "repair".
- Google Chrome s'est mis à jour alors la versio ne correspond plus à celle de chromedriver. Suivez le lien ci-dessus pour le mettre à jour.

En utilisant le programme, faites le code "45" + Enter pour afficher les logs de ce qui est fait et quand. Je l'utilisee très souvent.

Si vous avez le moindre problème, contactez moi de préférence sur discord: Zarki#5363

</br>

<b>Rapport hebdomadaire automatique</b>
<img src="https://zupimages.net/up/20/36/rnpu.png" width="80%">

<b>Comptage automatique des convois</b>
<img src="https://i.gyazo.com/7fe27fb604586e33c0153c61fdbfd3fa.png" width="80%">
