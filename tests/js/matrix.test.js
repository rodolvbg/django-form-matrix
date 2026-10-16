import { beforeAll, beforeEach, describe, expect, it } from "vitest";

const MATRIX = `
	<details class="form-matrix-section">
		<summary><span data-form-matrix-count>0/5</span></summary>
		<table>
			<thead><tr>
				<th><input type="checkbox" data-form-matrix-toggle="section" id="section"></th>
				<th><input type="checkbox" data-form-matrix-toggle="column" data-column="add" id="col-add"></th>
				<th><input type="checkbox" data-form-matrix-toggle="column" data-column="view" id="col-view"></th>
				<th><input type="checkbox" data-form-matrix-toggle="column" data-column="delete" id="col-delete"></th>
				<th><input type="checkbox" data-form-matrix-toggle="column" data-column="others" id="col-others"></th>
			</tr></thead>
			<tbody>
				<tr>
					<th><input type="checkbox" data-form-matrix-toggle="row" id="row-invoice"></th>
					<td data-column="add"><input type="checkbox" name="p" value="1"></td>
					<td data-column="view"><input type="checkbox" name="p" value="2" checked></td>
					<td data-column="delete"><span>—</span></td>
					<td data-column="others"><input type="checkbox" name="p" value="3"></td>
				</tr>
				<tr>
					<th><input type="checkbox" data-form-matrix-toggle="row" id="row-series"></th>
					<td data-column="add"><input type="checkbox" name="p" value="4"></td>
					<td data-column="view"><input type="checkbox" name="p" value="5"></td>
					<td data-column="delete"><span>—</span></td>
					<td data-column="others"></td>
				</tr>
			</tbody>
		</table>
	</details>`;

beforeAll(async () => {
	document.body.innerHTML = MATRIX;
	await import(
		"../../src/django_form_matrix/static/django_form_matrix/js/matrix.js"
	);
});

const $ = (selector) => document.querySelector(selector);
const checked = () =>
	[...document.querySelectorAll("input[name=p]:checked")].map((i) => i.value);

function toggle(selector) {
	const input = $(selector);
	input.checked = !input.checked;
	input.dispatchEvent(new Event("change", { bubbles: true }));
}

describe("initial state", () => {
	it("shows partial rows, columns and the count", () => {
		expect($("#row-invoice").indeterminate).toBe(true);
		expect($("#col-view").indeterminate).toBe(true);
		expect($("#section").indeterminate).toBe(true);
		expect($("#col-delete").disabled).toBe(true);
		expect($("[data-form-matrix-count]").textContent).toBe("1/5");
	});
});

describe("shortcuts", () => {
	beforeEach(() => {
		document.body.innerHTML = MATRIX;
		document.dispatchEvent(new Event("DOMContentLoaded"));
	});

	it("a row checks every checkbox of the row", () => {
		toggle("#row-invoice");
		expect(checked()).toEqual(["1", "2", "3"]);
		expect($("#row-invoice").checked).toBe(true);
		expect($("[data-form-matrix-count]").textContent).toBe("3/5");
		toggle("#row-invoice");
		expect(checked()).toEqual([]);
	});

	it("a column checks that column in every row", () => {
		toggle("#col-add");
		expect(checked()).toEqual(["1", "2", "4"]);
		expect($("#col-add").checked).toBe(true);
	});

	it("any column key works, not only the ones of permissions", () => {
		toggle("#col-others");
		expect(checked()).toEqual(["2", "3"]);
		expect($("#col-others").checked).toBe(true);
	});

	it("the section checks everything", () => {
		toggle("#section");
		expect(checked()).toEqual(["1", "2", "3", "4", "5"]);
		expect($("#row-series").checked).toBe(true);
		expect($("#section").indeterminate).toBe(false);
	});

	it("single checkboxes update the shortcuts", () => {
		toggle("input[value='4']");
		toggle("input[value='5']");
		expect($("#row-series").checked).toBe(true);
		expect($("[data-form-matrix-count]").textContent).toBe("3/5");
	});

	it("ignores changes outside the matrix", () => {
		document.body.insertAdjacentHTML(
			"beforeend",
			'<input type="checkbox" id="x">',
		);
		toggle("#x");
		expect(checked()).toEqual(["2"]);
	});

	it("works in a section without count", () => {
		$("[data-form-matrix-count]").remove();
		toggle("#row-series");
		expect(checked()).toEqual(["2", "4", "5"]);
	});
});
