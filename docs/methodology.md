# Methodology

This recommendation service is intended to return a suggested search result—and additional metadata for it—for an incomplete search string. Following: a walkthrough of the methodology using the search term "the mar", an in-process search where the user is looking for information about the film [The Martian](http://www.imdb.com/title/tt3659388/).

First, we want to determine the user's intended search from the in-process search string. We do that by passing the query to a search suggestion engine. That engine might respond with the following suggestions:

```json
[
  "the martian",
  "the martian trailer",
  "the martian movie",
  "the martian book",
  "the marion star",
  "the mary sue"
]
```

We'll take top of those, `the martian`, and perform a search on that using a full search engine API:

```json
{
  "abstract": "Directed by Ridley Scott. With Matt Damon, Jessica Chastain, Kristen Wiig, Kate Mara. During a manned mission to Mars, Astronaut Mark Watney is presumed dead after a ...",
  "clickurl": "http://www.imdb.com/title/tt3659388/",
  "date": "",
  "dispurl": "www.imdb.com/title/tt3659388",
  "title": "<b>The Martian</b> (2015) - IMDb",
  "url": "http://www.imdb.com/title/tt3659388/"
}
```

Using the data from that search result, we then run it through a series of classifiers. Each of these attempt to match and enhance results with data from additional sources.

An IMDb enhancer might recognize that the above result is a movie from IMDb and add the following data:

```json
{
  "date": "2 October 2015",
  "genre": [
     "Adventure",
     "Drama",
     "Sci-Fi"
  ],
  "rating": {
    "actual": 8.2,
    "max": 10
  },
  "credits": {
    "acting": [
      "Matt Damon",
      "Jessica Chastain",
      "Kristen Wiig"
    ],
    "directing": [
      "Ridley Scott"
    ],
    "writing": [
      "Drew Goddard",
      "Andy Weir"
    ]
  }
}
```

Summed up, the response from the API would look like this:

```json
{
  "enhancements": {
    "imdb": {
      "date": "2 October 2015",
      "genre": [
         "Adventure",
         "Drama",
         "Sci-Fi"
      ],
      "rating": {
        "actual": 8.2,
        "max": 10
      },
      "credits": {
        "acting": [
          "Matt Damon",
          "Jessica Chastain",
          "Kristen Wiig"
        ],
        "directing": [
          "Ridley Scott"
        ],
        "writing": [
          "Drew Goddard",
          "Andy Weir"
        ]
      }
    }
  },
  "query": {
    "completed": "the martian",
    "original": "the mar"
  },
  "result": {
    "abstract": "Directed by Ridley Scott. With Matt Damon, Jessica Chastain, Kristen Wiig, Kate Mara. During a manned mission to Mars, Astronaut Mark Watney is presumed dead after a ...",
    "title": "The Martian (2015) - IMDb",
    "url": "http://www.imdb.com/title/tt3659388/"
  }
}
```
