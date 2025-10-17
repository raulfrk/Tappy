from sqlalchemy.orm import Session


class TapService:

    def __init__(self, session: Session):
        self._db = session
