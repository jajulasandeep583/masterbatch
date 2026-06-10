// Force desk sidebar links to navigate in the same tab.
// Some environments end up opening sidebar DocType links in a new browser tab
// (stale cached assets / stray target=_blank). This delegated handler runs after
// frappe's own router handler; if the click is still unhandled, it routes in-app.
$(document).on("click", ".body-sidebar a.item-anchor", function (e) {
	if (e.isDefaultPrevented()) return; // core router already handled it
	if (e.ctrlKey || e.metaKey || e.which === 2) return; // deliberate new-tab
	const href = this.getAttribute("href");
	if (!href || !href.startsWith("/")) return; // external URLs keep default behavior
	e.preventDefault();
	if (this.search) {
		frappe.route_options = {};
		for (const [key, value] of new URLSearchParams(this.search)) {
			frappe.route_options[key] = value;
		}
	}
	frappe.set_route(this.pathname);
});
