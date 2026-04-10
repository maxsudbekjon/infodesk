(function () {
    var body = document.body;
    var layout = document.querySelector("[data-admin-layout]");
    var mobileToggle = document.querySelector("[data-sidebar-mobile-toggle]");
    var sidebarToggle = document.querySelector("[data-sidebar-toggle]");
    var sidebarScrim = document.querySelector("[data-sidebar-scrim]");
    var dropdownButtons = Array.prototype.slice.call(document.querySelectorAll("[data-dropdown-toggle]"));
    var modal = document.querySelector("[data-admin-modal]");
    var modalFrame = document.querySelector("[data-admin-modal-frame]");
    var modalTitle = document.querySelector("[data-admin-modal-title]");
    var modalCloseButtons = Array.prototype.slice.call(document.querySelectorAll("[data-admin-modal-close]"));
    var searchRoot = document.querySelector("[data-global-search]");
    var sidebarStorageKey = "infodesk-admin-sidebar-collapsed";
    var activeDropdown = null;
    var activeSearchController = null;

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function debounce(fn, delay) {
        var timer = null;
        return function () {
            var args = arguments;
            clearTimeout(timer);
            timer = window.setTimeout(function () {
                fn.apply(null, args);
            }, delay);
        };
    }

    function closeDropdown(menuOwner) {
        if (!menuOwner) {
            return;
        }

        var button = menuOwner.querySelector("[data-dropdown-toggle]");
        var menu = menuOwner.querySelector("[data-dropdown-menu]");
        if (button) {
            button.setAttribute("aria-expanded", "false");
        }
        if (menu) {
            menu.hidden = true;
        }
        if (activeDropdown === menuOwner) {
            activeDropdown = null;
        }
    }

    function openDropdown(menuOwner) {
        if (!menuOwner) {
            return;
        }
        if (activeDropdown && activeDropdown !== menuOwner) {
            closeDropdown(activeDropdown);
        }

        var button = menuOwner.querySelector("[data-dropdown-toggle]");
        var menu = menuOwner.querySelector("[data-dropdown-menu]");
        if (button) {
            button.setAttribute("aria-expanded", "true");
        }
        if (menu) {
            menu.hidden = false;
        }
        activeDropdown = menuOwner;
    }

    dropdownButtons.forEach(function (button) {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            var owner = button.closest(".admin-dropdown");
            if (!owner) {
                return;
            }
            if (activeDropdown === owner) {
                closeDropdown(owner);
                return;
            }
            openDropdown(owner);
        });
    });

    document.addEventListener("click", function (event) {
        if (activeDropdown && !activeDropdown.contains(event.target)) {
            closeDropdown(activeDropdown);
        }
    });

    function setSidebarCollapsed(collapsed) {
        body.classList.toggle("sidebar-collapsed", collapsed);
        try {
            window.localStorage.setItem(sidebarStorageKey, collapsed ? "1" : "0");
        } catch (error) {
            // Ignore localStorage errors.
        }
    }

    if (layout) {
        try {
            setSidebarCollapsed(window.localStorage.getItem(sidebarStorageKey) === "1");
        } catch (error) {
            setSidebarCollapsed(false);
        }
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", function () {
            setSidebarCollapsed(!body.classList.contains("sidebar-collapsed"));
        });
    }

    function closeMobileSidebar() {
        body.classList.remove("sidebar-mobile-open");
    }

    if (mobileToggle) {
        mobileToggle.addEventListener("click", function () {
            body.classList.toggle("sidebar-mobile-open");
        });
    }

    if (sidebarScrim) {
        sidebarScrim.addEventListener("click", closeMobileSidebar);
    }

    function shouldOpenInModal(anchor) {
        return false;
    }

    function withModalParam(href) {
        var url = new window.URL(href, window.location.origin);
        url.searchParams.set("_ui_modal", "1");
        return url.toString();
    }

    function openModal(href, title) {
        if (!modal || !modalFrame) {
            window.location.href = href;
            return;
        }
        if (modalTitle) {
            modalTitle.textContent = title || "Admin oynasi";
        }
        modal.hidden = false;
        body.classList.add("modal-open");
        modalFrame.src = withModalParam(href);
    }

    function closeModal() {
        if (!modal || !modalFrame) {
            return;
        }
        modal.hidden = true;
        body.classList.remove("modal-open");
        modalFrame.src = "about:blank";
    }

    modalCloseButtons.forEach(function (button) {
        button.addEventListener("click", closeModal);
    });

    document.addEventListener("click", function (event) {
        var anchor = event.target.closest("a");
        if (!shouldOpenInModal(anchor)) {
            return;
        }

        event.preventDefault();
        closeDropdown(activeDropdown);
        openModal(anchor.href, (anchor.textContent || "").trim());
    });

    if (modalFrame) {
        modalFrame.addEventListener("load", function () {
            var frameLocation;
            try {
                frameLocation = modalFrame.contentWindow.location;
            } catch (error) {
                return;
            }

            if (!frameLocation || frameLocation.href === "about:blank") {
                return;
            }

            var url = new window.URL(frameLocation.href);
            if (url.searchParams.get("_modal_updated") === "1") {
                closeModal();
                window.location.reload();
            }
        });
    }

    document.addEventListener("submit", function (event) {
        var form = event.target;
        var confirmMessage = form.getAttribute("data-confirm");
        if (confirmMessage && !window.confirm(confirmMessage)) {
            event.preventDefault();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeDropdown(activeDropdown);
            closeModal();
            closeMobileSidebar();
        }
    });

    function renderSearchResults(resultsContainer, results) {
        if (!results.length) {
            resultsContainer.innerHTML = '<div class="admin-search-results__state">Hech narsa topilmadi.</div>';
            return;
        }

        var groups = {};
        results.forEach(function (item) {
            if (!groups[item.category]) {
                groups[item.category] = [];
            }
            groups[item.category].push(item);
        });

        var html = Object.keys(groups).map(function (groupName) {
            var groupItems = groups[groupName].map(function (item) {
                return (
                    '<a href="' + escapeHtml(item.url) + '" class="admin-search-results__item js-admin-modal-trigger">' +
                        '<div>' +
                            '<strong>' + escapeHtml(item.title) + '</strong>' +
                            '<div class="admin-search-results__meta">' + escapeHtml(item.meta || "") + "</div>" +
                        "</div>" +
                        '<span class="status-badge status-badge--info">' + escapeHtml(groupName) + "</span>" +
                    "</a>"
                );
            }).join("");

            return (
                '<div class="admin-search-results__group">' +
                    '<div class="admin-search-results__label">' + escapeHtml(groupName) + "</div>" +
                    groupItems +
                "</div>"
            );
        }).join("");

        resultsContainer.innerHTML = html;
    }

    if (searchRoot) {
        var searchInput = searchRoot.querySelector("[data-global-search-input]");
        var resultsContainer = searchRoot.querySelector("[data-global-search-results]");

        if (searchInput && resultsContainer) {
            var runSearch = debounce(function (value) {
                if (value.length < 2) {
                    resultsContainer.hidden = false;
                    resultsContainer.innerHTML = '<div class="admin-search-results__state">Kamida 2 ta harf yoki raqam kiriting</div>';
                    return;
                }

                if (activeSearchController) {
                    activeSearchController.abort();
                }

                activeSearchController = new window.AbortController();
                resultsContainer.hidden = false;
                resultsContainer.innerHTML = '<div class="admin-search-results__state">Qidirilmoqda...</div>';

                window.fetch(searchInput.dataset.searchUrl + "?q=" + encodeURIComponent(value), {
                    signal: activeSearchController.signal,
                    headers: { "X-Requested-With": "XMLHttpRequest" }
                })
                    .then(function (response) {
                        return response.json();
                    })
                    .then(function (payload) {
                        renderSearchResults(resultsContainer, payload.results || []);
                    })
                    .catch(function (error) {
                        if (error.name === "AbortError") {
                            return;
                        }
                        resultsContainer.innerHTML = '<div class="admin-search-results__state">Qidiruvda xatolik yuz berdi.</div>';
                    });
            }, 220);

            searchInput.addEventListener("focus", function () {
                resultsContainer.hidden = false;
            });

            searchInput.addEventListener("input", function (event) {
                runSearch((event.target.value || "").trim());
            });

            document.addEventListener("click", function (event) {
                if (!searchRoot.contains(event.target)) {
                    resultsContainer.hidden = true;
                }
            });
        }
    }

    Array.prototype.slice.call(document.querySelectorAll(".search-filter, .search-filter-mptt")).forEach(function (field) {
        function syncFilterName() {
            var option = field.options[field.selectedIndex];
            var selectName = option ? option.getAttribute("data-name") : null;
            if (selectName) {
                field.setAttribute("name", selectName);
            } else {
                field.removeAttribute("name");
            }
        }

        syncFilterName();
        field.addEventListener("change", function () {
            syncFilterName();
            var form = field.form || field.closest("form");
            if (form) {
                form.submit();
            }
        });
    });

    function getCookie(name) {
        var cookieValue = null;
        if (!document.cookie) {
            return cookieValue;
        }

        document.cookie.split(";").forEach(function (cookie) {
            var trimmed = cookie.trim();
            if (trimmed.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(trimmed.substring(name.length + 1));
            }
        });

        return cookieValue;
    }

    function submitQuickDelete(button) {
        var action = button.getAttribute("data-quick-delete-url");
        if (!action) {
            return;
        }

        var confirmMessage = button.getAttribute("data-confirm");
        if (confirmMessage && !window.confirm(confirmMessage)) {
            return;
        }

        var csrfToken = getCookie("csrftoken");
        if (!csrfToken) {
            var csrfInput = document.querySelector("input[name='csrfmiddlewaretoken']");
            csrfToken = csrfInput ? csrfInput.value : "";
        }

        var form = document.createElement("form");
        form.method = "post";
        form.action = action;
        form.style.display = "none";

        var csrfField = document.createElement("input");
        csrfField.type = "hidden";
        csrfField.name = "csrfmiddlewaretoken";
        csrfField.value = csrfToken;
        form.appendChild(csrfField);

        var nextUrl = button.getAttribute("data-next-url");
        if (nextUrl) {
            var nextField = document.createElement("input");
            nextField.type = "hidden";
            nextField.name = "next";
            nextField.value = nextUrl;
            form.appendChild(nextField);
        }

        document.body.appendChild(form);
        form.submit();
    }

    function attendanceStateMeta(state) {
        if (state === "present") {
            return { label: "Kelgan", short: "K", tone: "present" };
        }
        if (state === "absent") {
            return { label: "Kelmagan", short: "Y", tone: "absent" };
        }
        return { label: "Belgilanmagan yoki dars yo'q", short: "", tone: "neutral" };
    }

    document.addEventListener("click", function (event) {
        var quickDeleteButton = event.target.closest("[data-quick-delete-url]");
        if (!quickDeleteButton) {
            return;
        }

        event.preventDefault();
        submitQuickDelete(quickDeleteButton);
    });

    function nextAttendanceState(state) {
        if (state === "neutral") {
            return "present";
        }
        if (state === "present") {
            return "absent";
        }
        return "neutral";
    }

    function updateAttendanceCounters(cell, previousState, nextState) {
        var row = cell.closest("[data-attendance-row]");
        if (row) {
            var rowPresent = row.querySelector("[data-attendance-count='present']");
            var rowAbsent = row.querySelector("[data-attendance-count='absent']");

            if (rowPresent) {
                rowPresent.textContent = String(
                    Math.max(0, parseInt(rowPresent.textContent || "0", 10) +
                    (nextState === "present" ? 1 : 0) -
                    (previousState === "present" ? 1 : 0))
                );
            }

            if (rowAbsent) {
                rowAbsent.textContent = String(
                    Math.max(0, parseInt(rowAbsent.textContent || "0", 10) +
                    (nextState === "absent" ? 1 : 0) -
                    (previousState === "absent" ? 1 : 0))
                );
            }
        }

        var summaryPresent = document.querySelector("[data-attendance-summary='present']");
        var summaryAbsent = document.querySelector("[data-attendance-summary='absent']");

        if (summaryPresent) {
            summaryPresent.textContent = String(
                Math.max(0, parseInt(summaryPresent.textContent || "0", 10) +
                (nextState === "present" ? 1 : 0) -
                (previousState === "present" ? 1 : 0))
            );
        }

        if (summaryAbsent) {
            summaryAbsent.textContent = String(
                Math.max(0, parseInt(summaryAbsent.textContent || "0", 10) +
                (nextState === "absent" ? 1 : 0) -
                (previousState === "absent" ? 1 : 0))
            );
        }
    }

    function paintAttendanceCell(cell, state) {
        var meta = attendanceStateMeta(state);
        cell.dataset.state = state;
        cell.classList.remove("attendance-cell--present", "attendance-cell--absent", "attendance-cell--neutral");
        cell.classList.add("attendance-cell--" + meta.tone);
        cell.textContent = meta.short;
        cell.title = meta.label;
        cell.setAttribute("aria-label", meta.label);
    }

    Array.prototype.slice.call(document.querySelectorAll("[data-attendance-cell]")).forEach(function (cell) {
        paintAttendanceCell(cell, cell.dataset.state || "neutral");

        cell.addEventListener("click", function () {
            if (cell.classList.contains("is-saving")) {
                return;
            }

            var previousState = cell.dataset.state || "neutral";
            var nextState = nextAttendanceState(previousState);

            cell.classList.add("is-saving");

            window.fetch(cell.dataset.updateUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken"),
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: JSON.stringify({
                    group_id: cell.dataset.groupId,
                    student_id: cell.dataset.studentId,
                    date: cell.dataset.date,
                    state: nextState
                })
            })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("Attendance update failed");
                    }
                    return response.json();
                })
                .then(function (payload) {
                    paintAttendanceCell(cell, payload.state || nextState);
                    updateAttendanceCounters(cell, previousState, payload.state || nextState);
                })
                .catch(function () {
                    window.alert("Davomatni saqlashda xatolik yuz berdi.");
                })
                .finally(function () {
                    cell.classList.remove("is-saving");
                });
        });
    });
})();
