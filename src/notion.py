# Use Notion API to create object in database.
import json
import os
import time
from getpass import getpass
from datetime import datetime

import requests


class NotionObject:
    def __init__(self) -> None:
        self.notion_api_key = self.set_api_key("NOTION_API_KEY")
        self.headers = {
            "Notion-Version": "2022-06-28",
            "Authorization": "Bearer " + self.notion_api_key,
            "Content-Type": "application/json",
        }

    def set_api_key(self, name: str) -> str:
        """
        Method to set API key from environment variable.
        If key was not bounded, this function asks the user to enter it.

        Parameters
        ----------
        name: str
            Name of environment variable.

        Return
        ------
        api_key: str
        """
        api_key = os.environ.get(name)
        if api_key is not None:
            return api_key
        else:
            api_key = getpass("Enter Notion API key: ")
            os.environ[name] = api_key
            return api_key


class NotionDB(NotionObject):
    """Class for handling Notion database."""

    def __init__(self, databse_id: str) -> None:
        super().__init__()
        self.database_id = databse_id

    def create_book_page(
        self,
        isbn: int,
        title: str,
        authors: list[str] | None,
        published_date: str | None,
        location: str,
        description: str | None,
        thumbnail_link: str | None,
    ) -> requests.Response:
        """
        Function to add book information to given database.
        `isbn` and `title` should not be `None`.
        """
        url = "https://api.notion.com/v1/pages"

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {"ISBN-13": {"number": isbn}, "名前": {"title": [{"text": {"content": title}}]}},
            "children": [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": "概要"}}]},
                },
            ],
        }

        # authors
        if authors:
            payload["properties"]["著者"] = {"multi_select": [{"name": n} for n in authors]}

        # published date
        if published_date:
            payload["properties"]["出版年"] = {"date": {"start": published_date}}

        # location
        if location:
            payload["properties"]["所蔵場所"] = {"select": {"name": location}}

        # description
        if description:
            if len(description) > 2000:
                print("len(description) was over 2000 ({})".format(len(description)))
            payload["children"].append(
                {
                    "object": "block",
                    "type": "quote",
                    "quote": {"rich_text": [{"type": "text", "text": {"content": description[:2000-4] + " ..."}}]},
                }
            )
        else:
            payload["children"].append(
                {
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "書籍情報はありません。"},
                                "annotations": {"color": "gray"},
                            }
                        ]
                    },
                }
            )

        # thumbnail
        if thumbnail_link:
            payload["cover"] = {"type": "external", "external": {"url": thumbnail_link}}
        else:
            payload["cover"] = {
                "type": "external",
                "external": {"url": "https://free-icons.net/wp-content/uploads/2020/08/life041.png"},
            }

        response = requests.post(url, headers=self.headers, json=payload)
        print(response)
        return response

    def get_isbn_list(self) -> list[int] | None:
        """
        Method to get the list of ISBN from a database.

        Return
        ------
        li_isbn: list[int]
            List of ISBN in a database.
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        payload = {"page_size": 100}
        has_more = True
        li_isbn = []
        try:
            while has_more:
                response = requests.post(url, headers=self.headers, data=json.dumps(payload))
                if response.status_code != 200:
                    time.sleep(0.5)
                    continue
                res_json = response.json()
                li_isbn += [
                    res_json["results"][i]["properties"]["ISBN-13"]["number"] for i in range(len(res_json["results"]))
                ]
                has_more = res_json["has_more"]
                next_cursor = res_json["next_cursor"]
                payload = {"page_size": 100, "start_cursor": next_cursor}
            return li_isbn
        except KeyError as e:
            print(f"Key {e} doesn't exists.")
            return None
        except BaseException as e:
            print(type(e))
            print(e)
            return None

    def get_location_tags(self) -> list[str]:
        """
        Method to get existing options for location select.

        Returns
        -------
        locations: list[str]
            Options for location select.
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}"

        response_data = requests.get(url, headers=self.headers).json()
        options_data = response_data["properties"]["所蔵場所"]["select"]["options"]

        locations = []
        for item in options_data:
            loc = item["name"]
            if not item in locations:
                locations.append(loc)

        return locations

    def get_existing_pageid(self, isbn: int) -> list[str]:
        """
        Method to get existing page ids for the book with given isbn.

        Parameters
        ----------
        isbn: int

        Returns
        -------
        ids: list[str]
            List of page ids for the given book.
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        filter = {
            "property": "ISBN-13",
            "number": {
                "equals": isbn
            } 
        }
        res = requests.post(url, headers=self.headers, json=dict(filter=filter))
        pages_data = res.json()["results"]
        ids = []
        if len(pages_data) > 0:
            for pg in pages_data:
                ids.append(pg["id"])
        
        return ids

    def save_bookdata(self, filename="bookdata.json"):
        """
        Method to save information about existing books into json.

        Parameters
        ----------
        filename: str
            Relative path of output file.

        Returns
        -------
        result: dict
            Data of current books in Notion database.
            `result` has folloting keys:
            - `databse_id`: str
            - `date`: str
            - `total_items`: int
            - `books`: dict
                + `isbn`: int
                + `title`: str
                + `location`: str
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        result = {
            "database_id": self.database_id, 
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_items": 0,
            "books": []
        }

        # query params
        has_more = True
        start_cursor = None
        i = 0

        while has_more:
            print("Fetching books {}-{}".format(100*i, 100*i+99))

            if start_cursor:
                res = requests.post(url, headers=self.headers, json=dict(start_cursor=start_cursor))
            else:
                res = requests.post(url, headers=self.headers)

            if res.status_code != 200:
                raise ValueError("Failed in API call.")

            has_more = res.json()["has_more"]
            start_cursor = res.json()["next_cursor"]

            for obj in res.json()["results"]:
                isbn = obj["properties"]["ISBN-13"]["number"]
                loc = obj["properties"]["所蔵場所"]["select"]["name"]
                title = obj["properties"]["名前"]["title"][0]["text"]["content"]
                result["books"].append(dict(isbn=isbn, title=title, location=loc))
            
            i += 1

        result["total_items"] = len(result["books"])

        with open(filename, "w") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        return result


class NotionPage(NotionObject):
    """Class for handling Notion Page object."""
    def __init__(self, page_id: str) -> None:
        super().__init__()
        self.page_id = page_id

    def get_location_tag(self) -> str:
        """Method to acquire location tag."""
        url = f"https://api.notion.com/v1/pages/{self.page_id}"
        res = requests.get(url, headers=self.headers)
        tag = res.json()["properties"]["所蔵場所"]["select"]["name"]
        return tag

    def update_location(self, loc: str):
        """
        Method to update location of the book.
        
        Parameters
        ----------
        loc: str
            Name of new location tag.
        """
        url = f"https://api.notion.com/v1/pages/{self.page_id}"
        properties = {
            "所蔵場所": {"select": {"name": loc}}
        }
        res = requests.patch(url, headers=self.headers, json=dict(properties=properties))
        if res.status_code != 200:
            raise ValueError("Failed in API call.")


if __name__ == "__main__":

    # pg = NotionPage(page_id="756baa14-53fa-441f-b35d-a088a67658df")
    # pg.update_location()

    db = NotionDB(databse_id="3dacfb355eb34f0b9d127a988539809a")  # books in lab
    ids = db.get_existing_pageid(9780262693073)
    print(ids)

    if len(ids) > 0: 
        pg = NotionPage(ids[0])
        tag = pg.get_location_tag()
        print(tag)
    # db.save_bookdata()

    # db.create_book_page(
    #     isbn=978_0000_0000_00,
    #     title="卒業論文",
    #     published_date="2024-01-31",
    #     authors=["Naoki Shimoda", "Akihiro Yamamoto"],
    #     location="N1",
    #     description="本研究では、説明可能な過程で多肢選択問題に対して解答する手法の開発を行う。",
    #     thumbnail_link="https://thumb.ac-illust.com/7a/7aa8e40fe838b70253a97eacbcb32764_t.jpeg",
    # )

    # locations = db.get_location_tags()
    # print(locations)
