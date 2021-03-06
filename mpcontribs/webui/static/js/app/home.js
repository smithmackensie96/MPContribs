define(function(require) {
  var $ = require('jquery');
  require('archieml');
  require('sandbox');
  require('thebe');
  var env = require('env');

  // prepare ArchieML sandbox (when ready)
  $.ready(function() {
    var qs = window.location.search.substring(1);
    qs.split('&').forEach(function(term) {
      var temp = term.split('=');
      if (temp[0] == 'aml') {
        var source = decodeURIComponent(temp[1].replace(/\+/g, " "));
        var aml = document.getElementsByTagName('aml')[0];
        aml.innerHTML = source;
      }
    });
  });

  // Thebe Jupyter Notebook Cell
  $(function(){
    console.log('starting Thebe');
    var thebe = new Thebe({
      tmpnb_mode: false,
      add_interrupt_button: true,
      url: env.jupyter_url
    });
    console.log(env.jupyter_url);
    var $button = $('<button id="savecells" type="button">Save Code</button>');
    $button.appendTo($('.thebe_controls'));
    var $button2 = $('<button type=button onClick="$(\'#myModal\').modal()"><span class="glyphicon glyphicon-info-sign" aria-hidden="true"></span></button>');
    $button2.appendTo($('.thebe_controls'));
  });

  // save cell contents to hidden input field to preserve code changes
  $('#savecells').on('click', function (e) {
    var thebe_elem = document.getElementById('inputthebe');
    var thebe_nodes = document.getElementsByTagName('pre');
    var thebe_cells = [];
    for (var i=0; i<thebe_nodes.length; i++) {
      if (thebe_nodes[i].classList.contains("CodeMirror-line")) {
        var div = document.createElement("div");
        div.innerHTML = thebe_nodes[i].firstChild.innerHTML;
        var text = div.textContent || div.innerText || "";
        thebe_cells.push(text);
      }
    }
    thebe_elem.value = JSON.stringify(thebe_cells);
    this.innerHTML = 'Save Code <span class="glyphicon glyphicon-ok" aria-hidden="true"></span>';
  });

});
