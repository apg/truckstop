# Truckstop

## About Truckstop

Truckstop is a code challenge, originally developed for an [Uber Coding Challenge](https://github.com/uber/coding-challenge-tools). It provides a simple search interface to food trucks in San Francisco, using the data (though it's not continually updated) from [here](https://data.sfgov.org/Permitting/Mobile-Food-Facility-Permit/rqzj-sfat).

It's a one page app, which utilizes a [bottle](http://bottlepy.org) application that serves static files, and responds to a single AJAX endpoint. On the front end, it uses [leaflet](http://leafletjs.com) to display a map, and [jQuery](http://jquery.org) to do anything else. An attempt was made to make the interaction simple and easy, but my frontend skills have atrophied over the years, and I didn't want to spend too too much time perfecting it. Leaflet was new to me, but pretty nice. And I haven't seriously used jQuery since 1.4. Bottle has served me well in the past for quick applications.

The site doesn't use a typical relational database. Instead, it opts for storing all the data in a Python dictionary. It indexes the contents of this dictionary with two special purposes indexes—a spatial index and a text index. I choose to do this primarily because the data is static and because I wanted to write my own indexing. Data loads and indexing happen at startup and take virtually no time at all.

The spatial index stores latitude, longitude pairs along with an object id in a kd-tree, which is a binary tree that alternates between x and y values of the coordinates for how it does branching. The result, is that we get very efficient lookups for geographical data.

The text index uses a frequency based approach and TF-IDF to index the text. TF-IDF values for each word in a query are computed on each candidate document, and the dot product of the formed vectors is computed giving us a relevancy score. The approach is rather naive, but it does take into consideration that 'food' is not as important as a word such as 'cupcake' for relevancy.

## Query Help

By default, the latitude and longitude are set to downtown San Francisco. If you choose to share your location, and are outside San Francisco, you're unlikely to get any data back for a search.

### Fixing your location

You can fix your location by adding the query parameters `?lat=[latitude]&lon=[longitude]` to the URL.

### Setting the radius

You can specify a radius for your search by adding to your query `within:[radius]`.
