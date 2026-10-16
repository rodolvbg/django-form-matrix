{
    // Shortcuts of the matrix (templates/django_form_matrix): the checkbox of a
    // row, a column or a whole section sets every checkbox it covers, and shows
    // whether they are all, some or none checked.
    const CELL = "input[type=checkbox][name]:not([disabled])";

    function covered(toggle) {
        const table = toggle.closest("table");
        switch (toggle.dataset.formMatrixToggle) {
            case "row":
                return toggle.closest("tr").querySelectorAll(CELL);
            case "column":
                return [...table.querySelectorAll("td[data-column]")]
                    .filter(
                        (cell) => cell.dataset.column === toggle.dataset.column,
                    )
                    .flatMap((cell) => [...cell.querySelectorAll(CELL)]);
            default:
                return table.querySelectorAll(CELL);
        }
    }

    function refresh(section) {
        for (const toggle of section.querySelectorAll(
            "[data-form-matrix-toggle]",
        )) {
            const inputs = [...covered(toggle)];
            const checked = inputs.filter((input) => input.checked).length;
            toggle.disabled = inputs.length === 0;
            toggle.checked = inputs.length > 0 && checked === inputs.length;
            toggle.indeterminate = checked > 0 && checked < inputs.length;
        }
        const count = section.querySelector("[data-form-matrix-count]");
        if (count) {
            const all = section.querySelectorAll("input[type=checkbox][name]");
            const checked = [...all].filter((input) => input.checked).length;
            count.textContent = `${checked}/${all.length}`;
        }
    }

    document.addEventListener("change", (event) => {
        const section = event.target.closest(".form-matrix-section");
        if (!section) {
            return;
        }
        if (event.target.dataset.formMatrixToggle) {
            for (const input of covered(event.target)) {
                input.checked = event.target.checked;
            }
        }
        refresh(section);
    });

    function init() {
        for (const section of document.querySelectorAll(
            ".form-matrix-section",
        )) {
            refresh(section);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
}
