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

        self.proxies = None


    def scrape_page(self, facebook_page_url):
        response = requests.get(facebook_page_url, headers=self.headers)
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

        return gold_data
