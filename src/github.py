import requests

def get_latest_tag(repo_owner: str, repo_name: str) -> str | None:
    """
    Function to get the latest tag name of the specified GitHub repository.

    Parameters
    ----------
    repo_owner: str
        Account name of repository owner.
    repo_name: str
        Name of repository.

    Return
    ------
    latest_tag_name: str | None
        Name of latest tag. Returns `None` if no tags published.
    """
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        latest_tag_name = data["tag_name"]
        release_date = str(data["published_at"]).split("T")[0]
        return latest_tag_name, release_date
    else:
        print(f"Failed to fetch latest release info. Status code: {response.status_code}")
        return None, None

if __name__ == "__main__":
    
    repo_owner = "N-Shimoda"
    repo_name = "notion-book-stock"
    VERSION = "v1.1"

    latest_tag, release_date = get_latest_tag(repo_owner, repo_name)
    if latest_tag:
        print("Latest tag: '{}' (released on {})".format(latest_tag, release_date))
        print(latest_tag==VERSION)