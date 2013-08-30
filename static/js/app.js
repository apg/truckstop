$(function() {
  var DEFAULT_POSITION = [37.783333, -122.416667];

  // XXX: not the greatest, but should do for our purposes
  var parseQuery = function() {
    var result = {}, bits = window.location.search.slice(1).split('&');
    for (pair in bits) {
      var pbits = pair.split('=');
      result[pbits[0]] = pbits[1] || '';
    }
    return result;
  };

  var getPosition = function(cb) {
    query = parseQuery();
    if (query['lat'] && query['lon']) {
      // use a fixed position
      cb([query['lat'], query['lon']]);
    }
    else if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(cb);
    }
    else {
      cb(DEFAULT_LOCATION);
    }
  };


  var MAP = L.map('map').setView(DEFAULT_POSITION, 13);
  
  // center the map on our current position
  getPosition(function(position) {
    MAP.setView(position, 13);
  });

  // add an OpenStreetMap tile layer
  L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(MAP);

  // Just a temporary thing-a-ma-bob
  $('body').on('click', function() {
    $('#map').css({'height': '200px'});     
    $('.result-list').css({'display': 'block'});
  });

  $(window).scroll(function() {
    if ($('.result-list:visible')) {
      console.log($(window).scrollTop());
      if ($(window).scrollTop() > 48) {
        $('#map').css({'top': ($(window).scrollTop() - 48) + 'px'}).addClass('map-scrolling');
      }
      else {
        $('#map').css({'top': '0'}).removeClass('map-scrolling');
      }

    }
  });

});
