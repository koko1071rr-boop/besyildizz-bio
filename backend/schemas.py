from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class LinkItem(BaseModel):
    label: str
    url: str
    icon: str = "link"


class BioPageBase(BaseModel):
    business_name: str
    tagline: str = ""
    logo_url: str = ""
    theme_color: str = "#22c55e"
    links: List[LinkItem] = []


class BioPageCreate(BioPageBase):
    slug: str


class BioPageUpdate(BioPageBase):
    pass


class BioPageOut(BioPageBase):
    slug: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
