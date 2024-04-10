# Use Notion API to create object in database.
import requests
import json
import os

# DATABASE_ID = "068ea96919534bcf9adba807c9f75833"    # 書籍一覧
DATABASE_ID = "3dacfb355eb34f0b9d127a988539809a"    # books in lab

def get_api_key(name: str) -> str:
    """
    Function to get API key from environment variable.
    If key was not bounded, this function asks the user to input it.

    Parameters
    ----------
    name: str
        Name of environment variable.

    Return
    ------
    api_key: str
    """
    api_key = os.environ.get(name)
    if api_key:
        return api_key
    else:
        api_key = input("Enter Notion API key: ")
        os.environ[name] = api_key
        return api_key

def get_page_ids(database_id):
    """Function to get information of current pages in database"""
    NOTION_API_KEY = get_api_key("NOTION_API_KEY")

    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers =  {
        "Notion-Version": "2022-06-28",
        "Authorization": "Bearer " + NOTION_API_KEY,
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers)
    data = response.json()
    with open("barcode/current_books.json", "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_book_info(
        isbn: int,
        title: str,
        authors: list[str] | None,
        published_date: str | None,
        description: str | None,
        thumbnail_link: str | None
        ):
    """
    Function to add book information to given database.
    `isbn` and `title` should not be `None`.
    """
    NOTION_API_KEY = get_api_key("NOTION_API_KEY")
    url = "https://api.notion.com/v1/pages"

    headers =  {
        "Notion-Version": "2022-06-28",
        "Authorization": "Bearer " + NOTION_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "ISBN-13": {
                "number": isbn
            },
            "名前": {
                "title": [
                    {"text": {"content": title}}
                ]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{ "type": "text", "text": { "content": "概要" } }]
                }
            },
        ]
    }

    # authors
    if authors:
        payload["properties"]["著者"] = {
                "multi_select": [
                    {"name": n} for n in authors
                ]
            }
    
    # published date
    if published_date:
        payload["properties"]["出版年"] = {
                "date": {
                    "start": published_date
                }
            }

    # description
    if description:
        payload["children"].append(
            {
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": description
                            }
                        }
                    ]
                }
            }
        )

    # thumbnail
    if thumbnail_link:
        payload["cover"] = {
            "type": "external",
            "external": {"url": thumbnail_link}
        }

    response = requests.post(url, headers=headers, json=payload)
    print(response)

if __name__ == "__main__":
    
    add_book_info(
        isbn=978_0000_0000_00,
        title="卒業論文", 
        published_date="2024-01-31",
        authors=["Naoki Shimoda", "Akihiro Yamamoto"],
        description='本研究では、説明可能な過程で多肢選択問題に対して解答する手法の開発を行う。',
        thumbnail_link="https://thumb.ac-illust.com/7a/7aa8e40fe838b70253a97eacbcb32764_t.jpeg"
    )

    # get_page_ids(DATABASE_ID)