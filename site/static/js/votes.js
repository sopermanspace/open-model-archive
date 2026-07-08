(function () {
  var API_BASE = document.body.dataset.apiBase;
  if (!API_BASE) return;

  var TOKEN_KEY = "oma_auth_token";
  var CATEGORY = document.body.dataset.voteCategory;
  var toastTimer = null;

  function getToken() {
    return sessionStorage.getItem(TOKEN_KEY);
  }

  function setToken(token) {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  }

  function captureAuthFromUrl() {
    var hash = location.hash || "";
    var match = hash.match(/oma_token=([^&]+)/);
    if (match) {
      setToken(decodeURIComponent(match[1]));
      history.replaceState(
        null,
        "",
        location.pathname + location.search,
      );
      return true;
    }
    if (new URLSearchParams(location.search).get("oma_auth") === "1") {
      history.replaceState(
        null,
        "",
        location.pathname + location.hash,
      );
    }
    return false;
  }

  function authHeaders() {
    var token = getToken();
    return token ? { Authorization: "Bearer " + token } : {};
  }

  function apiUrl(path) {
    return API_BASE.replace(/\/$/, "") + path;
  }

  function signInUrl() {
    var returnTo = location.href.split("#")[0];
    return (
      apiUrl("/api/auth/login") +
      "?return_to=" +
      encodeURIComponent(returnTo)
    );
  }

  function showToast(message, isError) {
    var toast = document.getElementById("vote-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "vote-toast";
      toast.className = "vote-toast";
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.toggle("is-error", Boolean(isError));
    toast.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toast.classList.remove("is-visible");
    }, 2800);
  }

  function updateAuthUi(user) {
    var signIn = document.getElementById("oma-signin");
    var userEl = document.getElementById("oma-user");
    var signOut = document.getElementById("oma-signout");
    if (!signIn || !userEl) return;

    if (user && user.login) {
      signIn.classList.add("hidden");
      userEl.classList.remove("hidden");
      userEl.innerHTML =
        '<img class="auth-avatar" src="' +
        (user.avatar_url || "") +
        '" alt="" width="20" height="20">' +
        "<span>@" +
        user.login +
        "</span>";
      if (signOut) signOut.classList.remove("hidden");
    } else {
      signIn.classList.remove("hidden");
      userEl.classList.add("hidden");
      userEl.textContent = "";
      if (signOut) signOut.classList.add("hidden");
    }
  }

  function fetchMe() {
    return fetch(apiUrl("/api/auth/me"), {
      headers: authHeaders(),
    })
      .then(function (res) {
        return res.json();
      })
      .then(function (data) {
        updateAuthUi(data.authenticated ? data.user : null);
        return data;
      })
      .catch(function () {
        updateAuthUi(null);
        return { authenticated: false };
      });
  }

  function modelLabel(modelId) {
    var bar = document.querySelector(
      '.vote-bar[data-model-id="' + modelId + '"]',
    );
    if (bar) {
      var col = bar.closest(".model-column");
      if (col) {
        var heading = col.querySelector(".model-header h2");
        if (heading) return heading.textContent.trim();
      }
    }
    var slug = modelId.split("/").pop() || modelId;
    return slug.replace(/-/g, " ");
  }

  function applyCounts(stats, userVote) {
    var bars = document.querySelectorAll(".vote-bar");
    bars.forEach(function (bar) {
      var modelId = bar.dataset.modelId;
      var likeBtn = bar.querySelector(".vote-like");
      var dislikeBtn = bar.querySelector(".vote-dislike");
      var likeCount = bar.querySelector(".like-count");
      var dislikeCount = bar.querySelector(".dislike-count");

      var modelStats = (stats.models || []).find(function (m) {
        return m.model_id === modelId;
      });
      if (likeCount) likeCount.textContent = modelStats ? modelStats.likes : 0;
      if (dislikeCount) {
        dislikeCount.textContent = modelStats ? modelStats.dislikes : 0;
      }

      if (likeBtn) likeBtn.classList.remove("is-active");
      if (dislikeBtn) dislikeBtn.classList.remove("is-active");
      if (userVote && userVote.model_id === modelId) {
        if (userVote.reaction === "like" && likeBtn) {
          likeBtn.classList.add("is-active");
        }
        if (userVote.reaction === "dislike" && dislikeBtn) {
          dislikeBtn.classList.add("is-active");
        }
      }
    });
  }

  function loadStats() {
    if (!CATEGORY) return Promise.resolve();
    var url = apiUrl("/api/votes?category=" + encodeURIComponent(CATEGORY));
    return fetch(url, { headers: authHeaders() })
      .then(function (res) {
        return res.json();
      })
      .then(function (data) {
        applyCounts(data, data.user_vote);
      })
      .catch(function () {});
  }

  function setBarLoading(bar, loading) {
    bar.querySelectorAll(".vote-btn").forEach(function (btn) {
      btn.disabled = loading;
    });
  }

  function castVote(bar, reaction) {
    if (!getToken()) {
      location.href = signInUrl();
      return;
    }

    var payload = {
      category: bar.dataset.category,
      task_slug: bar.dataset.taskSlug,
      model_id: bar.dataset.modelId,
      reaction: reaction,
    };

    setBarLoading(bar, true);

    fetch(apiUrl("/api/votes"), {
      method: "POST",
      headers: Object.assign(
        { "Content-Type": "application/json" },
        authHeaders(),
      ),
      body: JSON.stringify(payload),
    })
      .then(function (res) {
        if (res.status === 401) {
          setToken(null);
          showToast("Session expired — sign in again", true);
          setTimeout(function () {
            location.href = signInUrl();
          }, 900);
          return null;
        }
        return res.json().then(function (data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function (result) {
        if (!result) return;
        if (!result.ok) {
          showToast(result.data.error || "Could not save vote", true);
          return;
        }
        applyCounts(result.data, result.data.user_vote);
        showToast(
          result.data.user_vote ? "Vote saved" : "Vote removed",
          false,
        );
      })
      .catch(function () {
        showToast("Network error — try again", true);
      })
      .finally(function () {
        setBarLoading(bar, false);
      });
  }

  function initVoteBars() {
    document.querySelectorAll(".vote-bar").forEach(function (bar) {
      var likeBtn = bar.querySelector(".vote-like");
      var dislikeBtn = bar.querySelector(".vote-dislike");
      if (likeBtn) {
        likeBtn.addEventListener("click", function () {
          castVote(bar, "like");
        });
      }
      if (dislikeBtn) {
        dislikeBtn.addEventListener("click", function () {
          castVote(bar, "dislike");
        });
      }
    });
  }

  function initAuthControls() {
    var signIn = document.getElementById("oma-signin");
    var signOut = document.getElementById("oma-signout");
    if (signIn) {
      signIn.addEventListener("click", function () {
        location.href = signInUrl();
      });
    }
    if (signOut) {
      signOut.addEventListener("click", function () {
        setToken(null);
        updateAuthUi(null);
        loadStats();
      });
    }
  }

  function initCommunityPrefs() {
    var panel = document.getElementById("community-prefs");
    if (!panel) return;

    fetch(apiUrl("/api/votes"))
      .then(function (res) {
        return res.json();
      })
      .then(function (data) {
        var categories = data.categories || {};
        var keys = Object.keys(categories);
        if (!keys.length) {
          panel.classList.add("hidden");
          return;
        }
        var html = "";
        keys.sort().forEach(function (cat) {
          var entry = categories[cat];
          var liked = entry.top_liked;
          var disliked = entry.top_disliked;
          if (!liked && !disliked) return;
          html +=
            '<div class="pref-row"><span class="pref-category">' +
            cat +
            "</span>";
          if (liked) {
            html +=
              '<span class="pref-like">Most liked: <strong>' +
              modelLabel(liked.model_id) +
              "</strong> (" +
              liked.count +
              ")</span>";
          }
          if (disliked) {
            html +=
              '<span class="pref-dislike">Most disliked: <strong>' +
              modelLabel(disliked.model_id) +
              "</strong> (" +
              disliked.count +
              ")</span>";
          }
          html += "</div>";
        });
        if (!html) {
          panel.classList.add("hidden");
          return;
        }
        panel.querySelector(".pref-grid").innerHTML = html;
      })
      .catch(function () {
        panel.classList.add("hidden");
      });
  }

  captureAuthFromUrl();
  initAuthControls();
  initVoteBars();
  fetchMe().then(loadStats);
  initCommunityPrefs();
})();