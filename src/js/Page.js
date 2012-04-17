// Backbone Page.
(function ($) {
  "use strict";

  window.Page = Backbone.Model.extend({
    baseUrl: "http://tera-forums.enmasse.com/",

    loadPage: function () {
      if (this.path) {
        $.get(this.baseUrl + this.path, function (data) {
          var pageData = $(data);
          this.set('title', pageData.find('title').text());
          this.set('data', pageData.find('#content-primary').html());
        });
      }
    },
    isLoaded: function () {
      return (this.data !== undefined);
    }
  });
  window.currentPage = new window.Page({title: 'TERA Forums', path: 'forums', reload: true});

  window.Pages = Backbone.Collection.extend({
    model: window.Page,

    initialize: function (models, options) {
      this.bind("reset", this.reconnectView);
    },

    reconnectView: function () {
      this.setCurrentPage(window.currentPage.get('path'));
    },

    setCurrentPage: function (path) {
      if (this.getPage(path) !== undefined) {
        window.currentPage.set(this.getPage(path).toJSON());
      } else {
        var newPage = new window.Page({path: path});
        newPage.loadPage();
        if (newPage.get('data') !== undefined) {
          window.currentPage.set(newPage.toJSON());
        } else {
          window.currentPage.set({path: path, data: "404 Page not found"});
        }
      }
      return window.currentPage;
    },

    hasPage: function (path) {
      if (this.getPage(path) === undefined) {
        return false;
      }
      return true;
    },

    getPage: function (path) {
      if (path.substring(0, 1) === "/") {
        path = path.substring(1, path.length);
      }
      return _.filter(this.models, function (p) { return p.get('path') === path; })[0];
    }
  });
  window.pages = new window.Pages();

  window.PageView = Backbone.View.extend({
    initialize: function () {
      _.bindAll(this, "render");
      this.model.bind('change', this.render);
    },
    render: function () {
      $('#data-area').html(this.model.get('data'));
      $('#title-area').html(this.model.get('title'));
      return this;
    }
  });

  $(function () {
    window.Uber = new window.Page();
    Backbone.history.start({pushState: true});
    window.pages.fetch();

    $('.page-link').live('click', function (e) {
      e.preventDefault();
      window.Uber.openPage($(this).attr('href'));
    });
  });
}(jQuery));
