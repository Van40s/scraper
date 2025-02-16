from fastapi import FastAPI, HTTPException
from typing import Dict, List
import uvicorn
import requests

from ScraperConfig import ScraperConfig
from PageUrlRequest import PageUrlRequest

app = FastAPI(
    title="Scrape API",
    description="An API to scrape user data based on the provided username.",
    version="1.0.0",
)

scraper: ScraperConfig = ScraperConfig()


@app.post("/check_heatlh")
async def check_health():
    response = requests.get("https://ifconfig.me/")

    return {"outbound_ip": response.text, "proxy_health": scraper.check_proxy_health()}


@app.post(
    "/scrape/",
    summary="Scrape Facebook page data",
    description="This endpoint scrapes data from a Facebook page URL. If the URL does not end with `/about`, it will be appended automatically.",
    response_description="The scraped and processed data from the Facebook page.",
)
async def scrape_page(request: PageUrlRequest):
    try:
        scraper_result: List[dict] = scraper.scrape_page(request.page_url)

        if isinstance(scraper_result, dict) and "error" in scraper_result:
            return {"error": scraper_result["error"]}

        if not scraper_result:
            raise HTTPException(status_code=404, detail="No data found for the given page URL.")

        return scraper_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
