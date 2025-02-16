import os
from typing import List, Dict
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import json


class ScraperConfig:
    def __init__(self):
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.8",
            "cache-control": "max-age=0",
            "cookie": "ps_l=1; ps_n=1; sb=8HLlZrjirapqxtugJpFHaP1Q; oo=v1; datr=Y-8nZ3rICFiuIoPVwnEv8TGU; datr=__GMZCgwVF5BbyvAtfJojQwg; fr=1pFhbp4gdOGWxhOga.AWXy7CVF9e_5YtYhP1c36_52p5g.BnHp0K..AAA.0.0.BnNQfz.AWUu6xhfxag; wd=1005x966",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="130", "Brave";v="130", "Not?A_Brand";v="99"',
            "sec-ch-ua-full-version-list": '"Chromium";v="130.0.0.0", "Brave";v="130.0.0.0", "Not?A_Brand";v="99.0.0.0"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": '""',
            "sec-ch-ua-platform": '"Linux"',
            "sec-ch-ua-platform-version": '"6.8.0"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "sec-gpc": "1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        }

        username = os.getenv("PROXY_USERNAME", None)
        password = os.getenv("PROXY_PASSWORD", None)
        if username and password:
            self.proxy = f"http://{username}:{password}@dc.smartproxy.com:10000"
        else:
            self.proxy = None


    def check_proxy_health(self):
        result = None
        i = 0
        while i < 3:
            try:
                url = 'https://ip.smartproxy.com/json'

                result = requests.get(url, proxies={
                    'http': self.proxy,
                    'https': self.proxy
                })
                break
            except Exception as e:
                i += 1
                pass

        if result is None:
            return {
                "error": "proxy error"
            }

        return result.json()


    @staticmethod
    def extract_facebook_id(url):
        # Parse the URL
        parsed_url = urlparse(url)

        # Extract query parameters
        query_params = parse_qs(parsed_url.query)

        # Get the 'id' value
        fb_id = query_params.get("id", [None])[0]

        return fb_id


    @staticmethod
    def check_and_parse_url(url: str) -> str:
        url_suffix = url.split("facebook.com/")[1]

        url_suffix_split = url_suffix.split("/")

        new_url_built_basic = "https://www.facebook.com"
        path = ""
        if "/videos/" in url or "/photos/" in url:
            new_url_built_basic += f"/{url_suffix_split[0]}/about"
            return new_url_built_basic

        if "profile.php?id=" in url:
            facebook_id = ScraperConfig.extract_facebook_id(url)
            return f"{new_url_built_basic}/{facebook_id}/about"

        for split in reversed(url_suffix_split):
            if split in ["p", "people", "about", ""] or "?sk=about" in split or "?locale=" in split:
                continue

            path += f"/{split}"
            if split.isdigit():
                break

        path += "/about"
        new_url_built_basic += path
        return new_url_built_basic

    @staticmethod
    def process_scrape(scrape_list_result: List[dict]) -> Dict[str, any]:
        final_dict = {}
        for data in scrape_list_result:
            profile_fields = data.get("profile_fields", {}).get("nodes", [])
            for node in profile_fields:
                field_type = node.get("field_type", "")
                if field_type:
                    if field_type == "screenname":
                        field_type = node.get("list_item_groups", [])[0] \
                            .get("list_items", [])[0].get("text", {}) \
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


    def scrape_page(self, facebook_page_url):
        facebook_page_url = self.check_and_parse_url(facebook_page_url)

        response = None
        i = 0
        while i < 3:
            try:
                response = requests.get(facebook_page_url, proxies={
                    'http': self.proxy,
                    'https': self.proxy
                }, headers=self.headers)
                break
            except Exception as e:
                i += 1
                pass

        if response is None:
            return {
                "error": "Can't be scraped"
            }

        soup = BeautifulSoup(response.text, 'html.parser')
        gold_data = None
        for script_tag in soup.find_all('script', type='application/json'):
            try:
                json_data = script_tag.string
                parsed_data = json.loads(json_data)

                try:
                    first_part_list = parsed_data['require'][0][3][0].get("__bbox", {}).get("require", [])

                    continuation = None
                    for element in first_part_list:
                        if "profile_field_sections" in str(element):
                            continuation = element
                            break

                    if continuation is None:
                        continue

                    gold_data = continuation[3][1] \
                        .get("__bbox", {}).get("result", {}).get("data", {}).get("user").get("about_app_sections",
                                                                                             {}) \
                        .get("nodes", [])[0].get("activeCollections", {}).get("nodes", [])[0] \
                        .get("style_renderer", {}).get("profile_field_sections", [])
                except Exception as e:
                    continue
            except Exception as e:
                print(f"Error decoding JSON from a script tag. {e}")
                return {}

        processed = self.process_scrape(gold_data)

        return processed
