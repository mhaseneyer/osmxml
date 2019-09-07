# osmxml
OpenStreetMap XML processing (like for creating SVG vector graphics)

This project started when I needed a possibility to convert some of
OpenStreetMap's data to SVG (Scalable Vector Graphics) files, without setting up
a full-features GIS environment and just using what was already on my machine.

## How to start?

I assume you have Python 3 already installed, this is the only prerequisite. It
then should run out of the box with:

```
python3 osm2svg [URL] [xmlfile] [svgfile]
```

What does all this mean?

- `python3` should start Python.
- `osm2svg` is the name of the script.
- `URL` is the URL from OpenStreetMap that points to the node, relation or way
  you want to draw
- `xmlfile` is the path and file name of a file where either the downloaded data
  shall be stored locally (when you also provide a URL), or the file where data
  can be found locally (when you do not provide a URL).
- `svgfile` is the path and name of the target file. (You can omit this if you
  only want to download data from OpenStreetMap.

The order of `URL`, `xmlfile` and  `svgfile` does not matter.

A short example could look like this:

```
python3 osm2xml https://www.openstreetmap.org/relation/62450 suhl.svg
```

This will download the administrative boundary of Suhl, a town in Thuringia in
Germany, and create a graphic called `suhl.svg` based on that boundary in the
current folder.

Rather preparing offline work? The first step is downloading nevertheless:

```
python3 osm2xml https://www.openstreetmap.org/relation/62450 suhl.xml
```

But then we can use this XML file as source:

```
python3 osm2xml suhl.xml suhl.svg
```

## How to obtain the URLs for OpenStreetMap objects?

You use the search box at [OpenStreetMap](https://www.openstreetmap.org/) and
enter anything you want to search (obiously I took "Suhl"). Then click on one of
the search results. Now you should see the object painted in OpenStreetMap in
orange, with some technical data on the left side. Use the URL that your browser
shows.