from sqlalchemy.orm import Session
from app.models.team import Team

def get_all_teams(db: Session):
    """
    Restituisce la lista di tutte le squadre ordinate per id.
    """
    return db.query(Team).order_by(Team.id).all()

def get_team_by_name(db: Session, name: str):
    """
    Recupera una squadra dal database tramite il nome (case insensitive).
    """
    return db.query(Team).filter(Team.name.ilike(name)).first()

def update_teams_list(db: Session, new_teams: list):
    """
    Aggiorna la lista delle squadre top10.
    Cancella le vecchie squadre e inserisce le nuove.

    Args:
        db: sessione DB
        new_teams: lista di dict, esempio:
            [
                {"name": "Napoli", "logo_url": "https://..."},
                ...
            ]
    """
    # Elimina tutte le squadre esistenti
    db.query(Team).delete()
    db.commit()

    # Inserisce le nuove squadre
    for team_data in new_teams:
        team = Team(name=team_data['name'], logo_url=team_data['logo_url'])
        db.add(team)
    db.commit()

def team_exists(db: Session, name: str) -> bool:
    """
    Verifica se una squadra esiste già nel DB.
    """
    return db.query(Team).filter(Team.name.ilike(name)).count() > 0
