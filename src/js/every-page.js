$(document).ready(function() {//  $('head').remove();//  $('body').load('http://tera-forums.enmasse.com/ div#content-primary');//  scrapeAndClean();//  linkHijack();});function scrapeAndClean() {  for (i=0; i < document.styleSheets.length; i++)     { document.styleSheets[i].disabled = true; }};function linkHijack() {    $('a').live("click", function(event) {        event.preventDefault();    var link = 'http://tera-forums.enmasse.com' + $(this).attr("href");    forge.request.ajax({       url: link,       data: {},       success: function (data) {          $("#ajax-content").html($(data).find("#content-primary"));          $("#page-title").text($(data).find('.header h2').text());       },       dataType: 'html'    });    var hist = [];    hist.push(link);  });}event.menuPressed.addListener(function() {  var link = hist[hist.length];  forge.logging.info('backing! hist = '+link);  forge.request.ajax({     url: link,     data: {},     success: function (data) {        $("#ajax-content").html($(data).find("#content-primary"));        $("#page-title").text($(data).find('.header h2').text());     },     dataType: 'html'  });}, function(error) {forge.logging.info(error)});