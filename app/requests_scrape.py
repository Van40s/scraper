from fastapi import FastAPI, HTTPException
from typing import Dict, List
import uvicorn
from ScraperConfig import ScraperConfig
from PageUrlRequest import PageUrlRequest

app = FastAPI(
    title="Scrape API",
    description="An API to scrape user data based on the provided username.",
    version="1.0.0",
)

scraper: ScraperConfig = ScraperConfig()

def process_scrape(scrape_list_result: List[dict]) -> Dict[str, any]:
    final_dict = {}
    for data in scrape_list_result:
        profile_fields = data.get("profile_fields", {}).get("nodes", [])
        for node in profile_fields:
            field_type = node.get("field_type", "")
            if field_type:
                if field_type == "screenname":
                    field_type = node.get("list_item_groups", [])[0]\
                    .get("list_items", [])[0].get("text", {})\
                    .get("text")

                if field_type == "website":
                    if not final_dict.get("website", []):
                        final_dict["website"] = []

                value = node.get("title", {}).get("text", "")

                if value:
                    if field_type == "website":
                        final_dict["website"].append(value)
                        continue
                    final_dict[field_type] = value

    return final_dict


def ensure_about_url(url: str) -> str:
    url_suffix = url.split("facebook.com")[1]

    url_suffix_split = url_suffix.split("/")
    if len(url_suffix_split) == 3 and url_suffix_split[2] == "":
        url += "about"
    elif len(url_suffix_split) == 2:
        url += "about"

    return url


@app.post(
    "/scrape/",
    summary="Scrape Facebook page data",
    description="This endpoint scrapes data from a Facebook page URL. If the URL does not end with `/about`, it will be appended automatically.",
    response_description="The scraped and processed data from the Facebook page.",
)
async def scrape_page(request: PageUrlRequest):
    try:
        page_url = ensure_about_url(request.page_url)
        raw_data: List[dict] = scraper.scrape_page(page_url)
        processed_data: dict = process_scrape(raw_data)

        if not processed_data:
            raise HTTPException(status_code=404, detail="No data found for the given page URL.")

        return processed_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
