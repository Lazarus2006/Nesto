const NestoMap = (() => {
    "use strict";

    const WORLD_VIEW = [20, 0];
    const WORLD_ZOOM = 2;
    const DEFAULT_MAX_ZOOM = 18;
    const MIN_BOUNDS_SPAN = 0.06;
    const BOUNDS_PADDING = 0.5;
    const LIBRARY_ERROR = "The map library could not load. Check your internet connection and try again.";

    const city = {
        name: "",
        center: null,
        zoom: null,
        bounds: null,
        minZoom: null,
        maxZoom: null
    };

    let derivedBounds;
    let cityRevision = 0;

    const views = {
        category: {
            elementId: "category-map",
            statusId: "category-map-status",
            map: null,
            markers: null,
            pending: null,
            observer: null,
            generation: 0
        },

        entity: {
            elementId: "entity-map",
            statusId: "entity-map-status",
            map: null,
            marker: null,
            pending: null,
            observer: null,
            generation: 0
        }
    };

    let defaultCityCenter = null;
    let defaultCityZoom = null;

    function validCoordinates(latitude, longitude) {
        if (
            latitude === "" ||
            longitude === "" ||
            latitude == null ||
            longitude == null
        ) {
            return false;
        }

        const lat = Number(latitude);
        const lng = Number(longitude);

        return Number.isFinite(lat) &&
            Number.isFinite(lng) &&
            lat >= -90 &&
            lat <= 90 &&
            lng >= -180 &&
            lng <= 180;
    }

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[character]);
    }

    function setStatus(id, message) {
        const element = document.getElementById(id);

        if (element) {
            element.textContent = message;
        }
    }

    function isVisible(element) {
        return Boolean(
            element &&
            element.offsetWidth > 0 &&
            element.offsetHeight > 0
        );
    }

    function prefersReducedMotion() {
        return Boolean(
            window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches
        );
    }

    function numericOption(value) {
        if (
            value === null ||
            value === undefined ||
            value === "" ||
            !Number.isFinite(Number(value))
        ) {
            return null;
        }

        return Number(value);
    }

    function validBounds(bounds) {
        if (!Array.isArray(bounds) || bounds.length !== 2) {
            return false;
        }

        const [[south, west], [north, east]] = bounds;

        return validCoordinates(south, west) &&
            validCoordinates(north, east) &&
            Number(south) < Number(north) &&
            Number(west) < Number(east);
    }

    function setCity(options) {
        const settings = options || {};

        city.name = settings.name || "";

        city.center =
            Array.isArray(settings.center) &&
            settings.center.length === 2 &&
            validCoordinates(settings.center[0], settings.center[1])
                ? [Number(settings.center[0]), Number(settings.center[1])]
                : null;

        city.zoom = numericOption(settings.zoom);
        city.bounds = validBounds(settings.bounds) ? settings.bounds : null;
        city.minZoom = numericOption(settings.minZoom);
        city.maxZoom = numericOption(settings.maxZoom);

        if (
            city.minZoom !== null &&
            city.maxZoom !== null &&
            city.minZoom > city.maxZoom
        ) {
            city.minZoom = city.maxZoom;
        }

        derivedBounds = undefined;
        cityRevision++;

        Object.values(views).forEach(view => {
            view.generation++;

            if (!view.map || !isVisible(view.map.getContainer())) {
                return;
            }

            view.map.invalidateSize({ animate: false });
            applyCityLimits(view.map);
            resetView(view.map);
        });
    }

    function ensureMinimumSpan(bounds) {
        let southWest = bounds.getSouthWest();
        let northEast = bounds.getNorthEast();

        const latitudeGap =
            MIN_BOUNDS_SPAN - (northEast.lat - southWest.lat);

        if (latitudeGap > 0) {
            southWest = L.latLng(
                southWest.lat - latitudeGap / 2,
                southWest.lng
            );

            northEast = L.latLng(
                northEast.lat + latitudeGap / 2,
                northEast.lng
            );
        }

        const longitudeGap =
            MIN_BOUNDS_SPAN - (northEast.lng - southWest.lng);

        if (longitudeGap > 0) {
            southWest = L.latLng(
                southWest.lat,
                southWest.lng - longitudeGap / 2
            );

            northEast = L.latLng(
                northEast.lat,
                northEast.lng + longitudeGap / 2
            );
        }

        return L.latLngBounds(southWest, northEast);
    }

    function deriveBoundsFromListings() {
        const points = [];

        document.querySelectorAll("#entity-list .entity-card").forEach(card => {
            const latitude = card.dataset.entityLatitude;
            const longitude = card.dataset.entityLongitude;

            if (validCoordinates(latitude, longitude)) {
                points.push([Number(latitude), Number(longitude)]);
            }
        });

        return points.length
            ? ensureMinimumSpan(L.latLngBounds(points))
            : null;
    }

    function cityBounds() {
        if (city.bounds) {
            const bounds = L.latLngBounds(city.bounds);

            if (bounds.isValid()) {
                return bounds;
            }
        }

        if (derivedBounds === undefined) {
            derivedBounds = deriveBoundsFromListings();
        }

        return derivedBounds;
    }

    function applyCityLimits(map) {
        const bounds = cityBounds();
        const maxZoom = city.maxZoom !== null ? city.maxZoom : DEFAULT_MAX_ZOOM;
        map.setMaxZoom(maxZoom);
        
        if (!bounds) {
            map.setMaxBounds(null);
            const safeMinZoom = city.center ? 10 : 4;
            map.setMinZoom(city.minZoom !== null ? Math.min(city.minZoom, maxZoom) : safeMinZoom);
            return;
        }

        const allowedBounds = bounds.pad(BOUNDS_PADDING);
        map.setMaxBounds(allowedBounds);
        const fitZoom = map.getBoundsZoom(allowedBounds);
        const requestedMinZoom = city.minZoom !== null ? city.minZoom : fitZoom;
        map.setMinZoom(Math.min(Math.max(requestedMinZoom, fitZoom), maxZoom));
    }

    function resetView(map) {
        const bounds = cityBounds();

        if (bounds) {
            map.fitBounds(bounds, { padding: [24, 24], maxZoom: 15, animate: false });
        } else {
            if (city.center) {
                map.setView(city.center, city.zoom !== null ? city.zoom : 12, { animate: false });
            } else {
                map.setView([20.5937, 78.9629], 5, { animate: false }); // Fallback to country view
            }
        }
    }

    function createMap(element) {
        const map = L.map(element, {
            maxBoundsViscosity: 0.85
        }).setView(WORLD_VIEW, WORLD_ZOOM);

        const mapboxToken = window.MAPBOX_TOKEN || "";
        const tileLayer = mapboxToken
            ? L.tileLayer(`https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`, {
                tileSize: 512,
                zoomOffset: -1,
                maxZoom: 20,
                attribution: '&copy; <a href="https://www.mapbox.com/about/maps/">Mapbox</a> &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            })
            : L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            });
        tileLayer.addTo(map);
        return map;
    }

    function watchVisibility(view, element) {
        if (typeof ResizeObserver === "undefined") {
            return;
        }

        let lastWidth = 0;
        let lastHeight = 0;

        view.observer = new ResizeObserver((entries) => {
            if (!isVisible(element) || !view.map) {
                return;
            }

            const entry = entries[0];
            const newWidth = entry.contentRect.width;
            const newHeight = entry.contentRect.height;
            
            if (Math.abs(newWidth - lastWidth) < 5 && Math.abs(newHeight - lastHeight) < 5) {
                return;
            }

            lastWidth = newWidth;
            lastHeight = newHeight;

            view.map.invalidateSize({ animate: false });

            const job = view.pending;

            if (job) {
                view.pending = null;
                job();
            }
        });
        view.observer.observe(element);
    }

    function initMap(kind) {
        const view = views[kind || "category"];

        if (!view) {
            return null;
        }

        if (view.map) {
            return view.map;
        }

        if (typeof L === "undefined") {
            setStatus(view.statusId, LIBRARY_ERROR);
            return null;
        }

        const element = document.getElementById(view.elementId);

        if (!element) {
            return null;
        }

        view.map = createMap(element);

        if (view === views.category) {
            view.markers = L.featureGroup().addTo(view.map);
        }

        watchVisibility(view, element);

        return view.map;
    }

    function runWhenVisible(view, job) {
        const element = document.getElementById(view.elementId);
        if (!element || !view.map) return;
        const generation = view.generation;
        const run = () => {
            if (generation !== view.generation || !view.map || !isVisible(element)) return;
            view.map.invalidateSize({ animate: false });
            job();
        };

        requestAnimationFrame(() => {
            if (isVisible(element)) {
                view.pending = null;
                run();
            } else if (view.observer) {
                view.pending = run;
            } else {
                view.pending = null;
                requestAnimationFrame(run);
            }
        });
    }

    function renderCategory(categoryId) {
        const view = views.category;
        const map = view.map;

        applyCityLimits(map);
        view.markers.clearLayers();

        const points = [];

        document.querySelectorAll("#entity-list .entity-card").forEach(card => {
            if (card.dataset.categoryId !== categoryId) return;

            const latitude = card.dataset.entityLatitude;
            const longitude = card.dataset.entityLongitude;

            if (!validCoordinates(latitude, longitude)) return;

            const point = [Number(latitude), Number(longitude)];

            L.marker(point)
                .bindPopup(`<strong>${escapeHtml(card.dataset.entityName || "Listing")}</strong>`)
                .on("click", () => {
                    if (typeof showEntityState === "function") showEntityState(card);
                })
                .addTo(view.markers);

            points.push(point);
        });

        if (points.length === 1) {
            map.setView(points[0], Math.min(15, map.getMaxZoom()), { animate: false });
        } else if (points.length > 1) {
            map.fitBounds(points, { padding: [24, 24], maxZoom: 15, animate: false });
        } else {
            resetView(map);
        }

        setTimeout(() => {
            defaultCityCenter = map.getCenter();
            defaultCityZoom = map.getZoom();
        }, 200);

        setStatus(
            view.statusId,
            points.length
                ? `${points.length} mapped ${points.length === 1 ? "listing" : "listings"} in this category.`
                : "No listings in this category have valid coordinates yet. Showing default city view."
        );
    }

    function showCategory(categoryId) {
        if (!initMap("category")) {
            return;
        }

        const id = String(categoryId);

        views.category.generation++;

        runWhenVisible(views.category, () => {
            renderCategory(id);
        });
    }

    function waitForMoveEnd(map, generation, callback) {
        let completed = false;
        let fallbackTimer;

        const finish = () => {
            if (completed) {
                return;
            }

            completed = true;
            clearTimeout(fallbackTimer);
            map.off("moveend", onMoveEnd);

            if (generation === views.entity.generation) {
                callback();
            }
        };

        const onMoveEnd = () => finish();

        map.once("moveend", onMoveEnd);

        fallbackTimer = setTimeout(finish, 1800);
    }

    function renderEntity(button, generation) {
        const view = views.entity;
        const map = view.map;

        if (views.category.map && !prefersReducedMotion()) {
            map.setView(views.category.map.getCenter(), views.category.map.getZoom(), { animate: false });
        }
        if (view.marker) {
            map.removeLayer(view.marker);
            view.marker = null;
        }

        const latitude = button.dataset.entityLatitude;
        const longitude = button.dataset.entityLongitude;
        const directionsLink = document.getElementById("directions-link");

        if (!validCoordinates(latitude, longitude)) {
            applyCityLimits(map);
            resetView(map);

            if (directionsLink) {
                directionsLink.href =
                    "https://www.google.com/maps/search/?api=1&query=" +
                    encodeURIComponent(
                        (button.dataset.entityLocation || "") +
                        (city.name ? ", " + city.name : "")
                    );

                directionsLink.classList.remove("hidden");
                directionsLink.classList.add("flex");
            }

            setStatus(
                view.statusId,
                button.dataset.entityLocation
                    ? "No coordinates are saved, so the map cannot show an exact pin. You can search this address in Google Maps."
                    : "No valid coordinates are saved for this listing."
            );

            return;
        }

        const point = [Number(latitude), Number(longitude)];

        const marker = L.marker(point)
            .bindPopup(
                `<strong>${escapeHtml(button.dataset.entityName || "Listing")}</strong>`
            );

        marker.addTo(map);
        view.marker = marker;

        if (directionsLink) {
            directionsLink.href =
                "https://www.google.com/maps/dir/?api=1&destination=" +
                encodeURIComponent(latitude + "," + longitude);

            directionsLink.classList.remove("hidden");
            directionsLink.classList.add("flex");
        }

        applyCityLimits(map);

        const targetZoom = Math.min(16, map.getMaxZoom());

        if (prefersReducedMotion()) {
            map.setView(point, targetZoom, { animate: false });
            marker.openPopup();
        } else {
            const currentCenter = map.getCenter();
            const currentZoom = map.getZoom();

            const samePosition =
                map.distance(currentCenter, L.latLng(point)) < 20 &&
                Math.abs(currentZoom - targetZoom) < 0.1;

            if (samePosition) {
                marker.openPopup();
            } else {
                map.flyTo(point, targetZoom, { duration: 1.1 });

                waitForMoveEnd(map, generation, () => {
                    if (view.marker === marker) {
                        marker.openPopup();
                    }
                });
            }
        }

        setStatus(view.statusId, "Showing the saved coordinates for this listing.");
    }

    function focusEntity(button) {
        if (!button || !initMap("entity")) {
            return;
        }

        const view = views.entity;

        view.generation++;

        const generation = view.generation;

        runWhenVisible(view, () => {
            if (generation !== view.generation) {
                return;
            }

            renderEntity(button, generation);
        });
    }

    function zoomOutToCity() {
        const activeMap = isVisible(document.getElementById(views.entity.elementId)) 
            ? views.entity.map 
            : views.category.map;

        if (activeMap && defaultCityCenter && defaultCityZoom) {
            activeMap.flyTo(defaultCityCenter, defaultCityZoom, {
                animate: true,
                duration: 1.2
            });
            activeMap.closePopup();
            setTimeout(() => {
                if (views.category.map) {
                    views.category.map.setView(defaultCityCenter, defaultCityZoom, { animate: false });
                }
            }, 1200);
        }
    }

    return {
        initMap,
        setCity,
        showCategory,
        focusEntity,
        zoomOutToCity
    };
})();
