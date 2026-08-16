import pytest

from hospital_ai.main import create_app
from tests.cdi_v2.acceptance.harness import CDIv2Harness


@pytest.fixture
def cdi_v2_harness(session_and_settings):
    session, settings = session_and_settings
    app = create_app(settings)
    return CDIv2Harness(app=app, session=session, settings=settings)
