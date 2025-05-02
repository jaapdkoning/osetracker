# OSE Tracker

Een webgebaseerde toolkit voor het Old School Essentials (OSE) tabletop RPG-systeem.

## Kenmerken

- Characters aanmaken en beheren met volledige OSE-statistieken en uitrusting
- NPC's genereren (handmatig of met AI-ondersteuning)
- Encounters genereren voor combat, social en puzzle situaties
- Sessie-logging met relaties naar karakters en NPC's
- Resource tracking (voorraad, rations, fakkels, enz.)
- Ondersteuning voor meerdere campagnes
- Speler- en DM-authenticatie met verschillende gebruikersrollen
- OpenAI integratie voor NPC- en encounter-generatie

## Installatie

### Vereisten

- Python 3.8+
- MySQL (voor productie) of SQLite (voor ontwikkeling)
- Docker en Docker Compose (optioneel, voor containerisatie)

### Lokale installatie

1. Clone de repository:
```
git clone https://github.com/yourusername/osetracker.git
cd osetracker
```

2. Maak een virtuele omgeving aan:
```
python -m venv venv
source venv/bin/activate  # Op Windows: venv\Scripts\activate
```

3. Installeer de afhankelijkheden:
```
pip install -r requirements.txt
```

4. Maak een `.env` bestand aan op basis van het voorbeeld:
```
cp .env.example .env
```

5. Bewerk het `.env` bestand en configureer de instellingen naar wens.

6. Initialiseer de database:
```
flask init-db
flask create-roles
```

7. Maak een admin-gebruiker aan:
```
flask create-admin
```

8. Start de applicatie:
```
flask run
```

### Docker installatie

1. Clone de repository:
```
git clone https://github.com/yourusername/osetracker.git
cd osetracker
```

2. Maak een `.env` bestand aan en configureer de instellingen.

3. Start de containers met Docker Compose:
```
docker-compose up -d
```

4. Initialiseer de database en maak een admin-gebruiker aan:
```
docker-compose exec web flask create-roles
docker-compose exec web flask create-admin
```

5. De applicatie is nu beschikbaar op http://localhost:5000

## Gebruik

Na het inloggen worden spelers doorgestuurd naar hun dashboard waar ze:

1. Hun characters kunnen beheren
2. Campaigns kunnen bekijken waar ze aan deelnemen
3. Hun sessies kunnen bekijken

Dungeon Masters (DMs) hebben extra functionaliteiten:

1. Campaigns aanmaken en beheren
2. NPC's maken en genereren met AI
3. Encounters maken en genereren met AI
4. Sessies plannen en logging bijhouden

## AI-integratie

Voor het gebruik van de AI-generatiefunctionaliteiten is een OpenAI API-sleutel vereist. Deze kan worden geconfigureerd in het `.env` bestand:

```
OPENAI_API_KEY=uw-api-sleutel
```

De applicatie ondersteunt optioneel een creditsysteem om het gebruik van de AI-functionaliteit te beperken:

```
OPENAI_CREDITS_ENABLED=True
DEFAULT_AI_CREDITS=10
```

## Ontwikkeling

### Database migraties

Als je wijzigingen aanbrengt in de databasemodellen, gebruik Flask-Migrate om migraties aan te maken en uit te voeren:

```
flask db migrate -m "Beschrijving van de wijzigingen"
flask db upgrade
```

### Testen

Voer de tests uit met pytest:

```
pytest
```

## Bijdragen

Bijdragen zijn welkom! Open een pull request of een issue om bugs te rapporteren of nieuwe functionaliteiten voor te stellen.
