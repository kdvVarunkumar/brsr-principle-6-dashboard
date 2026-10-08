  // ---- shared by index.html and compare_companies.html: finding things, filling a dropdown, showing a page in the frame
  function $(id) { return document.getElementById(id); }

  function find(list, test) { return list.filter(test)[0]; }

  function fromHash() {
    try { return decodeURIComponent(location.hash.slice(1)); } catch (error) { return ""; }
  }

  function setOptions(select, items) {
    var keep = select.value;
    select.textContent = "";
    items.forEach(function (item) {
      var option = document.createElement("option");
      option.value = item.value;
      option.textContent = item.text;
      select.appendChild(option);
    });
    if (items.some(function (item) { return item.value === keep; })) { select.value = keep; }
  }

  // A page shown through srcdoc takes the address of the viewer, so a link such as href="#dash-energy" would try to load the viewer itself
  // into the frame (and fail). <base href="about:srcdoc"> makes such a link jump inside the page. Only the frame gets it, not "Open in a new tab".
  function forFrame(page) {
    return page.replace(/<head[^>]*>/i, function (tag) { return tag + '<base href="about:srcdoc">'; });
  }

  function makeViewer(entries) {
    var frame = $("viewer");
    var openTab = $("open-tab");
    var byId = {};
    var current = null;
    entries.forEach(function (entry) { byId[entry.id] = entry; });
    openTab.addEventListener("click", function (event) {
      if (!current) { event.preventDefault(); return; }
      openTab.href = typeof current.html === "string"
        ? URL.createObjectURL(new Blob([current.html], { type: "text/html" }))
        : encodeURI(current.file);
    });
    return {
      byId: byId,
      show: function (id) {
        var entry = byId[id];
        if (!entry) { return null; }
        current = entry;
        if (typeof entry.html === "string") {
          frame.srcdoc = forFrame(entry.html);
        } else {
          frame.removeAttribute("srcdoc");
          frame.src = encodeURI(entry.file);
        }
        document.title = entry.label;
        try { history.replaceState(null, "", "#" + encodeURIComponent(id)); } catch (error) { /* the page still works without a saved address */ }
        return entry;
      }
    };
  }
