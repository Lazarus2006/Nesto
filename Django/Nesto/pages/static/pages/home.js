
const modal = document.getElementById("discovery-modal");
const categoryState = document.getElementById("category-state");
const entityState = document.getElementById("entity-state");
const modalTitle = document.getElementById("modal-title");
const modalSubtitle = document.getElementById("modal-subtitle");
const modalEyebrow = document.getElementById("modal-eyebrow");
const modalBack = document.getElementById("modal-back");
const entityCount = document.getElementById("entity-count");
const noEntities = document.getElementById("no-entities");

let activeCategoryId = null;
let lastFocusedElement = null;

NestoMap.setCity({ name: cityName });

function switchView(view) {
    const explore = view === "explore";
    const explorePanel = document.getElementById("explore-view");
    const communityPanel = document.getElementById("community-view");
    const exploreTab = document.getElementById("explore-tab");
    const communityTab = document.getElementById("community-tab");

    explorePanel.hidden = !explore;
    communityPanel.hidden = explore;

    exploreTab.setAttribute("aria-selected", String(explore));
    communityTab.setAttribute("aria-selected", String(!explore));

    document.getElementById("page-heading").textContent =
        explore ? "Find your place." : "Your community";

    document.getElementById("page-subheading").textContent =
        explore
            ? `Discover places, everyday services, and local knowledge in ${cityName}.`
            : "Local questions, experiences, and recommendations.";
}

function openCategory(categoryId) {
    const categoryButton = document.querySelector(
        `.category-card[data-category-id="${categoryId}"]`
    );

    if (!categoryButton) return;

    lastFocusedElement = document.activeElement;
    activeCategoryId = String(categoryId);

    modalTitle.textContent = categoryButton.dataset.categoryName;
    modalSubtitle.textContent = "Discover places and services in " + cityName;
    modalEyebrow.textContent = "CITY GUIDE";

    showCategoryState();

    let count = 0;
    document.querySelectorAll("#entity-list .entity-card").forEach(card => {
        const matches = card.dataset.categoryId === activeCategoryId;
        card.classList.toggle("hidden", !matches);
        if (matches) count++;
    });

    entityCount.textContent = `${count} ${count === 1 ? "place" : "places"}`;
    noEntities.classList.toggle("hidden", count > 0);

    modal.classList.remove("hidden");
    modal.classList.add("flex");
    document.body.classList.add("modal-open");

    try { NestoMap.showCategory(activeCategoryId); } catch (error) { console.error("Category map error:", error); }

    document.getElementById("modal-close").focus();
}

function showCategoryState() {
    categoryState.classList.remove("hidden");
    categoryState.classList.add("flex");
    entityState.classList.add("hidden");
    entityState.classList.remove("flex");
    modalBack.classList.add("hidden");

    if (activeCategoryId !== null) {
        const categoryButton = document.querySelector(
            `.category-card[data-category-id="${activeCategoryId}"]`
        );

        if (categoryButton) {
            modalTitle.textContent = categoryButton.dataset.categoryName;
        }
    }

    modalEyebrow.textContent = "CITY GUIDE";
    modalSubtitle.textContent = "Discover places and services in " + cityName;
}

function showEntityState(button) {
    const name = button.dataset.entityName || "Untitled listing";
    const location = button.dataset.entityLocation || "";
    const price = button.dataset.entityPrice || "";
    const image = button.dataset.entityImage || "";

    const fullEntityLink = document.getElementById("full-entity-link");
    fullEntityLink.href = button.dataset.entityUrl || "#";

    categoryState.classList.add("hidden");
    categoryState.classList.remove("flex");
    entityState.classList.remove("hidden");
    entityState.classList.add("flex");
    modalBack.classList.remove("hidden");

    modalEyebrow.textContent = "PLACE DETAILS";
    modalTitle.textContent = name;
    modalSubtitle.textContent = location || "Location not provided";

    document.getElementById("detail-name").textContent = name;

    const priceElement = document.getElementById("detail-price");
    priceElement.textContent = price;
    priceElement.classList.toggle("hidden", !price);

    const locationWrap = document.getElementById("detail-location-wrap");
    document.getElementById("detail-location").textContent = location;
    locationWrap.classList.toggle("hidden", !location);

    const directionsLink = document.getElementById("directions-link");

    if (location) {
        directionsLink.href =
            "https://www.google.com/maps/search/?api=1&query=" +
            encodeURIComponent(location + ", " + cityName);
        directionsLink.classList.remove("hidden");
        directionsLink.classList.add("flex");
    } else {
        directionsLink.classList.add("hidden");
        directionsLink.classList.remove("flex");
        directionsLink.removeAttribute("href");
    }

    const imageWrap = document.getElementById("detail-image-wrap");
    const imageElement = document.getElementById("detail-image");

    if (image) {
        imageElement.src = image;
        imageElement.alt = name;
        imageWrap.classList.remove("hidden");
    } else {
        imageElement.removeAttribute("src");
        imageElement.alt = "";
        imageWrap.classList.add("hidden");
    }

    const attributesContainer = document.getElementById("detail-attributes");
    const noAttributes = document.getElementById("detail-no-attributes");
    attributesContainer.replaceChildren();

    let attributes = {};
    try {
        attributes = JSON.parse(button.dataset.entityAttributes || "{}");
    } catch (error) {
        attributes = {};
    }

    let attributeCount = 0;

    if (attributes && typeof attributes === "object" && !Array.isArray(attributes)) {
        Object.entries(attributes).forEach(([key, value]) => {
            if (value === null || value === undefined || String(value).trim() === "") return;

            const row = document.createElement("div");
            row.className = "rounded-xl border border-slate-200 bg-white p-3";

            const label = document.createElement("p");
            label.className = "text-[10px] font-extrabold uppercase tracking-wider text-slate-500";
            label.textContent = key;

            const content = document.createElement("p");
            content.className = "mt-1 break-words text-sm leading-6 text-slate-700";
            content.textContent = String(value);

            row.append(label, content);
            attributesContainer.appendChild(row);
            attributeCount++;
        });
    }

    noAttributes.classList.toggle("hidden", attributeCount > 0);

    try { NestoMap.focusEntity(button); } catch (error) { console.error("Entity map error:", error); }
}

function closeModal() {
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    document.body.classList.remove("modal-open");

    activeCategoryId = null;

    if (lastFocusedElement && typeof lastFocusedElement.focus === "function") {
        lastFocusedElement.focus();
    }
}

document.getElementById("modal-close").addEventListener("click", closeModal);

modal.addEventListener("click", event => {
    if (event.target === modal) closeModal();
});

document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !modal.classList.contains("hidden")) {
        closeModal();
    }
});

function handleBackClick() {
    try {
        NestoMap.zoomOutToCity();
    } catch (error) {
        console.error("Map zoom out error:", error);
    }
    setTimeout(() => {
        showCategoryState();
    }, 1200); 
}