from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import src.config as cfg


def get_session() -> Session:
    if cfg.config is None:
        raise ValueError(
            "Config is not set. Please initialize the config before getting a session."
        )
    engine = create_engine(cfg.config.database_url)
    Session = sessionmaker(bind=engine)
    return Session()
