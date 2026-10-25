// Moreland Associates — site behaviour: navigation, forms, Market Traction Test, Get Started topics.
(function () {
  "use strict";

  // ---- Mobile menu ----
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // ---- Dropdowns (click/tap support; hover is handled in CSS) ----
  document.querySelectorAll(".nav-group > button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var group = btn.parentElement;
      var open = !group.classList.contains("open");
      document.querySelectorAll(".nav-group.open").forEach(function (g) {
        g.classList.remove("open");
        g.querySelector("button").setAttribute("aria-expanded", "false");
      });
      group.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".nav-group")) {
      document.querySelectorAll(".nav-group.open").forEach(function (g) {
        g.classList.remove("open");
        g.querySelector("button").setAttribute("aria-expanded", "false");
      });
    }
  });

  // ---- Get Started: tailor the page to the ?topic= it was opened with ----
  var TOPICS = {
    "market-traction": {
      title: "Market Traction",
      lead: "We are here to help you reach the next milestone in your journey to achieve market traction and build your beachhead. Let us know the best way to reach you and we’ll be in touch right away."
    },
    "interim-executive": {
      title: "Interim Executive",
      lead: "Let us know the best way to reach you and we’ll be in touch right away to talk about the interim leadership your company needs."
    }
  };
  var topicHead = document.querySelector("[data-topic-title]");
  if (topicHead) {
    var key = new URLSearchParams(location.search).get("topic");
    // Topics from retired services now go to the interim executive version
    if (key === "pipeline-acceleration" || key === "revenue-lifecycle") key = "interim-executive";
    var t = TOPICS[key];
    if (t) {
      topicHead.textContent = t.title;
      document.querySelector("[data-topic-lead]").textContent = t.lead;
      document.title = t.title + " | Moreland Associates";
      document.querySelectorAll('input[name="topic"]').forEach(function (i) { i.value = key; });
    }
  }

  // ---- Forms: submit to the form service without leaving the page ----
  document.querySelectorAll("form[data-form]").forEach(function (form) {
    var status = form.querySelector(".form-status");
    // Tell the recipient where the enquiry came from
    var h1 = document.querySelector("h1");
    var heading = h1 ? h1.textContent.trim() : document.title;
    var cameFrom = document.referrer && document.referrer.indexOf(location.origin) === 0 ? document.referrer : (document.referrer ? "another site: " + document.referrer : "direct visit");
    var set = function (name, value) { var f = form.querySelector('input[name="' + name + '"]'); if (f) f.value = value; };
    set("page_heading", heading);
    set("form_page", location.href);
    set("came_from", cameFrom);
    var subject = form.querySelector('input[name="_subject"]');
    if (subject && heading && subject.value.indexOf(heading) === -1) subject.value += " · " + heading;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var btn = form.querySelector('[type="submit"]');
      status.className = "form-status";
      status.textContent = "";
      if (form.action.indexOf("REPLACE_WITH_FORM_ID") !== -1) {
        status.classList.add("err");
        status.textContent = "This form isn’t connected yet. Please email info@morelandassoc.com or call (510) 833-7308.";
        return;
      }
      btn.disabled = true;
      btn.textContent = "Sending…";
      fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" }
      }).then(function (res) {
        if (!res.ok) throw new Error(res.status);
        form.reset();
        status.classList.add("ok");
        status.textContent = "Thank you — we’ll be in touch shortly.";
      }).catch(function () {
        status.classList.add("err");
        status.textContent = "Sorry, something went wrong. Please email info@morelandassoc.com or call (510) 833-7308.";
      }).then(function () {
        btn.disabled = false;
        btn.textContent = "Submit";
      });
    });
  });

  // ---- Market Traction Test ----
  // One point per "Yes". 0–1 = Eureka, 2 = Kaa Ching … 6 = Market Traction (same scoring as the original site).
  var quiz = document.getElementById("traction-test");
  if (quiz) {
    var STAGES = ["eureka", "eureka", "kaa-ching", "two-thumbs-up", "momentum", "building-buzz", "market-traction"];
    quiz.addEventListener("submit", function (e) {
      e.preventDefault();
      var score = 0;
      var firstMissing = null;
      quiz.querySelectorAll("fieldset").forEach(function (fs) {
        var picked = fs.querySelector("input:checked");
        fs.classList.toggle("missing", !picked);
        if (!picked && !firstMissing) firstMissing = fs;
        if (picked) score += Number(picked.value);
      });
      if (firstMissing) {
        firstMissing.scrollIntoView({ behavior: "smooth", block: "center" });
        firstMissing.querySelector("input").focus({ preventScroll: true });
        return;
      }
      location.href = quiz.getAttribute("data-results") + STAGES[score] + "/";
    });
    quiz.addEventListener("change", function (e) {
      var fs = e.target.closest("fieldset");
      if (fs) fs.classList.remove("missing");
    });
  }
})();
