from flask import request


def get_lang() -> str:
    selected = request.accept_languages.best_match(TRANS.keys())
    if selected:
        return selected
    return 'en'


def _(msg: str) -> str:
    return TRANS[get_lang()].get(msg, msg)


TRANS = {
    'en': {
        'already revealed': '<p>This secret has already been '
                            'revealed.</p><p>If you are the recipient '
                            'of this secret, but haven\'t revealed it, '
                            'you should inform the creator of the '
                            'secret about a potential security '
                            'breach.</p>',
        'autoreload': 'Auto reload every 5s',
        'clip': 'Copy to clipboard',
        'create link': 'Create link',
        'download?': 'Download this secret?',
        'download!': 'Download the secret',
        'download done': '&#x2705; File retrieved',
        'error': 'Error',
        'go to receive': 'Receive the secret',
        'new secret': 'Check and correct the key. '
                      'Alternatively you can create a new secret and send the new link to the other side.',
        'only once': 'You can only do this once.',
        'request': 'Request a secret',
        'request desc': 'Give the Request-Link (validity 7 days) below to someone you want '
                        'to retrieve a secret from. Afterwards push "Receive the secret" to wait for the secret.',
        'reveal!': 'Reveal the secret',
        'reveal?': 'Reveal this secret?',
        'rid missing or invalid': 'Request ID (rid) missing or invalid.',
        'rid secret stored': 'Secret stored',
        'rid secret stored desc': 'The requested secret can now be revealed on the other side.',
        'secret': 'Secret',
        'share new secret': 'Share a new secret',
        'share new file': 'Share a new file',
        'share this': 'Share this link',
        'share this desc': 'Send this link to someone else. <em>It will '
                           'be valid for 7 days.</em>',
        'title': 'Share a secret',
        'waiting for secret': 'Waiting for secret',
        'waiting for secret desc': 'The other side has not entered the secret yet.',
        'welcome desc': 'Enter your text into the box below. Once you '
                        'hit the button, you will get a link that you '
                        'can send to someone else. That link can only '
                        'be used once.',
        'welcome maybe file': 'Alternatively, you can '
                              '<a href="/file{rid}">upload a file</a>',
        'welcome maybe text': 'Alternatively, you can '
                              '<a href="/{rid}">use plain text</a>',
        'welcome maybe request': ' or <a href="/request">request a secret</a>',
        'welcome file': 'Select the file to upload below. Once you hit '
                        'the button, you will get a link that you can '
                        'send to someone else. That link can only be '
                        'used once.',
        'welcome file max': 'Maximum allowed size',
        'wrong key': 'Wrong key. Secret has been destroyed.',
        'your secret': 'Here’s your secret. It is no longer accessible '
                       'through the link, so copy it <em>now</em>.',
    },
    'de': {
        'already revealed': '<p>Die vertraulichen Daten wurden bereits '
                            'abgerufen.</p><p>Falls Sie Empfänger*in '
                            'der Daten sind, diese aber nicht selbst '
                            'abgerufen haben, sollten Sie die '
                            'Versender*in über die potentielle '
                            'Kompromittierung informieren.</p>',
        'autoreload': 'Automatisch alle 5s neu laden',
        'clip': 'In die Zwischenablage kopieren',
        'create link': 'Link erzeugen',
        'download?': 'Vertrauliche Daten herunterladen?',
        'download!': 'Vertrauliche Daten herunterladen',
        'download done': '&#x2705; Bereits heruntergeladen',
        'error': 'Fehler',
        'go to receive': 'Vertrauliche Daten erhalten',
        'new secret': 'Bitte prüfen Sie den Schlüssel. '
                      'Alternativ können Sie ein neues Geheimnis für vertrauliche Daten generieren '
                      'und den neuen Link an die andere Seite senden.',
        'only once': 'Sie können diesen Vorgang nur <em>einmalig</em> '
                     'durchführen.',
        'request': 'Vertrauliche Daten anfordern',
        'request desc': 'Geben Sie den untenstehenden Request-Link (7 Tage gültig) an die Person weiter, '
                        'von der sie vertrauliche Daten erhalten möchten. Drücken Sie danach auf "Vertrauliche Daten erhalten".',
        'reveal!': 'Vertrauliche Daten anzeigen',
        'reveal?': 'Vertrauliche Daten anzeigen?',
        'rid missing or invalid': 'Die Request ID (rid) fehlt oder ist ungültig.',
        'rid secret stored': 'Vertrauliche Daten gespeichert',
        'rid secret stored desc': 'Die vertraulichen Daten können nun auf der anderen Seite abgerufen werden.',
        'secret': 'Vertrauliche Daten',
        'share new secret': 'Neue vertrauliche Daten',
        'share new file': 'Neue vertrauliche Datei hochladen',
        'share this': 'Geben Sie diesen Link weiter',
        'share this desc': 'Geben Sie den folgenden Link weiter. <em>Er '
                           'ist nur für 7 Tage gültig.</em>',
        'title': 'Vertrauliche Daten weitergeben',
        'waiting for secret': 'Warte auf vertrauliche Informationen',
        'waiting for secret desc': 'Bisher wurden auf der anderen Seite noch keine vertraulichen Informationen eingegeben.',
        'welcome desc': 'Geben Sie Ihre vertraulichen Daten in die '
                        'Textbox unten ein. Sobald Sie den Knopf '
                        'betätigen, erhalten Sie einen Link, den Sie '
                        'weitergeben können. Dieser Link kann nur ein '
                        'einziges Mal abgerufen werden.',
        'welcome maybe file': 'Alternativ können Sie '
                              '<a href="/file{rid}">eine Datei hochladen</a>',
        'welcome maybe text': 'Alternativ können Sie '
                              '<a href="/{rid}">einfachen Text verwenden</a>',
        'welcome maybe request': ' oder <a href="/request">vertrauliche Daten anfordern</a>',
        'welcome file': 'Wählen Sie die hochzuladende Datei aus. Sobald '
                        'Sie den Knopf betätigen, erhalten Sie einen '
                        'Link, den Sie weitergeben können. Dieser Link '
                        'kann nur ein einziges Mal abgerufen werden.',
        'welcome file max': 'Maximal erlaubte Größe',
        'wrong key': 'Falscher Schlüssel. Daten wurden gelöscht.',
        'your secret': 'Untenstehend finden Sie die angefragten '
                       'vertraulichen Daten. Von nun an ist es nicht '
                       'mehr möglich, diesen Link zu verwenden. Sie '
                       'sollten die Daten also <em>jetzt</em> sichern.',
    },
}
