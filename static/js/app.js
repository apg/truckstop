if (!String.prototype.encodeHTML) {
  String.prototype.encodeHTML = function () {
    return this.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;')
               .replace(/"/g, '&quot;');
  };
}
$(function() {
  var DEFAULT_POSITION = [37.783333, -122.416667];
  var CURRENT_LOCATION = [DEFAULT_POSITION[0], DEFAULT_POSITION[1]];
  var MARKERS = {};
  var MAP = L.map('map').setView(DEFAULT_POSITION, 13);
  var RESULT_TEMPLATE = Mustache.compile('<h2>Search Results</h2>' + 
'  {{#venues}}' +
'<dl data-id="{{ObjectID}}">' + 
'    <dt><span class="distance">{{ distance_desc }}</span><span class="name">{{ Applicant }}</span></dt>' +
'    <dd><span class="address">{{ Address }}</span>' +
'     <p><strong>Serves:</strong> {{ FoodItems }}</p>' +
'  </dd></dl>' +
'  {{/venues}}' +
'  {{^venues}}' +
'   <h2>No results found!</h2>' +
'  {{/venues}}');


  L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(MAP);

  // XXX: not the greatest, but should do for our purposes
  var parseQuery = function() {
    var result = {}, bits = window.location.search.slice(1).split('&');
    for (var i = 0; i < bits.length; i++) {
      var pbits = bits[i].split('=');
      result[pbits[0]] = pbits[1] || '';
      console.log(pbits[0] + " = " + pbits[1]);
    }
    return result;
  };

  var getPosition = function(cb) {
    query = parseQuery();
    console.log(query);
    if (query['lat'] && query['lon']) {
      // use a fixed position
      cb([parseFloat(query['lat']), parseFloat(query['lon'])]);
    }
    else if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(cb);
    }
    else {
      cb(DEFAULT_LOCATION);
    }
  };

  var getSearchResults = function(query, dcb, ecb) {
    var req = $.getJSON('/api/v1/search.json', {
        'query': query,
        'lat': CURRENT_LOCATION[0],
        'lon': CURRENT_LOCATION[1]
        }).done(dcb);
    if (ecb) {
      req.fail(ecb);
    }
  };
  
  // center the map on our current position
  getPosition(function(position) {
    MAP.setView(position, 13);
    CURRENT_POSITION = position;
  });

  $('.search input').keyup(function(event) {
    if (event.which == 13) {
      event.preventDefault();
      var query = $('.search input').val();

      getSearchResults(query, function(results) {
        if (results.venues) {
          // render a template to put in the result-list.innerHTML
          for (var i = 0; i < results.venues.length; i++) {
            var venue = results.venues[i];
            MARKERS[venue['ObjectID']] = L.marker([parseFloat(venue['Latitude']), parseFloat(venue['Longitude'])]).addTo(MAP);
          }

          $('#map').css({'height': '200px'});
          MAP.invalidateSize();
          $('.result-list').css({'display': 'block'}).html(RESULT_TEMPLATE({ 'venues': results.venues }));
        }
      });
    }

  });


  $(document).on('mouseover', '.result-list dl', function(event) {
    $(this).addClass('hover-state');
    var marker = MARKERS[$(this).data('id')];
    MAP.panTo(marker.getLatLng());

  });
  $(document).on('mouseout', '.result-list dl', function(event) {
    $(this).removeClass('hover-state');
  });

  // On scroll when result list is available, fix map to the top of the screen.
  $(window).scroll(function() {
    if ($('.result-list:visible')) {
      console.log($(window).scrollTop());
      if ($(window).scrollTop() > 58) {
        $('#map').css({'top': ($(window).scrollTop() - 58) + 'px'}).addClass('map-scrolling');
      }
      else {
        $('#map').css({'top': '0'}).removeClass('map-scrolling');
      }

    }
  });

});
