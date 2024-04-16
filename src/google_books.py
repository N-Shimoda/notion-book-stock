import requests

def copy_entry(
        src_dict: dict, src_key: str,
        dst_dict: dict, dst_key: str
    ):
    try:
        dst_dict[dst_key] = src_dict[src_key]
    except:
        dst_dict[dst_key] = None
        print("There is no key named '{}'".format(src_key))

def search_isbn(isbn: int, verbose=False) -> dict | None:
    """
    Function to search ISBN value in Google Books.

    Parameters
    ----------
    isbn: int
    verbose: bool

    Returns
    -------
    bookdata: dict | None
        Information about the book.
    """
    url = "https://www.googleapis.com/books/v1/volumes?q=isbn:{}".format(isbn)

    response = requests.get(url)
    data = response.json()

    if data["totalItems"] > 0:
        volume_info = data["items"][0]["volumeInfo"]
        bookdata = dict(
            isbn            = int(isbn),
            title           = volume_info["title"],
        )
        copy_entry(volume_info, "authors",       bookdata, "authors")
        copy_entry(volume_info, "publishedDate", bookdata, "published_date")
        copy_entry(volume_info, "description",   bookdata, "description")
        try:
            copy_entry(volume_info["imageLinks"], "thumbnail", bookdata, "thumbnail_link")
        except:
            bookdata["thumbnail_link"] = None

        if verbose:
            print(bookdata)

    else:
        bookdata = None
        if verbose:
            print("No book was found for ISBN '{}'".format(isbn))
    
    return bookdata


if __name__ == "__main__":
    
    # add a book into Notion database
    isbn = 9784537214192    # "The Wine"
    print(search_isbn(isbn))