from alembic.config import Config
from alembic import command
import os

def test_mig():
    cfg = Config('alembic.ini')
    cfg.set_main_option('sqlalchemy.url', 'sqlite:///temp.db')
    command.upgrade(cfg, '5a950640275c')

test_mig()
