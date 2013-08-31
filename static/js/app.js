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
  var DEFAULT_ICON = new L.Icon.Default();
  var CURRENT_LOCATION = [DEFAULT_POSITION[0], DEFAULT_POSITION[1]];
  var CURRENT_LOCATION_MARKER;
  var MARKERS = {};
  var MAP = L.map('map').setView(DEFAULT_POSITION, 13);
  var RESULT_TEMPLATE = Mustache.compile('<span class="clear-button">X</span><h2>Search Results</h2>' + 
'  {{#venues}}' +
'<dl id="anchor-{{ObjectID}}" data-id="{{ObjectID}}">' + 
'    <dt><span class="distance">{{ distance_desc }}</span><span class="name">{{ Applicant }}</span></dt>' +
'    <dd><span class="address">{{ Address }}</span>' +
'     <p><strong>Serves:</strong> {{ FoodItems }}</p>' +
'  </dd></dl>' +
'  {{/venues}}' +
'  {{^venues}}' +
'   <h2>No results found!</h2>' +
'  {{/venues}}');

  var HIGHLIGHT_ICON = L.icon({
      iconUrl: '/static/img/active-marker-icon.png',
      iconRetinaUrl: '/static/img/active-marker-icon@2x.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41],
      shadowUrl: '/static/img/marker-shadow.png'
  });

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

  var resetEverything = function() {
    for (var m in MARKERS) {
      MAP.removeLayer(MARKERS[m]);
    };
    MARKERS = {};
    $('#map').css({'height': '500px'});
    MAP.invalidateSize();
    $('.result-list').css({'display': 'none'});
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



  $(document).on('click', '.clear-button', function(e) {
    $('.search input').val('');
    resetEverything();
  });
  
  // center the map on our current position
  getPosition(function(position) {
    MAP.setView(position, 13);
    CURRENT_LOCATION = position;

    var here = L.icon({
        iconUrl: '/static/img/here-marker-icon.png',
        iconRetinaUrl: '/static/img/here-marker-icon@2x.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowUrl: '/static/img/marker-shadow.png',
        shadowSize: [41, 41]
    });

    CURRENT_LOCATION_MARKER = L.marker(CURRENT_LOCATION, {icon: here}).addTo(MAP);

  });

  $('.search input').keyup(function(event) {
    if (event.which == 13) {
      event.preventDefault();
      resetEverything();
      var query = $('.search input').val();

      getSearchResults(query, function(results) {
        if (results.venues) {
          // render a template to put in the result-list.innerHTML
          for (var i = 0; i < results.venues.length; i++) {
            var venue = results.venues[i];
            MARKERS[venue['ObjectID']] = L.marker([parseFloat(venue['Latitude']), parseFloat(venue['Longitude'])]).addTo(MAP);
            MARKERS[venue['ObjectID']].on('mouseover', (function (v) {
              return function(e) {
                 MARKERS[v['ObjectID']].setIcon(HIGHLIGHT_ICON);
                 var off = $('#anchor-' + v['ObjectID']).offset();
                 $(window).scrollTop(off.top - 220);
                 $('#anchor-' + v['ObjectID']).addClass('hover-state');
              }})(venue));
            MARKERS[venue['ObjectID']].on('mouseout', (function (v) {
              return function(e) {
                 MARKERS[v['ObjectID']].setIcon(DEFAULT_ICON);
                 $('#anchor-' + v['ObjectID']).removeClass('hover-state');
              }})(venue));

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
    MARKERS[$(this).data('id')].setIcon(HIGHLIGHT_ICON);
  });
  $(document).on('mouseout', '.result-list dl', function(event) {
    $(this).removeClass('hover-state');
    MARKERS[$(this).data('id')].setIcon(DEFAULT_ICON);
  });

  // On scroll when result list is available, fix map to the top of the screen.
  $(window).scroll(function() {
    if ($('.result-list:visible')) {
      if ($(window).scrollTop() > 58) {
        $('#map').css({'top': ($(window).scrollTop() - 58) + 'px'}).addClass('map-scrolling');
      }
      else {
        $('#map').css({'top': '0'}).removeClass('map-scrolling');
      }

    }
  });

});
