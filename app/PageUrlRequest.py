from pydantic import BaseModel

# Pydantic model for the POST request body
class PageUrlRequest(BaseModel):
    page_url: str