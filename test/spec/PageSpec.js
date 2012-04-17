describe("Page", function() {
  var page;

  beforeEach(function() {
    //;
  });

  it("should create a Page", function() {
    page = new Page({path: ""});
    expect(page.get('path')).toEqual("");

    //demonstrates use of custom matcher
    //expect(player).toBePlaying(song);
  });

  describe("when page has not been loaded", function() {
    beforeEach(function() {
      page = new Page({path: ""});
    });

    it("should know it is not loaded.", function() {
      expect(page.get('data')).toEqual(undefined);
      expect(page.isLoaded()).toBeFalsy();
    });

    it("should load the page", function() {
      page.loadPage();
      var t = setTimeout("Finish load test",1000);
      expect(page.get('data')).not.toEqual(undefined);
    });
  });

  // demonstrates use of spies to intercept and test method calls
  //it("tells the current song if the user has made it a favorite", function() {
  //  spyOn(song, 'persistFavoriteStatus');
  //
  //  player.play(song);
  //  player.makeFavorite();
  //
  //  expect(song.persistFavoriteStatus).toHaveBeenCalledWith(true);
  //});
  //
  ////demonstrates use of expected exceptions
  //describe("#resume", function() {
  //  it("should throw an exception if song is already playing", function() {
  //    player.play(song);
  //
  //    expect(function() {
  //      player.resume();
  //    }).toThrow("song is already playing");
  //  });
  //});
});
