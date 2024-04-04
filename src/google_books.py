import requests

def search_isbn(isbn: int, verbose=False)->dict:
    """
    Function to search ISBN value in Google Books.

    Parameters
    ----------
    isbn: int
    verbose: bool

    Returns
    -------
    title, authors, published_date, thumbnail_link
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
            authors         = volume_info["authors"],
            published_date  = volume_info["publishedDate"],
        )
        try:
            bookdata["description"] = volume_info["description"]
        except:
            print("No description found")
            bookdata["description"] = None

        try:
            bookdata["thumbnail_link"] = volume_info["imageLinks"]["thumbnail"]
        except:
            print("No thumbnail found.")
            bookdata["thumbnail_link"] = None

        if verbose:
            print(bookdata)

    else:
        bookdata = None
        if verbose:
            raise ValueError("No book was found for ISBN '{}'".format(isbn))
    
    return bookdata


if __name__ == "__main__":
    
    # add a book into Notion database
    isbn = 9784537214192    # "The Wine"
    print(search_isbn(isbn))